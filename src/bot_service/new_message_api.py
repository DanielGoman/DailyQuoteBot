from fastapi import FastAPI

from src.bot_service.consts import API
from src.bot_service.notion_bot import TelegramBot, get_command_handler

app = FastAPI()


@app.get('/')
async def root() -> str:
    return "Hello World"


@app.post(f"/add_keyboard_buttons_to_message")
async def add_keyboard_buttons_to_message(payload: dict[str, str]) -> None:
    message_id = int(payload.get("message_id"))
    chat_id = payload.get("chat_id")

    bot_app = TelegramBot.get_instance()
    command_handler = get_command_handler()

    await bot_app.bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=command_handler)
