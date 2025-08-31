import telegram

from src.bot_service.telegram_bot import get_command_handler
from src.daily_service.consts import Telegram


async def send_telegram(msg: str, quote_id: str, media_url: str = None, telegram_bot_token: str = None,
                        telegram_chat_id: str = None) -> None:
    bot = telegram.Bot(token=telegram_bot_token)
    command_handler = get_command_handler(metadata_str=quote_id)
    try:
        if media_url:
            if len(msg) > Telegram.IMAGE_CAPTION_TEXT_LENGTH_LIMIT:
                messages = split_message(msg)
                await bot.send_photo(chat_id=telegram_chat_id, photo=media_url, reply_markup=command_handler)
                for msg in messages:
                    await bot.send_message(chat_id=telegram_chat_id, text=msg)
                else:
                    await bot.send_message(chat_id=telegram_chat_id, text=msg, reply_markup=command_handler)
            else:
                await bot.send_photo(chat_id=telegram_chat_id, photo=media_url, caption=msg,
                                     reply_markup=command_handler)
        else:
            await bot.send_message(chat_id=telegram_chat_id, text=msg, reply_markup=command_handler)
        print("Message sent successfully!")
    except Exception as e:
        print(f"Failed to send message: {e}")


def split_message(message: str) -> list[str]:
    return [message[i:i + Telegram.TEXT_MESSAGE_LENGTH_LIMIT - 3] + "..."
            for i in range(0, len(message), Telegram.TEXT_MESSAGE_LENGTH_LIMIT - 3)]
