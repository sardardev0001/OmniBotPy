import httpx
import pytest
from omnibotpy import Bot, Platform, MultiBot
from omnibotpy.models import normalize_event

@pytest.mark.parametrize('platform,expected', [
    (Platform.TELEGRAM, 'api.telegram.org'),
    (Platform.BALE, 'tapi.bale.ai'),
    (Platform.SOROUSH, 'api.splus.ir'),
])
@pytest.mark.asyncio
async def test_three_platform_routing(platform, expected):
    requests = []
    def mock(request):
        requests.append(request)
        return httpx.Response(200, json={'ok':True,'result':{'message_id':42}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(mock)) as client:
        bot = Bot(platform, 'FAKE', client=client)
        assert await bot.adapter.send_message(11, 'Hi') == {'message_id': 42}
        assert requests[0].url.host == expected
        assert requests[0].url.path.endswith('/sendMessage')

@pytest.mark.asyncio
async def test_multibot_registration_order():
    app = MultiBot()
    fired = []
    @app.command('start')
    async def start(ctx):
        fired.append(ctx.platform)
    def mock(request):
        return httpx.Response(200, json={'ok':True,'result':True})
    async with httpx.AsyncClient(transport=httpx.MockTransport(mock)) as client:
        first = app.add_bot('telegram', 'FAKE', client=client)
        second = app.add_bot('bale', 'FAKE', client=client)
        update = {'update_id': 1, 'message': {'chat': {'id': 1}, 'text': '/start'}}
        assert await first.dispatch_raw(update)
        assert await second.dispatch_raw(update)
    assert fired == ['telegram','bale']
