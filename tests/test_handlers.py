import pytest
from omnibotpy import BotController, CommandHandler, MessageHandler, Support
from omnibotpy.models import normalize_event

SAMPLE = {'update_id': 9, 'message': {'message_id': 2, 'chat': {'id': 111, 'type': 'private'},
          'from': {'id': 22, 'first_name': 'Test'}, 'text': '/start hello'}}

@pytest.mark.asyncio
async def test_decorator(fake_bot):
    bot, requests = fake_bot
    @bot.command('start')
    async def start(ctx):
        assert ctx.args == 'hello'
        await ctx.reply('OK')
    @bot.message()
    async def fallback(ctx):
        raise AssertionError('fallback should not run')
    assert await bot.dispatch_raw(SAMPLE)
    assert len(requests) == 1
    assert requests[0].url.path.endswith('/sendMessage')

@pytest.mark.asyncio
async def test_oop(fake_bot):
    bot, requests = fake_bot
    class Start(CommandHandler):
        command = 'start'
        async def handle(self, ctx):
            await ctx.reply('from class')
    bot.add_handler(Start())
    await bot.dispatch_raw(SAMPLE)
    assert len(requests) == 1

@pytest.mark.asyncio
async def test_controller(fake_bot):
    bot, requests = fake_bot
    class Main(BotController):
        async def on_start(self, ctx):
            await ctx.reply('controller')
    bot.add_controller(Main())
    await bot.dispatch_raw(SAMPLE)
    assert len(requests) == 1

@pytest.mark.asyncio
async def test_middleware(fake_bot):
    bot, calls = fake_bot
    trace = []
    async def middleware(ctx, next_call):
        trace.append('before')
        await next_call()
        trace.append('after')
    bot.add_middleware(middleware)
    @bot.command('start')
    async def start(ctx):
        trace.append('handler')
    await bot.dispatch_raw(SAMPLE)
    assert trace == ['before', 'handler', 'after']

def test_normalization():
    ev = normalize_event(SAMPLE, 'bale')
    assert ev.platform == 'bale' and ev.command == 'start' and ev.args == 'hello'
    callback = normalize_event({'update_id':10,'callback_query':{'id':'c1','data':'buy:1',
        'from':{'id':22},'message':{'chat':{'id':111},'message_id':3}}}, 'telegram')
    assert callback.kind == 'callback' and callback.callback_data == 'buy:1'

def test_capabilities(fake_bot):
    bot, _ = fake_bot
    assert bot.supports('callback') is Support.SUPPORTED
    assert bot.supports('payments') is Support.UNKNOWN
