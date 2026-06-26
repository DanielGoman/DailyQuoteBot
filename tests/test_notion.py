import datetime
from unittest.mock import MagicMock, patch

from dateutil.relativedelta import relativedelta

from src.daily_service.notion import (
    get_next_quote,
    get_unsent_quotes,
    reset_quotes_tracker,
    update_used_quotes,
    get_favorite,
    set_favorite,
    clear_send_date,
    set_deleted,
)


DB_ID = "db-123"


def _client_with_query_results(*result_batches):
    client = MagicMock()
    client.databases.query.side_effect = [
        {"results": batch} for batch in result_batches
    ]
    return client


def test_get_unsent_quotes_filters_by_send_date_before_and_empty():
    client = _client_with_query_results([{"id": "q1"}])

    quotes = get_unsent_quotes(client, DB_ID, refresh_window_months=3)

    assert quotes == [{"id": "q1"}]
    call_kwargs = client.databases.query.call_args.kwargs
    assert call_kwargs["database_id"] == DB_ID

    expected_before = (datetime.date.today() - relativedelta(months=3)).isoformat()
    filter_ = call_kwargs["filter"]
    assert filter_ == {
        "and": [
            {
                "or": [
                    {"property": "Send Date", "date": {"before": expected_before}},
                    {"property": "Send Date", "date": {"is_empty": True}},
                ]
            },
            {"property": "Deleted", "checkbox": {"equals": False}},
        ]
    }


@patch("src.daily_service.notion.random.choice", side_effect=lambda xs: xs[0])
def test_get_next_quote_happy_path_returns_a_quote(_mock_choice):
    client = _client_with_query_results([{"id": "q1"}, {"id": "q2"}])

    picked = get_next_quote(client, DB_ID, refresh_window_months=3)

    assert picked == {"id": "q1"}
    assert client.databases.query.call_count == 1
    client.pages.update.assert_not_called()


@patch("src.daily_service.notion.random.choice", side_effect=lambda xs: xs[0])
def test_get_next_quote_resets_when_no_unsent_quotes(_mock_choice):
    client = MagicMock()
    client.databases.query.side_effect = [
        {"results": []},
        {"results": [{"id": "all-1"}, {"id": "all-2"}]},
        {"results": [{"id": "all-1"}, {"id": "all-2"}]},
    ]

    picked = get_next_quote(client, DB_ID, refresh_window_months=3)

    assert picked == {"id": "all-1"}
    assert client.databases.query.call_count == 3
    assert client.pages.update.call_count == 2
    for c in client.pages.update.call_args_list:
        assert c.kwargs["properties"] == {"Send Date": {"date": None}}


def test_reset_quotes_tracker_clears_send_date_for_all_pages():
    client = _client_with_query_results([{"id": "a"}, {"id": "b"}, {"id": "c"}])

    reset_quotes_tracker(client, DB_ID)

    assert client.pages.update.call_count == 3
    page_ids = [c.kwargs["page_id"] for c in client.pages.update.call_args_list]
    assert page_ids == ["a", "b", "c"]
    for c in client.pages.update.call_args_list:
        assert c.kwargs["properties"] == {"Send Date": {"date": None}}


def test_update_used_quotes_stamps_today_on_the_picked_page():
    client = MagicMock()
    quote = {"id": "picked-1"}

    update_used_quotes(client, quote)

    today_iso = datetime.date.today().isoformat()
    client.pages.update.assert_called_once_with(
        page_id="picked-1",
        properties={"Send Date": {"date": {"start": today_iso}}},
    )


def test_get_favorite_reads_checkbox():
    client = MagicMock()
    client.pages.retrieve.return_value = {
        "properties": {"Favorite": {"checkbox": True}}
    }

    assert get_favorite(client, "page-1") is True
    client.pages.retrieve.assert_called_once_with(page_id="page-1")


def test_get_favorite_defaults_false_when_missing():
    client = MagicMock()
    client.pages.retrieve.return_value = {"properties": {}}

    assert get_favorite(client, "page-1") is False


def test_set_favorite_updates_checkbox():
    client = MagicMock()

    set_favorite(client, "page-1", True)

    client.pages.update.assert_called_once_with(
        page_id="page-1", properties={"Favorite": {"checkbox": True}}
    )


def test_clear_send_date_sets_date_none():
    client = MagicMock()

    clear_send_date(client, "page-1")

    client.pages.update.assert_called_once_with(
        page_id="page-1", properties={"Send Date": {"date": None}}
    )


def test_set_deleted_defaults_true():
    client = MagicMock()

    set_deleted(client, "page-1")

    client.pages.update.assert_called_once_with(
        page_id="page-1", properties={"Deleted": {"checkbox": True}}
    )
