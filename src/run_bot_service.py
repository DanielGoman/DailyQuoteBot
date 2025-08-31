import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler


from src.bot_service.telegram_bot import get_telegram_bot


# Environment variables
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']


def main():
    # Create the bot app
    bot_app = get_telegram_bot(TELEGRAM_BOT_TOKEN)

    print("Starting Telegram Bot")
    # Run the bot (blocking)
    bot_app.run_polling()


# --- Minimal dummy server ---
def run_server():
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    print(f"Listening on port {port}")
    server.serve_forever()


# ---------------- Run ----------------
if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    main()