import telebot

from src.daily_service.consts import Telegram


def send_telegram(msg: str, media_url: str | None, bot_token: str, chat_id: str) -> None:
    bot = telebot.TeleBot(bot_token)

    try:
        if media_url and len(msg) <= Telegram.CAPTION_TEXT_LENGTH_LIMIT:
            bot.send_photo(chat_id, photo=media_url, caption=msg, parse_mode="HTML")
        elif media_url:
            bot.send_photo(chat_id, photo=media_url)
            for chunk in split_message(msg):
                bot.send_message(chat_id, chunk, parse_mode="HTML",
                                 disable_web_page_preview=True)
        else:
            for chunk in split_message(msg):
                bot.send_message(chat_id, chunk, parse_mode="HTML",
                                 disable_web_page_preview=True)
        print("Message sent successfully!")
    except Exception as e:
        print(f"Failed to send message: {e}")


def split_message(message: str) -> list[str]:
    limit = Telegram.TEXT_MESSAGE_LENGTH_LIMIT
    if len(message) <= limit:
        return [message]
    return [message[i:i + limit - 3] + "..."
            for i in range(0, len(message), limit - 3)]
