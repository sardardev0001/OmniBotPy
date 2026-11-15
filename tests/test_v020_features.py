import asyncio
import json
import pytest
import httpx
from omnibotpy import Bot, Platform, InlineButton, InlineKeyboard, ReplyKeyboard, MemoryStorage
from omnibotpy.adapters import TelegramAdapter, BaleAdapter, SoroushAdapter
from omnibotpy.errors import APIError, TransportError
from omnibotpy.transport import HTTPTransport


def mk(update_id=1, text='/start', chat=123, user=456):
    return {'update_id': update_id, 'message': {'message_id': 7, 'chat': {'id': chat, 'type': 'private'},
            'from': {'id': user, 'first_name': 'A'}, 'text': text}}


def response(request):
    if request.url.path.endswith('getUpdates'):
        return httpx.Response(200, json={'ok': True, 'result': []})
    return httpx.Response(200, json={'ok': True, 'result': {'message_id': 4}})


@pytest.mark.asyncio
async def test_fsm_handler_lifecycle():
    storage = MemoryStorage()
    client = httpx.AsyncClient(transport=httpx.MockTransport(response))
    bot = Bot(Platform.TELEGRAM, 'secret:123', client=client, storage=storage)
    @bot.command('start')
    async def start(ctx):
        await ctx.set_state('form:name')
        await ctx.update_data(greeting='سلام')
    await bot.dispatch_raw(mk())
    record = await storage.get('telegram:123:456')
    assert record.state == 'form:name'
    assert record.data == {'greeting': 'سلام'}
    record.data['greeting'] = 'changed'
    assert (await storage.get('telegram:123:456')).data['greeting'] == 'سلام'
    await storage.clear('telegram:123:456')
    assert (await storage.get('telegram:123:456')).state is None
    await client.aclose()


@pytest.mark.asyncio
async def test_multipart_upload(tmp_path):
    seen = {}
    def handler(request):
        seen['body'] = request.content
        seen['ctype'] = request.headers['content-type']
        return httpx.Response(200, json={'ok': True, 'result': {'message_id': 99}})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = TelegramAdapter('secret', client=client)
    f = tmp_path / 'demo.txt'
    f.write_text('سلام', encoding='utf-8')
    result = await adapter.send_document_file(123, f, caption='caption')
    assert result['message_id'] == 99
    assert b'demo.txt' in seen['body']
    assert 'multipart/form-data' in seen['ctype']
    assert 'سلام'.encode() in seen['body']
    await client.aclose()


@pytest.mark.asyncio
async def test_keyboard_serialization_and_validation():
    button = InlineButton('OK', callback_data='ok')
    assert InlineKeyboard([[button]]).to_dict() == {'inline_keyboard': [[{'text': 'OK', 'callback_data': 'ok'}]]}
    assert ReplyKeyboard([['One']]).to_dict()['keyboard'][0][0]['text'] == 'One'
    with pytest.raises(ValueError):
        InlineButton('X')
    with pytest.raises(ValueError):
        InlineButton('X', callback_data='x', url='https://example.org')
    with pytest.raises(ValueError):
        InlineButton('X', callback_data='😂'*17)


@pytest.mark.asyncio
async def test_keyboard_sent_as_json():
    seen = {}
    def handler(request):
        seen.update(json.loads(request.content))
        return httpx.Response(200, json={'ok': True, 'result': True})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = BaleAdapter('secret', client=client)
    await adapter.send_message(1, 'Hi', reply_markup=InlineKeyboard([[InlineButton('ok', callback_data='go')]]))
    assert seen['reply_markup']['inline_keyboard'][0][0]['callback_data'] == 'go'
    await client.aclose()


@pytest.mark.asyncio
async def test_native_convenience_method():
    seen = []
    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, json={'ok': True, 'result': True})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = TelegramAdapter('secret', client=client)
    await adapter.delete_message(chat_id=1, message_id=2)
    assert seen[0].endswith('/deleteMessage')
    assert 'editMessageText' in adapter.available_methods()
    assert 'inquireTransaction' in BaleAdapter('secret', client=client).available_methods()
    assert not SoroushAdapter('secret', client=client).available_methods()
    await client.aclose()


@pytest.mark.asyncio
async def test_on_error_handler_receives_error():
    client = httpx.AsyncClient(transport=httpx.MockTransport(response))
    bot = Bot('telegram', 'secret', client=client)
    errors = []
    @bot.command('start')
    async def bad(ctx):
        raise RuntimeError('broken')
    @bot.on_error
    async def error_handler(ctx, exc):
        errors.append(str(exc))
    assert await bot.dispatch_raw(mk())
    assert errors == ['broken']
    await client.aclose()


@pytest.mark.asyncio
async def test_transport_redacts_token_in_api_description():
    token = 'never-leak-me'
    def handler(request):
        return httpx.Response(400, json={'ok': False, 'error_code': 400, 'description': f'Error: {token}'})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = TelegramAdapter(token, client=client)
    with pytest.raises(APIError) as exc:
        await adapter.get_me()
    assert token not in str(exc.value)
    await client.aclose()


@pytest.mark.asyncio
async def test_send_does_not_retry_but_read_does():
    calls = []
    def handler(request):
        calls.append(request.url.path)
        if len(calls) == 1:
            raise httpx.ConnectError('connection')
        return httpx.Response(200, json={'ok': True, 'result': []})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = TelegramAdapter('token', client=client)
    assert await adapter.get_updates(timeout=0) == []
    assert len(calls) == 2
    await client.aclose()


@pytest.mark.asyncio
async def test_send_failure_not_retried():
    calls=[]
    def handler(request):
        calls.append(1)
        raise httpx.ConnectError('broken')
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = TelegramAdapter('token', client=client)
    with pytest.raises(TransportError):
        await adapter.send_message(1, 'test')
    assert len(calls) == 1
    await client.aclose()


@pytest.mark.asyncio
async def test_generated_catalog_shortcut():
    seen = []
    def handler(request):
        seen.append(request.url.path)
        return httpx.Response(200, json={'ok': True, 'result': []})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = TelegramAdapter('secret', client=client)
    await adapter.get_user_profile_photos(user_id=123)
    assert seen[-1].endswith('/getUserProfilePhotos')
    await client.aclose()
