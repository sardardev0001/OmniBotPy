"""Example two-step conversation with in-memory FSM (not durable)."""
import os
from omnibotpy import Bot

bot = Bot('telegram', os.environ['BOT_TOKEN'])

@bot.command('start')
async def start(ctx):
    await ctx.set_state('awaiting_name')
    await ctx.reply('What is your name?')

@bot.message()
async def conversation(ctx):
    record = await ctx.get_state()
    if record.state == 'awaiting_name' and ctx.text:
        await ctx.update_data(name=ctx.text)
        await ctx.clear_state()
        await ctx.reply(f'Nice to meet you, {ctx.text}!')

if __name__ == '__main__':
    bot.run()
