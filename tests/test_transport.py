import httpx
import pytest
from omnibotpy.adapters import TelegramAdapter, SoroushAdapter
from omnibotpy.errors import APIError, RateLimitError, UnsupportedCapability, TransportError
from omnibotpy.webhook import handle_webhook
from omnibotpy import Bot, Platform

@pytest.mark.asyncio
async def test_api_error():
    c = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={
        'ok': False, 'error_code': 400, 'description': 'Bad request'})))
    adapter = TelegramAdapter('test', client=c)
    with pytest.raises(APIError):
        await adapter.get_me()
    await c.aclose()

@pytest.mark.asyncio
async def test_rate_limit():
    c = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={
        'ok': False, 'error_code': 429, 'description': 'Too many', 'parameters': {'retry_after': 10}})))
    adapter = TelegramAdapter('test', client=c)
    with pytest.raises(RateLimitError) as info:
        await adapter.get_me()
    assert info.value.retry_after == 10
    await c.aclose()

@pytest.mark.asyncio
async def test_soroush_webhook_guard():
    adapter = SoroushAdapter('test')
    with pytest.raises(UnsupportedCapability):
        await adapter.set_webhook('https://example.com')
    await adapter.close()

@pytest.mark.asyncio
async def test_webhook_secret(fake_bot):
    bot, _ = fake_bot
    with pytest.raises(PermissionError):
        await handle_webhook(bot, {}, headers={}, secret_token='secret')
    assert not await handle_webhook(bot, {}, headers={'X-Telegram-Bot-Api-Secret-Token':'secret'}, secret_token='secret')

@pytest.mark.asyncio
async def test_no_token_exposure():
    c = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(503)))
    adapter = TelegramAdapter('SECRET123', client=c)
    with pytest.raises(TransportError) as info:
        await adapter.get_me()
    assert 'SECRET123' not in str(info.value)
    await c.aclose()

@pytest.mark.parametrize('method', ['../getMe', 'foo/bar', 'getMe?token=x'])
@pytest.mark.asyncio
async def test_method_injection(method):
    adapter = TelegramAdapter('secret')
    with pytest.raises(ValueError):
        await adapter.call_method(method)
    await adapter.close()
