import os
import argparse

from dotenv import load_dotenv
from notion_client import Client

load_dotenv('../.env')

from src.daily_service.consts import DEFAULT_REFRESH_WINDOW_MONTHS
from src.daily_service.service import pick_and_send


NOTION_TOKEN = os.environ['NOTION_TOKEN']
NOTION_DB_ID = os.environ['NOTION_DB_ID']
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']


def main(refresh_window_months: int) -> None:
    notion_client = Client(auth=NOTION_TOKEN)
    pick_and_send(notion_client=notion_client, notion_db_id=NOTION_DB_ID,
                  bot_token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID,
                  refresh_window_months=refresh_window_months)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh_window_months", default=DEFAULT_REFRESH_WINDOW_MONTHS, type=int)
    args = parser.parse_args()

    main(args.refresh_window_months)
