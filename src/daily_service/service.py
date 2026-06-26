from notion_client import Client

from src.daily_service.utils import format_response
from src.daily_service.telegram import send_telegram, build_quote_keyboard
from src.daily_service.notion import get_next_quote, update_used_quotes


def _is_favorite(quote: dict) -> bool:
    return bool(quote.get("properties", {}).get("Favorite", {}).get("checkbox", False))


def pick_and_send(notion_client: Client, notion_db_id: str, bot_token: str,
                  chat_id: str, refresh_window_months: int) -> None:
    """Core daily-send flow, shared by the cron entry point and the webhook's
    'Send another now' button."""
    next_quote = get_next_quote(notion_client=notion_client, notion_db_id=notion_db_id,
                                refresh_window_months=refresh_window_months)
    if next_quote:
        message, media_url = format_response(next_quote)
        keyboard = build_quote_keyboard(next_quote["id"], _is_favorite(next_quote))
        send_telegram(msg=message, media_url=media_url, bot_token=bot_token,
                      chat_id=chat_id, reply_markup=keyboard)
        update_used_quotes(notion_client, next_quote)
    else:
        send_telegram(msg="⚠️ No sentences found in Notion.", media_url=None,
                      bot_token=bot_token, chat_id=chat_id)
