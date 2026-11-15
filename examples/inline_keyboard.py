"""Use the same keyboard objects on Telegram and Bale when supported."""
import os
from omnibotpy import Bot, InlineButton, InlineKeyboard

bot = Bot(os.getenv('BOT_PLATFORM', 'telegram'), os.environ['BOT_TOKEN'])

@bot.command('start')
async def start(ctx):
    keyboard = InlineKeyboard([[InlineButton('Choose', callback_data='choose:1')]])
    await ctx.reply('Welcome!', reply_markup=keyboard)

@bot.callback('choose:')
async def callback(ctx):
    await ctx.answer_callback('Selected')

if __name__ == '__main__':
    bot.run()
