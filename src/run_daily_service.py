import os
import argparse

from dotenv import load_dotenv
from notion_client import Client

load_dotenv('../.env')

from src.daily_service.utils import format_response
from src.daily_service.telegram import send_telegram
from src.daily_service.consts import DEFAULT_REFRESH_WINDOW_MONTHS
from src.daily_service.notion import get_next_quote, update_used_quotes


NOTION_TOKEN = os.environ['NOTION_TOKEN']
NOTION_DB_ID = os.environ['NOTION_DB_ID']
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']


def main(refresh_window_months: int) -> None:
    notion_client = Client(auth=NOTION_TOKEN)
    next_quote = get_next_quote(notion_client=notion_client, notion_db_id=NOTION_DB_ID,
                                refresh_window_months=refresh_window_months)
    if next_quote:
        message, media_url = format_response(next_quote)
        send_telegram(msg=message, media_url=media_url,
                      bot_token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID)
        update_used_quotes(notion_client, next_quote)
    else:
        send_telegram(msg="⚠️ No sentences found in Notion.", media_url=None,
                      bot_token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh_window_months", default=DEFAULT_REFRESH_WINDOW_MONTHS, type=int)
    args = parser.parse_args()

    main(args.refresh_window_months)
