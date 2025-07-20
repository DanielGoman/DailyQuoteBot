import os
import random
import requests

from twilio.rest import Client


# Environment variables
NOTION_TOKEN = os.environ['NOTION_TOKEN']
NOTION_DB_ID = os.environ['NOTION_DB_ID']
TWILIO_SID = os.environ['TWILIO_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
WHATSAPP_FROM = os.environ['WHATSAPP_FROM']
WHATSAPP_TO = os.environ['WHATSAPP_TO']


def main() -> None:
    sentences = get_sentences()
    if sentences:
        selected_quote = random.choice(sentences)
        message = (f"📜 Your daily quote:\n\n"
                   f"\"{selected_quote['title']}\" - {selected_quote.get('author', '?')}\n\n"
                   f"🔗 {selected_quote['url']}")
        send_whatsapp(msg=message, media_url=selected_quote['media_url'])
    else:
        send_whatsapp("⚠️ No sentences found in Notion.")


def get_sentences() -> list[dict[str, str]]:
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers)
    data = response.json()
    results = data.get("results", [])

    sentences = []
    for item in results:
        title_text, media_url, author_name = None, None, None
        try:
            props = item.get("properties", {})

            # Get quote text
            quote_prop = props.get("Quote", {})
            quote_rich_text = quote_prop.get("title", [])
            if quote_rich_text and isinstance(quote_rich_text, list):
                title_text = quote_rich_text[0].get("text", {}).get("content")

            # Get author name
            author_prop = props.get("Author", {})
            author_rich_text = author_prop.get("rich_text", [])
            if author_rich_text and isinstance(author_rich_text, list):
                author_name = author_rich_text[0].get("text", {}).get("content", "")

            # Get cover
            cover_prop = props.get("Cover", {})
            files = cover_prop.get("files", [])
            if files and "file" in files[0]:
                media_url = files[0].get("file", {}).get("url")

        except KeyError:
            continue

        if title_text:
            sentences.append({
                'title': title_text,
                'author': author_name,
                'media_url': media_url,
                'url': shorten_tinyurl(item['url'])
            })

    return sentences


def shorten_tinyurl(long_url: str) -> str:
    try:
        response = requests.get("https://tinyurl.com/api-create.php", params={"url": long_url})
        return response.text
    except Exception as e:
        print(f"TinyURL error: {e}")
        return long_url


def send_whatsapp(msg: str, media_url: str = None) -> None:
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    res = client.messages.create(
        from_=WHATSAPP_FROM,
        to=WHATSAPP_TO,
        body=msg,
        media_url=[media_url] if media_url else None
    )
    print(f"Status: {res.status}")


if __name__ == "__main__":
    main()
