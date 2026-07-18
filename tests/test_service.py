from unittest.mock import patch, MagicMock

from src.daily_service.service import pick_and_send


@patch("src.daily_service.service.update_used_quotes")
@patch("src.daily_service.service.send_telegram")
@patch("src.daily_service.service.format_response", return_value=("msg", None))
@patch("src.daily_service.service.get_next_quote",
       return_value={"id": "p1", "properties": {}})
@patch("src.daily_service.service.get_active_filter",
       return_value=(["Stoicism"], ["Meditations"]))
def test_pick_and_send_applies_active_filter(mock_filter, mock_next, *_):
    client = MagicMock()

    pick_and_send(client, "db", "tok", "chat", refresh_window_months=3,
                  config_page_id="cfg")

    mock_filter.assert_called_once_with(client, "cfg")
    assert mock_next.call_args.kwargs["active_genres"] == ["Stoicism"]
    assert mock_next.call_args.kwargs["active_sources"] == ["Meditations"]


@patch("src.daily_service.service.update_used_quotes")
@patch("src.daily_service.service.send_telegram")
@patch("src.daily_service.service.format_response", return_value=("msg", None))
@patch("src.daily_service.service.get_next_quote",
       return_value={"id": "p1", "properties": {}})
@patch("src.daily_service.service.get_active_filter")
def test_pick_and_send_without_config_skips_filter(mock_filter, mock_next, *_):
    client = MagicMock()

    pick_and_send(client, "db", "tok", "chat", refresh_window_months=3)

    mock_filter.assert_not_called()
    assert mock_next.call_args.kwargs["active_genres"] == []
    assert mock_next.call_args.kwargs["active_sources"] == []
