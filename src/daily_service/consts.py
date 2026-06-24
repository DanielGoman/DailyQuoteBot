
class Whatsapp:
    IMAGE_CAPTION_TEXT_LENGTH_LIMIT = 1024
    TEXT_MESSAGE_LENGTH_LIMIT = 4096

DEFAULT_REFRESH_WINDOW_MONTHS = 3

# Remind the recipient to reply if they haven't sent an inbound message in this
# many hours, so the Twilio WhatsApp sandbox opt-in (which lapses after 72h of
# recipient inactivity) stays alive. Keep this safely below 72.
INBOUND_REMINDER_THRESHOLD_HOURS = 48

REMINDER_MESSAGE = (
    "👋 Reminder: reply to this chat (even just \"hi\") to keep your daily "
    "quotes coming. The WhatsApp sandbox stops delivering after 72h without a "
    "reply from you."
)
