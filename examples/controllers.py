import os
from omnibotpy import Bot, BotController, Platform

class MainController(BotController):
    async def on_start(self, ctx):
        await ctx.reply("Welcome")

    async def on_message(self, ctx):
        if ctx.text:
            await ctx.reply(f"Echo: {ctx.text}")

bot = Bot(Platform.TELEGRAM, os.environ["BOT_TOKEN"])
bot.add_controller(MainController())

if __name__ == "__main__":
    bot.run()
