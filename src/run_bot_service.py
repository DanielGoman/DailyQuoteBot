import os
import uvicorn
import asyncio

from dotenv import load_dotenv

from src.bot_service.new_message_api import app
from src.bot_service.notion_bot import TelegramBot

load_dotenv()

# Environment variables
API_PORT = int(os.environ['API_PORT'])
NOTION_TOKEN = os.environ['NOTION_TOKEN']
NOTION_DB_ID = os.environ['NOTION_DB_ID']
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']


async def main():
    # Start FastAPI server
    server = uvicorn.Server(config=uvicorn.Config(app, host="0.0.0.0", port=API_PORT))

    # Create the bot app
    # TODO: add updating button for "make favorite" and "make not favorite"
    bot_app = TelegramBot.get_instance(TELEGRAM_BOT_TOKEN)
    await bot_app.updater.initialize(),  # prepares the bot

    # Run both FastAPI and Telegram polling concurrently
    await asyncio.gather(
        server.serve(),
        bot_app.updater.start_polling()  # starts polling loop
    )


if __name__ == "__main__":
    asyncio.run(main())