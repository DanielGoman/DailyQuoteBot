import telebot

from src.daily_service.consts import Telegram, Callback

ACTIVE_MARK = "✅"
INACTIVE_MARK = "▫️"


def build_quote_keyboard(page_id: str, is_favorite: bool) -> "telebot.types.InlineKeyboardMarkup":
    """Inline keyboard attached to each quote. The favorite button toggles, so its
    label reflects the current state."""
    markup = telebot.types.InlineKeyboardMarkup()
    fav_label = "☆ Unfavorite" if is_favorite else "⭐ Favorite"
    markup.row(
        telebot.types.InlineKeyboardButton(
            fav_label, callback_data=f"{Callback.FAVORITE}:{page_id}"),
        telebot.types.InlineKeyboardButton(
            "🔁 Put back", callback_data=f"{Callback.CYCLE}:{page_id}"),
    )
    markup.row(
        telebot.types.InlineKeyboardButton(
            "🗑 Delete", callback_data=f"{Callback.DELETE}:{page_id}"),
        telebot.types.InlineKeyboardButton("➕ Send another", callback_data=Callback.MORE),
    )
    markup.row(
        telebot.types.InlineKeyboardButton("🎛 Filters", callback_data=Callback.OPEN_FILTERS),
    )
    return markup


def build_filters_keyboard(genre_options: list[str], source_options: list[str],
                           active_genres: list[str], active_sources: list[str],
                           ) -> "telebot.types.InlineKeyboardMarkup":
    """Multi-toggle menu. Each option shows ✅/▫️ for its state and is encoded by
    index (gf:<i> / sf:<i>) to stay under Telegram's 64-byte callback_data limit —
    the handler re-derives the same sorted option lists to resolve the index."""
    markup = telebot.types.InlineKeyboardMarkup()

    markup.row(telebot.types.InlineKeyboardButton("🏷 Genres", callback_data=Callback.NOOP))
    for i, name in enumerate(genre_options):
        mark = ACTIVE_MARK if name in active_genres else INACTIVE_MARK
        markup.row(telebot.types.InlineKeyboardButton(
            f"{mark} {name}", callback_data=f"{Callback.TOGGLE_GENRE}:{i}"))

    markup.row(telebot.types.InlineKeyboardButton("📚 Sources", callback_data=Callback.NOOP))
    for i, name in enumerate(source_options):
        mark = ACTIVE_MARK if name in active_sources else INACTIVE_MARK
        markup.row(telebot.types.InlineKeyboardButton(
            f"{mark} {name}", callback_data=f"{Callback.TOGGLE_SOURCE}:{i}"))

    markup.row(
        telebot.types.InlineKeyboardButton("🧹 Clear all", callback_data=Callback.CLEAR_FILTERS),
        telebot.types.InlineKeyboardButton("✔ Done", callback_data=Callback.DONE_FILTERS),
    )
    return markup


def _button_name(text: str) -> str:
    """Strip the leading ✅/▫️ mark off a toggle button's label."""
    return text.split(" ", 1)[1] if " " in text else text


def _is_toggle(callback_data: str | None) -> bool:
    data = callback_data or ""
    return (data.startswith(f"{Callback.TOGGLE_GENRE}:")
            or data.startswith(f"{Callback.TOGGLE_SOURCE}:"))


def toggle_keyboard_option(markup, callback_data: str):
    """Flip the ✅/▫️ mark on the button with this callback_data, in place. Lets the
    menu update purely from the message's own keyboard — no Notion round-trip."""
    for row in markup.keyboard:
        for btn in row:
            if btn.callback_data == callback_data:
                mark = INACTIVE_MARK if btn.text.startswith(ACTIVE_MARK) else ACTIVE_MARK
                btn.text = f"{mark} {_button_name(btn.text)}"
    return markup


def clear_keyboard_marks(markup):
    """Set every toggle button on the menu keyboard to inactive, in place."""
    for row in markup.keyboard:
        for btn in row:
            if _is_toggle(btn.callback_data):
                btn.text = f"{INACTIVE_MARK} {_button_name(btn.text)}"
    return markup


def parse_active_from_keyboard(markup) -> tuple[list[str], list[str]]:
    """Read (active_genres, active_sources) back out of a menu keyboard's checkmarks."""
    genres, sources = [], []
    for row in markup.keyboard:
        for btn in row:
            data = btn.callback_data or ""
            if not btn.text.startswith(ACTIVE_MARK):
                continue
            if data.startswith(f"{Callback.TOGGLE_GENRE}:"):
                genres.append(_button_name(btn.text))
            elif data.startswith(f"{Callback.TOGGLE_SOURCE}:"):
                sources.append(_button_name(btn.text))
    return genres, sources


def format_active_filter(active_genres: list[str], active_sources: list[str]) -> str:
    """Human-readable summary of the active filter, shown when the menu is closed."""
    if not active_genres and not active_sources:
        return "🎛 Filters: none (sending from all quotes)"
    genres = ", ".join(active_genres) if active_genres else "any"
    sources = ", ".join(active_sources) if active_sources else "any"
    return f"🎛 Filters\nGenres: {genres}\nSources: {sources}"


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
