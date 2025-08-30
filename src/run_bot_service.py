import os


from src.bot_service.telegram_bot import get_telegram_bot


# Environment variables
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']


def main():
    # Create the bot app
    bot_app = get_telegram_bot(TELEGRAM_BOT_TOKEN)

    print("Starting Telegram Bot")
    # Run the bot (blocking)
    bot_app.run_polling()


# ---------------- Run ----------------
if __name__ == "__main__":
    main()