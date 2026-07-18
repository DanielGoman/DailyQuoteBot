from unittest.mock import MagicMock, patch

import telebot

from api.telegram import handle_update


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


@patch("api.telegram.get_active_filter", return_value=([], []))
@patch("api.telegram.list_source_values", return_value=[])
@patch("api.telegram.list_genre_options", return_value=["Stoicism", "Zen"])
@patch("api.telegram.toggle_genre")
def test_toggle_genre_resolves_index_and_rerenders(mock_toggle, _genres, _sources, _active):
    notion = MagicMock()
    bot = MagicMock()

    _dispatch(_update("gf:1"), notion, bot)

    mock_toggle.assert_called_once_with(notion, "cfg-1", "Zen")
    bot.edit_message_reply_markup.assert_called_once()
    assert bot.answer_callback_query.call_args.args[1] == "Zen"


@patch("api.telegram.get_active_filter", return_value=([], []))
@patch("api.telegram.list_source_values", return_value=[])
@patch("api.telegram.list_genre_options", return_value=["Stoicism"])
@patch("api.telegram.clear_filter")
def test_clear_filters_clears_and_rerenders(mock_clear, _genres, _sources, _active):
    notion = MagicMock()
    bot = MagicMock()

    _dispatch(_update("fclr"), notion, bot)

    mock_clear.assert_called_once_with(notion, "cfg-1")
    bot.edit_message_reply_markup.assert_called_once()


@patch("api.telegram.get_active_filter", return_value=(["Stoicism"], ["Meditations"]))
def test_done_filters_shows_summary_and_drops_keyboard(_active):
    notion = MagicMock()
    bot = MagicMock()

    _dispatch(_update("fdone"), notion, bot)

    bot.edit_message_text.assert_called_once()
    summary = bot.edit_message_text.call_args.args[0]
    assert "Stoicism" in summary and "Meditations" in summary


def test_tap_from_wrong_user_is_ignored():
    notion = MagicMock()
    bot = MagicMock()

    _dispatch(_update("del:page-1", from_id=99999), notion, bot)

    notion.pages.update.assert_not_called()
    bot.edit_message_reply_markup.assert_not_called()
    # Still answers the callback (to stop the spinner) but with a rejection.
    bot.answer_callback_query.assert_called_once()
    assert "Not authorized" in bot.answer_callback_query.call_args.args[1]
