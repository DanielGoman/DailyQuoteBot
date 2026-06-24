from src.daily_service.utils import format_response


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


def test_format_response_happy_path():
    quote = _make_quote()

    message, media_url = format_response(quote)

    assert media_url == "https://example.com/img.png"
    assert "Be water, my friend." in message
    assert "Bruce Lee" in message
    # The trailing link is the raw Notion page URL (no shortener)
    assert "https://www.notion.so/Be-water-page-123" in message


def test_format_response_without_cover():
    quote = _make_quote(cover_url=None)

    message, media_url = format_response(quote)

    assert media_url is None
    assert "Be water, my friend." in message
    assert "Bruce Lee" in message
    assert "https://www.notion.so/Be-water-page-123" in message


def test_format_response_uses_question_mark_when_author_missing():
    quote = _make_quote()
    quote["properties"]["Author"]["rich_text"] = []

    message, _ = format_response(quote)

    assert message.endswith(
        "\"Be water, my friend.\" - None\n\n🔗 https://www.notion.so/Be-water-page-123"
    )
