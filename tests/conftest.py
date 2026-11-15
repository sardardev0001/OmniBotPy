import pytest
import httpx
from omnibotpy import Bot, Platform

@pytest.fixture
def fake_bot():
    calls = []
    def handler(request):
        calls.append(request)
        import json
        data = json.loads(request.content) if request.content else {}
        method = request.url.path.rsplit('/', 1)[-1]
        if method == 'getUpdates':
            return httpx.Response(200, json={'ok': True, 'result': []})
        return httpx.Response(200, json={'ok': True, 'result': {'chat': {'id': data.get('chat_id')}, 'text': data.get('text')}})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    bot = Bot(Platform.TELEGRAM, 'TEST_TOKEN', client=client)
    yield bot, calls
