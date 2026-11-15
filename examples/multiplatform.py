import os
from omnibotpy import MultiBot, Platform

app = MultiBot()
for platform, key in ((Platform.TELEGRAM, "TELEGRAM_TOKEN"), (Platform.BALE, "BALE_TOKEN"),
                      (Platform.SOROUSH, "SOROUSH_TOKEN")):
    if token := os.getenv(key):
        app.add_bot(platform, token)

@app.command("start")
async def start(ctx):
    await ctx.reply(f"Welcome from {ctx.platform}!")

if __name__ == "__main__":
    app.run()
