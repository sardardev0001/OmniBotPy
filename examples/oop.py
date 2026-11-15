import os
from omnibotpy import Bot, Platform, CommandHandler, MessageHandler

class Start(CommandHandler):
    command = "start"
    async def handle(self, ctx):
        await ctx.reply("Hello from a class-based handler!")

class Echo(MessageHandler):
    async def handle(self, ctx):
        if ctx.text:
            await ctx.reply(ctx.text)

bot = Bot(Platform(os.environ.get("BOT_PLATFORM", "bale")), os.environ["BOT_TOKEN"])
bot.add_handler(Start())
bot.add_handler(Echo())

if __name__ == "__main__":
    bot.run()
