import os

from notion_client import Client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CallbackQueryHandler

from src.bot_service.bot_actions import action_make_favorite, action_put_back_to_cycle, action_delete_quote
from src.bot_service.consts import Callbacks, FavoriteToggleStates

NOTION_TOKEN = os.environ['NOTION_TOKEN']


BOT_ACTIONS = {
    Callbacks.FAVORITE_TOGGLE: action_make_favorite,
    Callbacks.PUT_BACK_TO_CYCLE: action_put_back_to_cycle,
    Callbacks.DELETE_QUOTE: action_delete_quote
}


def get_telegram_bot(telegram_bot_token: str):
    bot_app = Application.builder().token(telegram_bot_token).build()
    bot_app.add_handler(CallbackQueryHandler(callback_handler))

    return bot_app


def get_command_handler(metadata_str: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(FavoriteToggleStates.MAKE_FAVORITE, callback_data=f"{Callbacks.FAVORITE_TOGGLE}:{metadata_str}"),
          InlineKeyboardButton("Delete quote", callback_data=f"{Callbacks.DELETE_QUOTE}:{metadata_str}")],
        [InlineKeyboardButton("Put back into cycle", callback_data=f"{Callbacks.PUT_BACK_TO_CYCLE}:{metadata_str}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()

    action, quote_id = query.data.split(':')
    action_method = BOT_ACTIONS[action]

    notion_client = Client(auth=NOTION_TOKEN)
    await action_method(notion_client, quote_id, query=query)
