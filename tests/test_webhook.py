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


def _dispatch(update, notion_client, bot):
    handle_update(update, notion_client, bot, chat_id=CHAT_ID, notion_db_id=DB_ID,
                  bot_token=BOT_TOKEN, refresh_window_months=3)


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
    bot.answer_callback_query.assert_called_once()


def test_tap_from_wrong_user_is_ignored():
    notion = MagicMock()
    bot = MagicMock()

    _dispatch(_update("del:page-1", from_id=99999), notion, bot)

    notion.pages.update.assert_not_called()
    bot.edit_message_reply_markup.assert_not_called()
    # Still answers the callback (to stop the spinner) but with a rejection.
    bot.answer_callback_query.assert_called_once()
    assert "Not authorized" in bot.answer_callback_query.call_args.args[1]
