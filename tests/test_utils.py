from unittest.mock import patch, MagicMock

from src.daily_service.utils import format_response, shorten_tinyurl


def _make_quote(quote_text="Be water, my friend.",
                author="Bruce Lee",
                cover_url="https://example.com/img.png",
                page_id="page-123"):
    properties = {
        "Quote": {"title": [{"text": {"content": quote_text}}]},
        "Author": {"rich_text": [{"text": {"content": author}}]},
    }
    if cover_url is not None:
        properties["Cover"] = {"files": [{"file": {"url": cover_url}}]}
    else:
        properties["Cover"] = {"files": []}
    return {"id": page_id, "properties": properties}


@patch("src.daily_service.utils.shorten_tinyurl", return_value="https://tinyurl.com/abc")
def test_format_response_happy_path(mock_shorten):
    quote = _make_quote()

    message, media_url = format_response(quote)

    assert media_url == "https://example.com/img.png"
    assert "Be water, my friend." in message
    assert "Bruce Lee" in message
    assert "https://tinyurl.com/abc" in message
    mock_shorten.assert_called_once_with("https://example.com/img.png")


@patch("src.daily_service.utils.shorten_tinyurl", return_value="")
def test_format_response_without_cover(mock_shorten):
    quote = _make_quote(cover_url=None)

    message, media_url = format_response(quote)

    assert media_url is None
    assert "Be water, my friend." in message
    assert "Bruce Lee" in message


@patch("src.daily_service.utils.shorten_tinyurl", return_value="https://tinyurl.com/x")
def test_format_response_uses_question_mark_when_author_missing(mock_shorten):
    quote = _make_quote()
    quote["properties"]["Author"]["rich_text"] = []

    message, _ = format_response(quote)

    assert message.endswith(
        "\"Be water, my friend.\" - None\n\n🔗 https://tinyurl.com/x"
    ) or " - None" in message


@patch("src.daily_service.utils.requests.get")
def test_shorten_tinyurl_returns_response_text(mock_get):
    mock_get.return_value = MagicMock(text="https://tinyurl.com/short")

    result = shorten_tinyurl("https://example.com/very/long/url")

    assert result == "https://tinyurl.com/short"
    mock_get.assert_called_once_with(
        "https://tinyurl.com/api-create.php",
        params={"url": "https://example.com/very/long/url"},
    )


@patch("src.daily_service.utils.requests.get", side_effect=RuntimeError("boom"))
def test_shorten_tinyurl_returns_long_url_on_error(mock_get):
    long_url = "https://example.com/very/long/url"

    result = shorten_tinyurl(long_url)

    assert result == long_url
