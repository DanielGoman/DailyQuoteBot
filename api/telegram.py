import os
import sys
import json
from http.server import BaseHTTPRequestHandler

import telebot
from notion_client import Client

# Make the shared src package importable when bundled on Vercel.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.daily_service.consts import DEFAULT_REFRESH_WINDOW_MONTHS, Callback
from src.daily_service.telegram import (build_quote_keyboard, build_filters_keyboard,
                                        format_active_filter)
from src.daily_service.service import pick_and_send
from src.daily_service.notion import (get_favorite, set_favorite,
                                       clear_send_date, set_deleted)
from src.daily_service.config import (get_active_filter, clear_filter,
                                      toggle_genre, toggle_source,
                                      list_genre_options, list_source_values)


FILTER_ACTIONS_NEEDING_CONFIG = (Callback.OPEN_FILTERS, Callback.TOGGLE_GENRE,
                                 Callback.TOGGLE_SOURCE, Callback.CLEAR_FILTERS)


def _build_filters_markup(notion_client, notion_db_id, config_page_id):
    """Fetch the current menu vocabulary + active filter and render the keyboard."""
    genre_options = list_genre_options(notion_client, notion_db_id)
    source_options = list_source_values(notion_client, notion_db_id)
    active_genres, active_sources = get_active_filter(notion_client, config_page_id)
    return build_filters_keyboard(genre_options, source_options,
                                  active_genres, active_sources)


def _toggle_filter_value(cq, bot, action, arg, notion_client, notion_db_id,
                         config_page_id) -> None:
    """Resolve a gf:/sf: index against the freshly-derived option list, toggle it
    on the config page, and re-render the menu keyboard in place."""
    if action == Callback.TOGGLE_GENRE:
        options = list_genre_options(notion_client, notion_db_id)
        toggle = toggle_genre
    else:
        options = list_source_values(notion_client, notion_db_id)
        toggle = toggle_source
    try:
        idx = int(arg)
    except ValueError:
        idx = -1
    if 0 <= idx < len(options):
        toggle(notion_client, config_page_id, options[idx])
        note = options[idx]
    else:
        note = "Option changed — reopen the menu"
    bot.edit_message_reply_markup(
        chat_id=cq.message.chat.id, message_id=cq.message.message_id,
        reply_markup=_build_filters_markup(notion_client, notion_db_id, config_page_id))
    bot.answer_callback_query(cq.id, note)


def _handle_filter_action(cq, bot, action, arg, notion_client, notion_db_id,
                          config_page_id) -> bool:
    """Handle the filter-menu callbacks. Returns True if the action belonged to the
    filter menu (so the caller stops dispatching), False otherwise."""
    if action in FILTER_ACTIONS_NEEDING_CONFIG and not config_page_id:
        bot.answer_callback_query(cq.id, "Filters not configured")
        return True

    msg_chat, msg_id = cq.message.chat.id, cq.message.message_id
    if action == Callback.OPEN_FILTERS:
        bot.send_message(msg_chat, "🎛 Tap to toggle genres and sources:",
                         reply_markup=_build_filters_markup(notion_client, notion_db_id,
                                                            config_page_id))
        bot.answer_callback_query(cq.id)
    elif action in (Callback.TOGGLE_GENRE, Callback.TOGGLE_SOURCE):
        _toggle_filter_value(cq, bot, action, arg, notion_client, notion_db_id,
                             config_page_id)
    elif action == Callback.CLEAR_FILTERS:
        clear_filter(notion_client, config_page_id)
        bot.edit_message_reply_markup(
            chat_id=msg_chat, message_id=msg_id,
            reply_markup=_build_filters_markup(notion_client, notion_db_id, config_page_id))
        bot.answer_callback_query(cq.id, "🧹 Cleared")
    elif action == Callback.DONE_FILTERS:
        active_genres, active_sources = ([], [])
        if config_page_id:
            active_genres, active_sources = get_active_filter(notion_client, config_page_id)
        bot.edit_message_text(format_active_filter(active_genres, active_sources),
                              chat_id=msg_chat, message_id=msg_id)
        bot.answer_callback_query(cq.id, "✔ Saved")
    else:
        return False
    return True


def handle_update(update, notion_client, bot, chat_id, notion_db_id,
                  bot_token, refresh_window_months, config_page_id) -> None:
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

    action, _, arg = (cq.data or "").partition(":")
    msg_chat = cq.message.chat.id
    msg_id = cq.message.message_id

    # Quote actions (arg is the Notion page id).
    if action == Callback.FAVORITE:
        new_value = not get_favorite(notion_client, arg)
        set_favorite(notion_client, arg, new_value)
        bot.edit_message_reply_markup(
            chat_id=msg_chat, message_id=msg_id,
            reply_markup=build_quote_keyboard(arg, new_value))
        bot.answer_callback_query(cq.id,
                                  "⭐ Favorited" if new_value else "☆ Removed from favorites")
    elif action == Callback.CYCLE:
        clear_send_date(notion_client, arg)
        bot.answer_callback_query(cq.id, "🔁 Put back in cycle")
    elif action == Callback.DELETE:
        set_deleted(notion_client, arg, True)
        bot.edit_message_reply_markup(chat_id=msg_chat, message_id=msg_id, reply_markup=None)
        bot.answer_callback_query(cq.id, "🗑 Deleted")
    elif action == Callback.MORE:
        pick_and_send(notion_client=notion_client, notion_db_id=notion_db_id,
                      bot_token=bot_token, chat_id=chat_id,
                      refresh_window_months=refresh_window_months,
                      config_page_id=config_page_id)
        bot.answer_callback_query(cq.id, "➕ Sent another")
    elif _handle_filter_action(cq, bot, action, arg, notion_client, notion_db_id,
                               config_page_id):
        pass  # handled by the filter menu
    else:  # NOOP label buttons and anything unrecognised.
        bot.answer_callback_query(cq.id)


class handler(BaseHTTPRequestHandler):  # pylint: disable=invalid-name
    # Class/method names are dictated by the http.server + Vercel handler contract.
    def do_POST(self):  # pylint: disable=invalid-name
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
                          refresh_window_months=refresh,
                          config_page_id=os.environ.get("NOTION_CONFIG_PAGE_ID"))
        except Exception as e:
            print(f"Webhook error: {e}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
