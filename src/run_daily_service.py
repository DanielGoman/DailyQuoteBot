import os
import argparse

from dotenv import load_dotenv
from notion_client import Client

load_dotenv('../.env')

from src.daily_service.utils import format_response
from src.daily_service.whatsapp import send_whatsapp, get_hours_since_last_inbound
from src.daily_service.consts import (DEFAULT_REFRESH_WINDOW_MONTHS,
                                      INBOUND_REMINDER_THRESHOLD_HOURS, REMINDER_MESSAGE)
from src.daily_service.notion import get_next_quote, update_used_quotes


NOTION_TOKEN = os.environ['NOTION_TOKEN']
NOTION_DB_ID = os.environ['NOTION_DB_ID']
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_WHATSAPP_FROM = os.environ['TWILIO_WHATSAPP_FROM']
WHATSAPP_TO_NUMBER = os.environ['WHATSAPP_TO_NUMBER']
TINYURL_API_TOKEN = os.environ.get('TINYURL_API_TOKEN')  # optional; falls back to full URL


def main(refresh_window_months: int) -> None:
    notion_client = Client(auth=NOTION_TOKEN)
    next_quote = get_next_quote(notion_client=notion_client, notion_db_id=NOTION_DB_ID,
                                refresh_window_months=refresh_window_months)
    if next_quote:
        message, media_url = format_response(next_quote, TINYURL_API_TOKEN)
        send_whatsapp(msg=message, media_url=media_url,
                      account_sid=TWILIO_ACCOUNT_SID, auth_token=TWILIO_AUTH_TOKEN,
                      from_number=TWILIO_WHATSAPP_FROM, to_number=WHATSAPP_TO_NUMBER)
        update_used_quotes(notion_client, next_quote)
    else:
        send_whatsapp(msg="⚠️ No sentences found in Notion.", media_url=None,
                      account_sid=TWILIO_ACCOUNT_SID, auth_token=TWILIO_AUTH_TOKEN,
                      from_number=TWILIO_WHATSAPP_FROM, to_number=WHATSAPP_TO_NUMBER)

    maybe_remind_to_reply()


def maybe_remind_to_reply() -> None:
    """Send a short, separate reminder if the recipient hasn't replied within the
    threshold, so the Twilio sandbox opt-in doesn't lapse."""
    try:
        hours = get_hours_since_last_inbound(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
                                             TWILIO_WHATSAPP_FROM, WHATSAPP_TO_NUMBER)
    except Exception as e:
        print(f"Could not check time since last inbound message: {e}")
        return

    if hours is None or hours >= INBOUND_REMINDER_THRESHOLD_HOURS:
        print(f"No inbound reply in the last {INBOUND_REMINDER_THRESHOLD_HOURS}h "
              f"(measured: {hours}); sending reminder.")
        send_whatsapp(msg=REMINDER_MESSAGE, media_url=None,
                      account_sid=TWILIO_ACCOUNT_SID, auth_token=TWILIO_AUTH_TOKEN,
                      from_number=TWILIO_WHATSAPP_FROM, to_number=WHATSAPP_TO_NUMBER)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh_window_months", default=DEFAULT_REFRESH_WINDOW_MONTHS, type=int)
    args = parser.parse_args()

    main(args.refresh_window_months)
