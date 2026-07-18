from unittest.mock import MagicMock, patch

import telebot

from api.telegram import handle_update
from src.daily_service.telegram import build_filters_keyboard, ACTIVE_MARK, INACTIVE_MARK


CHAT_ID = "12345"
DB_ID = "db-1"
BOT_TOKEN = "tok"


def _update(data, from_id=int(CHAT_ID)):
    return telebot.types.Update.de_json({
        "update_id": 1,
        "callback_query": {
            "id": "cb-1",
            "from": {"id": from_id, "is_bot": False, "first_name": "U"},
            "chat_instance": "ci",
            "message": {
                "message_id": 99,
                "date": 0,
                "chat": {"id": int(CHAT_ID), "type": "private"},
            },
            "data": data,
        },
    })


def _menu_update(data, genres, sources, active_genres, active_sources):
    """A callback tap on an open filter menu — the message carries the menu keyboard."""
    update = _update(data)
    update.callback_query.message.reply_markup = build_filters_keyboard(
        genres, sources, active_genres, active_sources)
    return update


def _flatten(markup):
    return [btn for row in markup.keyboard for btn in row]


def _dispatch(update, notion_client, bot, config_page_id="cfg-1"):
    handle_update(update, notion_client, bot, chat_id=CHAT_ID, notion_db_id=DB_ID,
                  bot_token=BOT_TOKEN, refresh_window_months=3,
                  config_page_id=config_page_id)


def test_favorite_toggles_on_and_edits_keyboard():
    notion = MagicMock()
    notion.pages.retrieve.return_value = {"properties": {"Favorite": {"checkbox": False}}}
    bot = MagicMock()

    _dispatch(_update("fav:page-1"), notion, bot)

    notion.pages.update.assert_called_once_with(
        page_id="page-1", properties={"Favorite": {"checkbox": True}}
    )
    bot.edit_message_reply_markup.assert_called_once()
    bot.answer_callback_query.assert_called_once()
    assert "Favorited" in bot.answer_callback_query.call_args.args[1]


def test_cycle_clears_send_date():
    notion = MagicMock()
    bot = MagicMock()

    _dispatch(_update("cycle:page-1"), notion, bot)

    notion.pages.update.assert_called_once_with(
        page_id="page-1", properties={"Send Date": {"date": None}}
    )
    bot.answer_callback_query.assert_called_once()


def test_delete_sets_flag_and_removes_buttons():
    notion = MagicMock()
    bot = MagicMock()

    _dispatch(_update("del:page-1"), notion, bot)

    notion.pages.update.assert_called_once_with(
        page_id="page-1", properties={"Deleted": {"checkbox": True}}
    )
    bot.edit_message_reply_markup.assert_called_once_with(
        chat_id=int(CHAT_ID), message_id=99, reply_markup=None
    )
    bot.answer_callback_query.assert_called_once()


@patch("api.telegram.pick_and_send")
def test_more_sends_another_quote(mock_pick_and_send):
    notion = MagicMock()
    bot = MagicMock()

    _dispatch(_update("more"), notion, bot)

    mock_pick_and_send.assert_called_once()
    assert mock_pick_and_send.call_args.kwargs["notion_db_id"] == DB_ID
    assert mock_pick_and_send.call_args.kwargs["config_page_id"] == "cfg-1"
    bot.answer_callback_query.assert_called_once()


@patch("api.telegram.get_active_filter", return_value=([], []))
@patch("api.telegram.list_source_values", return_value=["Meditations"])
@patch("api.telegram.list_genre_options", return_value=["Stoicism", "Zen"])
def test_open_filters_sends_menu(_genres, _sources, _active):
    notion = MagicMock()
    bot = MagicMock()

    _dispatch(_update("filters"), notion, bot)

    bot.send_message.assert_called_once()
    assert bot.send_message.call_args.kwargs["reply_markup"] is not None
    bot.answer_callback_query.assert_called_once()


def test_open_filters_without_config_is_rejected():
    notion = MagicMock()
    bot = MagicMock()

    _dispatch(_update("filters"), notion, bot, config_page_id=None)

    bot.send_message.assert_not_called()
    assert "not configured" in bot.answer_callback_query.call_args.args[1]


def test_toggle_genre_flips_mark_without_notion_write():
    notion = MagicMock()
    bot = MagicMock()
    update = _menu_update("gf:1", ["Stoicism", "Zen"], ["Meditations"], [], [])

    _dispatch(update, notion, bot)

    # A toggle only edits the message keyboard — it must not touch Notion.
    notion.pages.update.assert_not_called()
    markup = bot.edit_message_reply_markup.call_args.kwargs["reply_markup"]
    by_data = {b.callback_data: b.text for b in _flatten(markup)}
    assert by_data["gf:1"].startswith(ACTIVE_MARK)   # Zen now active
    assert by_data["gf:0"].startswith(INACTIVE_MARK)  # Stoicism untouched


def test_clear_filters_marks_all_inactive_without_notion_write():
    notion = MagicMock()
    bot = MagicMock()
    update = _menu_update("fclr", ["Stoicism"], ["Meditations"],
                          ["Stoicism"], ["Meditations"])

    _dispatch(update, notion, bot)

    notion.pages.update.assert_not_called()
    markup = bot.edit_message_reply_markup.call_args.kwargs["reply_markup"]
    for btn in _flatten(markup):
        if (btn.callback_data or "").startswith(("gf:", "sf:")):
            assert btn.text.startswith(INACTIVE_MARK)


@patch("api.telegram.set_active_filter")
def test_done_persists_selection_once_and_shows_summary(mock_set):
    notion = MagicMock()
    bot = MagicMock()
    update = _menu_update("fdone", ["Stoicism", "Zen"], ["Meditations"],
                          ["Zen"], ["Meditations"])

    _dispatch(update, notion, bot)

    # Persisted exactly once, with the keyboard's active selection.
    mock_set.assert_called_once_with(notion, "cfg-1", ["Zen"], ["Meditations"])
    summary = bot.edit_message_text.call_args.args[0]
    assert "Zen" in summary and "Meditations" in summary


def test_tap_from_wrong_user_is_ignored():
    notion = MagicMock()
    bot = MagicMock()

    _dispatch(_update("del:page-1", from_id=99999), notion, bot)

    notion.pages.update.assert_not_called()
    bot.edit_message_reply_markup.assert_not_called()
    # Still answers the callback (to stop the spinner) but with a rejection.
    bot.answer_callback_query.assert_called_once()
    assert "Not authorized" in bot.answer_callback_query.call_args.args[1]
