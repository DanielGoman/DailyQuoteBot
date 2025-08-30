from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CallbackQueryHandler

from src.bot_service.consts import Callbacks



class TelegramBot:
    _instance = None

    @classmethod
    def get_instance(cls, telegram_bot_token: str | None = None):
        if cls._instance is None:
            cls._instance = Application.builder().token(telegram_bot_token).build()
            cls._instance.add_handler(CallbackQueryHandler(callback_handler))
        return cls._instance


def get_command_handler() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Make favorite", callback_data=Callbacks.MAKE_FAVORITE),
          InlineKeyboardButton("Delete quote", callback_data=Callbacks.DELETE_QUOTE)],
        [InlineKeyboardButton("Put back into cycle", callback_data=Callbacks.PUT_BACK_TO_CYCLE)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

