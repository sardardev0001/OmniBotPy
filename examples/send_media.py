"""Send a local document via multipart; requires the bot to be added to chat."""
import asyncio
import os
from omnibotpy.adapters import TelegramAdapter

async def main():
    async with TelegramAdapter(os.environ['BOT_TOKEN']) as bot:
        result = await bot.send_document_file(os.environ['CHAT_ID'], 'README.md',
                                              caption='Project README')
        print('Sent message ID:', result.get('message_id'))

if __name__ == '__main__':
    asyncio.run(main())
