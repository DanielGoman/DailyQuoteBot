from twilio.rest import Client

from src.daily_service.consts import Whatsapp


def send_whatsapp(msg: str, media_url: str | None, account_sid: str, auth_token: str,
                  from_number: str, to_number: str) -> None:
    client = Client(account_sid, auth_token)
    from_ = f"whatsapp:{from_number}"
    to = f"whatsapp:{to_number}"

    try:
        if media_url and len(msg) <= Whatsapp.IMAGE_CAPTION_TEXT_LENGTH_LIMIT:
            client.messages.create(from_=from_, to=to, body=msg, media_url=[media_url])
        elif media_url:
            client.messages.create(from_=from_, to=to, media_url=[media_url])
            for chunk in split_message(msg):
                client.messages.create(from_=from_, to=to, body=chunk)
        else:
            for chunk in split_message(msg):
                client.messages.create(from_=from_, to=to, body=chunk)
        print("Message sent successfully!")
    except Exception as e:
        print(f"Failed to send message: {e}")


def split_message(message: str) -> list[str]:
    limit = Whatsapp.TEXT_MESSAGE_LENGTH_LIMIT
    if len(message) <= limit:
        return [message]
    return [message[i:i + limit - 3] + "..."
            for i in range(0, len(message), limit - 3)]
