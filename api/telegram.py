import os
import sys
import json
from http.server import BaseHTTPRequestHandler

import telebot
from notion_client import Client

# Make the shared src package importable when bundled on Vercel.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.daily_service.consts import DEFAULT_REFRESH_WINDOW_MONTHS
from src.daily_service.telegram import build_quote_keyboard
from src.daily_service.service import pick_and_send
from src.daily_service.notion import (get_favorite, set_favorite,
                                       clear_send_date, set_deleted)


def handle_update(update, notion_client, bot, chat_id, notion_db_id,
                  bot_token, refresh_window_months) -> None:
    """Dispatch a single Telegram update. Only callback-query taps from the
    configured chat are acted on; every path answers the callback so the button
    spinner stops."""
    cq = update.callback_query
    if cq is None:
        return

    # Only the configured recipient may drive the buttons.
    if str(cq.from_user.id) != str(chat_id):
        bot.answer_callback_query(cq.id, "Not authorized")
        return

    action, _, page_id = (cq.data or "").partition(":")
    msg_chat = cq.message.chat.id
    msg_id = cq.message.message_id

    if action == "fav":
        new_value = not get_favorite(notion_client, page_id)
        set_favorite(notion_client, page_id, new_value)
        bot.edit_message_reply_markup(
            chat_id=msg_chat, message_id=msg_id,
            reply_markup=build_quote_keyboard(page_id, new_value))
        bot.answer_callback_query(cq.id,
                                  "⭐ Favorited" if new_value else "☆ Removed from favorites")
    elif action == "cycle":
        clear_send_date(notion_client, page_id)
        bot.answer_callback_query(cq.id, "🔁 Put back in cycle")
    elif action == "del":
        set_deleted(notion_client, page_id, True)
        bot.edit_message_reply_markup(chat_id=msg_chat, message_id=msg_id, reply_markup=None)
        bot.answer_callback_query(cq.id, "🗑 Deleted")
    elif action == "more":
        pick_and_send(notion_client=notion_client, notion_db_id=notion_db_id,
                      bot_token=bot_token, chat_id=chat_id,
                      refresh_window_months=refresh_window_months)
        bot.answer_callback_query(cq.id, "➕ Sent another")
    else:
        bot.answer_callback_query(cq.id)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Reject anything not carrying Telegram's secret token.
        secret = os.environ["TELEGRAM_WEBHOOK_SECRET"]
        if self.headers.get("X-Telegram-Bot-Api-Secret-Token") != secret:
            self.send_response(401)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8") if length else "{}"

        try:
            update = telebot.types.Update.de_json(json.loads(body))
            bot = telebot.TeleBot(os.environ["TELEGRAM_BOT_TOKEN"])
            notion_client = Client(auth=os.environ["NOTION_TOKEN"])
            refresh = int(os.environ.get("REFRESH_WINDOW_MONTHS",
                                         DEFAULT_REFRESH_WINDOW_MONTHS))
            handle_update(update, notion_client, bot,
                          chat_id=os.environ["TELEGRAM_CHAT_ID"],
                          notion_db_id=os.environ["NOTION_DB_ID"],
                          bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
                          refresh_window_months=refresh)
        except Exception as e:
            print(f"Webhook error: {e}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
