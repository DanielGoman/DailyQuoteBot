import os

import requests
import random
from dotenv import load_dotenv


load_dotenv()

# Environment variables
NOTION_TOKEN = os.environ['NOTION_TOKEN']
NOTION_DB_ID = os.environ['NOTION_DB_ID']
TWILIO_SID = os.environ['TWILIO_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
WHATSAPP_FROM = os.environ['WHATSAPP_FROM']
WHATSAPP_TO = os.environ['WHATSAPP_TO']


def main():
    sentences = get_sentences()
    if sentences:
        selected_quote = random.choice(sentences)
        message = (f"📜 Your daily quote:\n\n"
                   f"\"{selected_quote['title']}\" - {selected_quote.get('author', '?')}\n\n"
                   f"🔗 {selected_quote['url']}")
        send_whatsapp(message)

    else:
        send_whatsapp("⚠️ No sentences found in Notion.")


def get_sentences():
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
        title_text = None
        try:
            quote_title = item['properties']['Quote']['title']
            if quote_title and isinstance(quote_title, list):
                title_text = quote_title[0]['plain_text']

            quote_author = item['properties']['Author']['rich_text']
            if quote_author and isinstance(quote_author, list):
                author_name = quote_author[0]['text']['content']
            else:
                author_name = ""

        except KeyError:
            continue

        if title_text:
            sentences.append({
                'title': title_text,
                'author': author_name,
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


def send_whatsapp(msg: str):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    data = {
        "From": WHATSAPP_FROM,
        "To": WHATSAPP_TO,
        "Body": msg
    }
    response = requests.post(url, data=data, auth=(TWILIO_SID, TWILIO_AUTH_TOKEN))
    print(f"Sent: {response.status_code} - {response.text}")


if __name__ == "__main__":
    main()
