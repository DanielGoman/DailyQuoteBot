import html

import requests

TINYURL_CREATE_ENDPOINT = "https://api.tinyurl.com/create"


def shorten_url(long_url: str, api_token: str | None) -> str:
    """Shorten a URL via TinyURL's v2 API. Falls back to the original URL if
    no token is configured or the request fails."""
    if not long_url or not api_token:
        return long_url
    try:
        response = requests.post(
            TINYURL_CREATE_ENDPOINT,
            headers={"Authorization": f"Bearer {api_token}"},
            json={"url": long_url},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["data"]["tiny_url"]
    except Exception as e:
        print(f"TinyURL error: {e}")
        return long_url


def format_response(quote: dict) -> tuple[str, str]:
    title_text, media_url, author_name = None, None, None
    try:
        page_url = quote.get("url")
        props = quote.get("properties", {})

        # Get quote text
        quote_prop = props.get("Quote", {})
        quote_rich_text = quote_prop.get("title", [])
        if quote_rich_text and isinstance(quote_rich_text, list):
            title_text = quote_rich_text[0].get("text", {}).get("content", "")

        # Get author name
        author_prop = props.get("Author", {})
        author_rich_text = author_prop.get("rich_text", [])
        if author_rich_text and isinstance(author_rich_text, list):
            author_name = author_rich_text[0].get("text", {}).get("content", "?")

        # Get cover
        cover_prop = props.get("Cover", {})
        files = cover_prop.get("files", [])
        if files and "file" in files[0]:
            media_url = files[0].get("file", {}).get("url", "")
    except KeyError as e:
        print(f"Error while parsing select quote with page_id: {quote['id']}, with error:", e)
        message = "❌ Error"
    else:
        # HTML parse mode: escape user-derived text and hide the long Notion URL
        # behind a short hyperlink ("View on Notion").
        message = (f"📜 Your daily quote:\n\n"
                   f"\"{html.escape(title_text)}\" - {html.escape(author_name)}\n\n"
                   f"🔗 <a href=\"{html.escape(page_url, quote=True)}\">View on Notion</a>")

    return message, media_url
