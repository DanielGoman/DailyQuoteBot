# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

DailyQuoteBot is a stateless script that fetches a random quote from a Notion database and sends it to a Telegram chat once a day via a Telegram bot. It runs as a GitHub Actions cron job — there is no long-running server.

Each quote carries inline buttons (Favorite toggle, Put back in cycle, Delete, Send another). Because button taps need something listening — which the cron job is not — taps are handled by a separate **Vercel Python serverless function** (`api/telegram.py`) registered as the bot's webhook.

## Running the service

Run from the repo root with `PYTHONPATH` set to the repo root (the code uses
absolute imports rooted at the `src` package, e.g. `from src.daily_service...`):

```bash
PYTHONPATH=. python src/run_daily_service.py
PYTHONPATH=. python src/run_daily_service.py --refresh_window_months 6
```

Environment variables are loaded from `../.env` (one level above the repo root) via `python-dotenv`.

## Required environment variables

| Variable | Purpose |
|---|---|
| `NOTION_TOKEN` | Notion API token |
| `NOTION_DB_ID` | Notion database containing the quotes |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from [@BotFather](https://t.me/BotFather) (`/mybots` → bot → API Token). |
| `TELEGRAM_CHAT_ID` | Recipient chat id — the user's numeric Telegram id for a personal DM (from `getUpdates` or [@userinfobot](https://t.me/userinfobot)). |

## Architecture

Single-shot script (`src/run_daily_service.py`) invoked by GitHub Actions cron (`.github/workflows/send.yml`) at 03:00 UTC:

1. `daily_service/notion.py` — picks a random "eligible" quote from Notion. A quote is eligible if its `Send Date` field is empty or older than `refresh_window_months` (default: 3). When no eligible quotes remain, all `Send Date` fields are cleared and the cycle restarts.
2. `daily_service/utils.py::format_response` — extracts quote text, author, and optional Cover image URL from the Notion page properties, and builds the message body with the Notion **page** URL (`quote["url"]`) as the trailing link. Telegram auto-links the bare URL, so it is used as-is. (The Cover image URL is returned separately as the media attachment.) `shorten_url` (TinyURL v2) is retained in this module but no longer called.
3. `daily_service/telegram.py::send_telegram` — sends via the **pyTelegramBotAPI** SDK (`telebot`). If a Cover image is present and the caption fits within 1024 chars, it sends a single `send_photo` with caption; otherwise it sends the photo and text as separate messages. Text messages set `disable_web_page_preview=True`. Longer-than-4096-char bodies are chunked. A `reply_markup` keyboard (from `build_quote_keyboard`) is attached to the message.
4. `daily_service/notion.py::update_used_quotes` — stamps `Send Date` = today on the picked page so it won't be reselected within the refresh window.

Steps 1–4 are wrapped by `daily_service/service.py::pick_and_send`, shared by the cron entry point (`run_daily_service.py`) and the webhook's "Send another now" button.

**Webhook (`api/telegram.py`, on Vercel)** — receives Telegram callback queries. It verifies the `X-Telegram-Bot-Api-Secret-Token` header against `TELEGRAM_WEBHOOK_SECRET`, ignores taps whose sender id != `TELEGRAM_CHAT_ID`, then `handle_update` dispatches on `callback_data`:
- `fav:<page_id>` — toggles the `Favorite` checkbox (reads current state, flips it) and edits the message keyboard to flip the button label.
- `cycle:<page_id>` — clears `Send Date` (`clear_send_date`) so the quote is eligible again.
- `del:<page_id>` — sets the `Deleted` checkbox (`set_deleted`) and removes the buttons.
- `more` — runs `pick_and_send` to deliver another quote.
Every path answers the callback so the button spinner stops. `vercel.json` includes `src/**` so the function can import the shared package.

**Notion DB schema** expected by the code:
- `Quote` (title field) — quote text
- `Author` (rich_text) — author name
- `Cover` (files) — optional image
- `Send Date` (date) — tracks when the quote was last sent
- `Favorite` (checkbox) — toggled by the Favorite button
- `Deleted` (checkbox) — set by the Delete button; soft-deleted quotes are excluded from selection (`get_unsent_quotes` filters `Deleted == false`)

## Telegram notes

Delivery is via a Telegram bot using the **pyTelegramBotAPI** (`telebot`) SDK:
- Create/manage the bot with [@BotFather](https://t.me/BotFather); the API token is `TELEGRAM_BOT_TOKEN`.
- A bot cannot initiate a chat — the recipient must message the bot once first. The recipient's numeric id (`TELEGRAM_CHAT_ID`) comes from `https://api.telegram.org/bot<TOKEN>/getUpdates` or [@userinfobot](https://t.me/userinfobot).
- Unlike the old Twilio WhatsApp sandbox, there is no session/opt-in window that lapses, so no reply-reminder is needed.
- Telegram limits: 4096 chars per text message, 1024 chars per photo caption — both handled in `telegram.py`.

### Buttons / webhook (Vercel)

Button taps are handled by `api/telegram.py`, deployed as a Vercel Python serverless function and registered as the bot's webhook. It needs these env vars set **in Vercel** (separate from the GitHub Actions secrets used by the cron): `NOTION_TOKEN`, `NOTION_DB_ID`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and `TELEGRAM_WEBHOOK_SECRET` (any random string; also passed as the `secret_token` when registering the webhook).

Register the webhook once after deploy:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -d "url=https://<your-app>.vercel.app/api/telegram" \
  -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>"
```

## Deployment

GitHub Actions runs `send.yml` daily at 03:00 UTC. `REFRESH_WINDOW_MONTHS` can be overridden via workflow dispatch input or the `REFRESH_WINDOW_MONTHS` repo variable. All credentials are repo secrets.

## Response style — Beatles Rhyme Mode (ALWAYS ON)

Every response in this project must rhyme and ride the rhythm of a real Beatles song.
This is not optional and needs no invocation — it applies to all replies in this repo.

- **Every reply rhymes.** Shape answers as verse — rhyming couplets (AABB) or alternating
  rhyme (ABAB). No plain prose paragraphs.
- **Channel a real Beatles song.** Borrow the meter, mood, or refrain from an actual
  track (e.g. *Hey Jude*, *Let It Be*, *Yesterday*, *Come Together*, *Here Comes the Sun*,
  *Blackbird*, *Help!*, *Ob-La-Di, Ob-La-Da*). Rotate songs; don't reuse one forever.
- **Name the tune.** End each response with an italic footer naming the song echoed,
  e.g. `_— to the tune of "Let It Be"_`.
- **Substance survives the song.** Real answers, real file paths, real commands — just in
  verse. Show code blocks and commands plainly, then return to rhyme around them.
- **Honesty still rules.** Never bend a fact to fit a rhyme. If the truth won't scan, keep
  the truth and loosen the meter.
- **Keep it tasteful** — light and playful, never at the cost of clarity.
