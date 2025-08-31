import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler


from src.bot_service.telegram_bot import get_telegram_bot

# Environment variables
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
PORT = int(os.environ['PORT'])
WEBHOOK_URL = os.environ['WEBHOOK_URL']
WEBHOOK_PATH = f"/{TELEGRAM_BOT_TOKEN}"



def main():
    # Create the bot app
    bot_app = get_telegram_bot(TELEGRAM_BOT_TOKEN)

    print("Starting Telegram Bot")
    # TODO: replace Polling with Webhook, this polling is blocking AF and is causing problems on render

    # Start webhook server
    print(f"Starting webhook on port {PORT} at path {WEBHOOK_PATH}")
    bot_app.run_webhook(
        listen="localhost",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=f"{WEBHOOK_URL}{WEBHOOK_PATH}"
    )


# --- Minimal dummy server ---
def run_server():
    port = int(os.environ.get("PORT", 6000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    print(f"Listening on port {port}")
    server.serve_forever()


# ---------------- Run ----------------
if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    main()
