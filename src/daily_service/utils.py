import requests


def shorten_tinyurl(long_url: str) -> str:
    try:
        response = requests.get("https://tinyurl.com/api-create.php", params={"url": long_url})
        return response.text
    except Exception as e:
        print(f"TinyURL error: {e}")
        return long_url


def format_response(quote: dict) -> tuple[str, str, str]:
    title_text, media_url, author_name = None, None, None
    try:
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
        shortened_url = shorten_tinyurl(media_url)
        message = (f"📜 Your daily quote:\n\n"
                   f"\"{title_text}\" - {author_name}\n\n"
                   f"🔗 {shortened_url}")

    return message, media_url, quote['id']