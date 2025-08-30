import os
import asyncio


from src.bot_service.telegram_bot import get_telegram_bot


# Environment variables
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']


async def main():
    # Create the bot app
    bot_app = get_telegram_bot(TELEGRAM_BOT_TOKEN)

    # Run the bot (blocking)
    await bot_app.run_polling()


# ---------------- Run ----------------
if __name__ == "__main__":
    asyncio.run(main())