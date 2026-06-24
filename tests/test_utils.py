from unittest.mock import patch, MagicMock

from src.daily_service.utils import format_response, shorten_url


def _make_quote(quote_text="Be water, my friend.",
                author="Bruce Lee",
                cover_url="https://example.com/img.png",
                page_id="page-123",
                page_url="https://www.notion.so/Be-water-page-123"):
    properties = {
        "Quote": {"title": [{"text": {"content": quote_text}}]},
        "Author": {"rich_text": [{"text": {"content": author}}]},
    }
    if cover_url is not None:
        properties["Cover"] = {"files": [{"file": {"url": cover_url}}]}
    else:
        properties["Cover"] = {"files": []}
    return {"id": page_id, "url": page_url, "properties": properties}


def test_format_response_without_token_uses_full_url():
    quote = _make_quote()

    message, media_url = format_response(quote)

    assert media_url == "https://example.com/img.png"
    assert "Be water, my friend." in message
    assert "Bruce Lee" in message
    # No token -> the raw Notion page URL is used
    assert "https://www.notion.so/Be-water-page-123" in message


@patch("src.daily_service.utils.shorten_url", return_value="https://tinyurl.com/abc")
def test_format_response_with_token_uses_shortened_url(mock_shorten):
    quote = _make_quote()

    message, _ = format_response(quote, tinyurl_token="tok-123")

    assert "https://tinyurl.com/abc" in message
    assert "https://www.notion.so/Be-water-page-123" not in message
    mock_shorten.assert_called_once_with(
        "https://www.notion.so/Be-water-page-123", "tok-123"
    )


def test_format_response_without_cover():
    quote = _make_quote(cover_url=None)

    message, media_url = format_response(quote)

    assert media_url is None
    assert "Be water, my friend." in message
    assert "Bruce Lee" in message


def test_shorten_url_returns_original_when_no_token():
    url = "https://www.notion.so/page"
    assert shorten_url(url, None) == url


@patch("src.daily_service.utils.requests.post")
def test_shorten_url_returns_tiny_url_on_success(mock_post):
    mock_post.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"data": {"tiny_url": "https://tinyurl.com/xyz"}}),
    )

    result = shorten_url("https://www.notion.so/page", "tok-123")

    assert result == "https://tinyurl.com/xyz"
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.tinyurl.com/create"
    assert kwargs["headers"]["Authorization"] == "Bearer tok-123"
    assert kwargs["json"] == {"url": "https://www.notion.so/page"}


@patch("src.daily_service.utils.requests.post", side_effect=RuntimeError("boom"))
def test_shorten_url_falls_back_to_original_on_error(mock_post):
    url = "https://www.notion.so/page"

    assert shorten_url(url, "tok-123") == url
