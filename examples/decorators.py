"""Set BOT_TOKEN and BOT_PLATFORM environment variables before running."""
import os
from omnibotpy import Bot, Platform

bot = Bot(platform=Platform(os.environ.get("BOT_PLATFORM", "telegram")), token=os.environ["BOT_TOKEN"])

@bot.command("start")
async def start(ctx):
    await ctx.reply("سلام! Welcome to OmniBotPy")

@bot.command("help")
async def help_command(ctx):
    await ctx.reply("Send a message and I will echo it.")

@bot.message()
async def echo(ctx):
    if ctx.text:
        await ctx.reply(ctx.text)

if __name__ == "__main__":
    bot.run()
