import os
import asyncio
import argparse

from notion_client import Client

from src.utils import format_response
from src.telegram import send_telegram
from src.consts import DEFAULT_REFRESH_WINDOW_MONTHS
from src.notion import get_next_quote, update_used_quotes


# Environment variables
NOTION_TOKEN = os.environ['NOTION_TOKEN']
NOTION_DB_ID = os.environ['NOTION_DB_ID']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']


async def main(refresh_window_months: int) -> None:
    notion_client = Client(auth=NOTION_TOKEN)
    next_quote = get_next_quote(notion_client=notion_client, notion_db_id=NOTION_DB_ID,
                                refresh_window_months=refresh_window_months)
    if next_quote:
        message, media_url = format_response(next_quote)
        await send_telegram(msg=message, media_url=media_url,
                            telegram_bot_token=TELEGRAM_BOT_TOKEN, telegram_chat_id=TELEGRAM_CHAT_ID)
        update_used_quotes(notion_client, next_quote)
    else:
        await send_telegram("⚠️ No sentences found in Notion.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh_window_months", default=DEFAULT_REFRESH_WINDOW_MONTHS, type=int)
    args = parser.parse_args()

    asyncio.run(main(args.refresh_window_months))
