from unittest.mock import patch, call

from src.daily_service.telegram import send_telegram, split_message
from src.daily_service.consts import Telegram


BOT_TOKEN = "123456:test_token"
CHAT_ID = "987654321"


def test_split_message_short_returns_single_chunk():
    assert split_message("hello") == ["hello"]


def test_split_message_at_exact_limit_returns_single_chunk():
    msg = "a" * Telegram.TEXT_MESSAGE_LENGTH_LIMIT
    assert split_message(msg) == [msg]


def test_split_message_long_splits_with_ellipsis_suffix():
    limit = Telegram.TEXT_MESSAGE_LENGTH_LIMIT
    msg = "a" * (limit + 100)

    chunks = split_message(msg)

    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= limit
        assert chunk.endswith("...")


@patch("src.daily_service.telegram.telebot.TeleBot")
def test_send_telegram_media_with_short_caption_sends_single_photo(MockTeleBot):
    bot = MockTeleBot.return_value
    msg = "short caption"
    media_url = "https://example.com/img.png"

    send_telegram(msg, media_url, BOT_TOKEN, CHAT_ID)

    MockTeleBot.assert_called_once_with(BOT_TOKEN)
    bot.send_photo.assert_called_once_with(
        CHAT_ID, photo=media_url, caption=msg, parse_mode="HTML"
    )
    bot.send_message.assert_not_called()


@patch("src.daily_service.telegram.telebot.TeleBot")
def test_send_telegram_media_with_long_caption_sends_photo_then_text(MockTeleBot):
    bot = MockTeleBot.return_value
    media_url = "https://example.com/img.png"
    msg = "x" * (Telegram.CAPTION_TEXT_LENGTH_LIMIT + 1)

    send_telegram(msg, media_url, BOT_TOKEN, CHAT_ID)

    bot.send_photo.assert_called_once_with(CHAT_ID, photo=media_url)
    assert bot.send_message.call_count >= 1
    for c in bot.send_message.call_args_list:
        assert c.args[0] == CHAT_ID
        assert c.kwargs["disable_web_page_preview"] is True


@patch("src.daily_service.telegram.telebot.TeleBot")
def test_send_telegram_text_only_sends_chunks(MockTeleBot):
    bot = MockTeleBot.return_value
    msg = "y" * (Telegram.TEXT_MESSAGE_LENGTH_LIMIT + 10)

    send_telegram(msg, None, BOT_TOKEN, CHAT_ID)

    bot.send_photo.assert_not_called()
    assert bot.send_message.call_count >= 2
    for c in bot.send_message.call_args_list:
        assert c.args[0] == CHAT_ID
        assert c.kwargs["disable_web_page_preview"] is True


@patch("src.daily_service.telegram.telebot.TeleBot")
def test_send_telegram_text_only_short_sends_single_message(MockTeleBot):
    bot = MockTeleBot.return_value

    send_telegram("hi", None, BOT_TOKEN, CHAT_ID)

    bot.send_message.assert_called_once_with(
        CHAT_ID, "hi", parse_mode="HTML", disable_web_page_preview=True
    )
    bot.send_photo.assert_not_called()


@patch("src.daily_service.telegram.telebot.TeleBot")
def test_send_telegram_swallows_errors(MockTeleBot, capsys):
    bot = MockTeleBot.return_value
    bot.send_message.side_effect = RuntimeError("telegram down")

    send_telegram("hi", None, BOT_TOKEN, CHAT_ID)

    captured = capsys.readouterr()
    assert "Failed to send message" in captured.out
