import telebot

from src.daily_service.consts import Telegram


def build_quote_keyboard(page_id: str, is_favorite: bool) -> "telebot.types.InlineKeyboardMarkup":
    """Inline keyboard attached to each quote. The favorite button toggles, so its
    label reflects the current state."""
    markup = telebot.types.InlineKeyboardMarkup()
    fav_label = "☆ Unfavorite" if is_favorite else "⭐ Favorite"
    markup.row(
        telebot.types.InlineKeyboardButton(fav_label, callback_data=f"fav:{page_id}"),
        telebot.types.InlineKeyboardButton("🔁 Put back", callback_data=f"cycle:{page_id}"),
    )
    markup.row(
        telebot.types.InlineKeyboardButton("🗑 Delete", callback_data=f"del:{page_id}"),
        telebot.types.InlineKeyboardButton("➕ Send another", callback_data="more"),
    )
    return markup


def send_telegram(msg: str, media_url: str | None, bot_token: str, chat_id: str,
                  reply_markup=None) -> None:
    bot = telebot.TeleBot(bot_token)

    try:
        if media_url and len(msg) <= Telegram.CAPTION_TEXT_LENGTH_LIMIT:
            bot.send_photo(chat_id, photo=media_url, caption=msg, parse_mode="HTML",
                           reply_markup=reply_markup)
        elif media_url:
            bot.send_photo(chat_id, photo=media_url)
            _send_text_chunks(bot, chat_id, msg, reply_markup)
        else:
            _send_text_chunks(bot, chat_id, msg, reply_markup)
        print("Message sent successfully!")
    except Exception as e:
        print(f"Failed to send message: {e}")


def _send_text_chunks(bot, chat_id: str, msg: str, reply_markup) -> None:
    """Send the body as one or more chunks, attaching the keyboard to the last one."""
    chunks = split_message(msg)
    for i, chunk in enumerate(chunks):
        markup = reply_markup if i == len(chunks) - 1 else None
        bot.send_message(chat_id, chunk, parse_mode="HTML",
                         disable_web_page_preview=True, reply_markup=markup)


def split_message(message: str) -> list[str]:
    limit = Telegram.TEXT_MESSAGE_LENGTH_LIMIT
    if len(message) <= limit:
        return [message]
    return [message[i:i + limit - 3] + "..."
            for i in range(0, len(message), limit - 3)]
