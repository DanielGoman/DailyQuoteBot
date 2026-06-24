from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, call

from src.daily_service.whatsapp import (send_whatsapp, split_message,
                                        get_hours_since_last_inbound)
from src.daily_service.consts import Whatsapp


SID = "AC_test_sid"
TOKEN = "test_token"
FROM_NUMBER = "+14155238886"
TO_NUMBER = "+972500000000"
FROM_ = f"whatsapp:{FROM_NUMBER}"
TO = f"whatsapp:{TO_NUMBER}"


def test_split_message_short_returns_single_chunk():
    assert split_message("hello") == ["hello"]


def test_split_message_at_exact_limit_returns_single_chunk():
    msg = "a" * Whatsapp.TEXT_MESSAGE_LENGTH_LIMIT
    assert split_message(msg) == [msg]


def test_split_message_long_splits_with_ellipsis_suffix():
    limit = Whatsapp.TEXT_MESSAGE_LENGTH_LIMIT
    msg = "a" * (limit + 100)

    chunks = split_message(msg)

    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= limit
        assert chunk.endswith("...")


@patch("src.daily_service.whatsapp.Client")
def test_send_whatsapp_media_with_short_caption_sends_single_message(MockClient):
    client = MockClient.return_value
    msg = "short caption"
    media_url = "https://example.com/img.png"

    send_whatsapp(msg, media_url, SID, TOKEN, FROM_NUMBER, TO_NUMBER)

    MockClient.assert_called_once_with(SID, TOKEN)
    client.messages.create.assert_called_once_with(
        from_=FROM_, to=TO, body=msg, media_url=[media_url]
    )


@patch("src.daily_service.whatsapp.Client")
def test_send_whatsapp_media_with_long_caption_sends_image_then_text(MockClient):
    client = MockClient.return_value
    media_url = "https://example.com/img.png"
    msg = "x" * (Whatsapp.IMAGE_CAPTION_TEXT_LENGTH_LIMIT + 1)

    send_whatsapp(msg, media_url, SID, TOKEN, FROM_NUMBER, TO_NUMBER)

    calls = client.messages.create.call_args_list
    assert calls[0] == call(from_=FROM_, to=TO, media_url=[media_url])
    assert len(calls) >= 2
    for c in calls[1:]:
        assert "body" in c.kwargs
        assert "media_url" not in c.kwargs


@patch("src.daily_service.whatsapp.Client")
def test_send_whatsapp_text_only_sends_chunks(MockClient):
    client = MockClient.return_value
    msg = "y" * (Whatsapp.TEXT_MESSAGE_LENGTH_LIMIT + 10)

    send_whatsapp(msg, None, SID, TOKEN, FROM_NUMBER, TO_NUMBER)

    calls = client.messages.create.call_args_list
    assert len(calls) >= 2
    for c in calls:
        assert c.kwargs["from_"] == FROM_
        assert c.kwargs["to"] == TO
        assert "body" in c.kwargs
        assert "media_url" not in c.kwargs


@patch("src.daily_service.whatsapp.Client")
def test_send_whatsapp_text_only_short_sends_single_message(MockClient):
    client = MockClient.return_value
    msg = "hi"

    send_whatsapp(msg, None, SID, TOKEN, FROM_NUMBER, TO_NUMBER)

    client.messages.create.assert_called_once_with(from_=FROM_, to=TO, body="hi")


@patch("src.daily_service.whatsapp.Client")
def test_send_whatsapp_swallows_twilio_errors(MockClient, capsys):
    client = MockClient.return_value
    client.messages.create.side_effect = RuntimeError("twilio down")

    send_whatsapp("hi", None, SID, TOKEN, FROM_NUMBER, TO_NUMBER)

    captured = capsys.readouterr()
    assert "Failed to send message" in captured.out


@patch("src.daily_service.whatsapp.Client")
def test_get_hours_since_last_inbound_computes_age(MockClient):
    client = MockClient.return_value
    sent = datetime.now(timezone.utc) - timedelta(hours=50)
    client.messages.list.return_value = [MagicMock(date_sent=sent, date_created=sent)]

    hours = get_hours_since_last_inbound(SID, TOKEN, FROM_NUMBER, TO_NUMBER)

    assert hours is not None
    assert 49.9 < hours < 50.1
    # Inbound query swaps from_/to: recipient -> our sandbox number
    client.messages.list.assert_called_once_with(from_=TO, to=FROM_, limit=1)


@patch("src.daily_service.whatsapp.Client")
def test_get_hours_since_last_inbound_handles_naive_timestamp(MockClient):
    client = MockClient.return_value
    naive_sent = datetime.utcnow() - timedelta(hours=10)
    client.messages.list.return_value = [MagicMock(date_sent=naive_sent, date_created=naive_sent)]

    hours = get_hours_since_last_inbound(SID, TOKEN, FROM_NUMBER, TO_NUMBER)

    assert hours is not None
    assert 9.9 < hours < 10.1


@patch("src.daily_service.whatsapp.Client")
def test_get_hours_since_last_inbound_returns_none_when_no_messages(MockClient):
    client = MockClient.return_value
    client.messages.list.return_value = []

    assert get_hours_since_last_inbound(SID, TOKEN, FROM_NUMBER, TO_NUMBER) is None
