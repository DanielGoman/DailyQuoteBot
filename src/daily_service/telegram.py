import requests
import telegram

from src.bot_service.consts import API
from src.daily_service.consts import Telegram


async def send_telegram(msg: str, media_url: str = None, telegram_bot_token: str = None,
                        telegram_chat_id: str = None) -> str | None:
    sent_message = None
    bot = telegram.Bot(token=telegram_bot_token)

    try:

        if media_url:
            if len(msg) > Telegram.IMAGE_CAPTION_TEXT_LENGTH_LIMIT:
                messages = split_message(msg)
                await bot.send_photo(chat_id=telegram_chat_id, photo=media_url)
                for msg in messages:
                    sent_message = await bot.send_message(chat_id=telegram_chat_id, text=msg)
            else:
                sent_message = await bot.send_photo(chat_id=telegram_chat_id, photo=media_url, caption=msg)
        else:
            sent_message = await bot.send_message(chat_id=telegram_chat_id, text=msg)
        print("Message sent successfully!")
    except Exception as e:
        print(f"Failed to send message: {e}")

    message_id = sent_message.message_id if sent_message else None
    return message_id


def split_message(message: str) -> list[str]:
    return [message[i:i + Telegram.TEXT_MESSAGE_LENGTH_LIMIT - 3] + "..."
            for i in range(0, len(message), Telegram.TEXT_MESSAGE_LENGTH_LIMIT - 3)]


def send_info_to_bot_service(message_id: str, chat_id: str) -> None:
    payload = {
        'message_id': str(message_id),
        'chat_id': chat_id
    }

    res = requests.post(API.URL, json=payload)
    # Check the response
    if res.status_code == 200:
        print("Sent message info to bot service successfully!")
    else:
        print("Failed:", res.status_code, res.text)
