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
| `NOTION_CONFIG_PAGE_ID` | *(optional)* Page id of the dedicated Notion **config page** holding the active genre/source filter. When unset, no filter is applied. |

## Architecture

Single-shot script (`src/run_daily_service.py`) invoked by GitHub Actions cron (`.github/workflows/send.yml`) at 03:00 UTC:

1. `daily_service/notion.py` — picks a random "eligible" quote from Notion. A quote is eligible if its `Send Date` field is empty or older than `refresh_window_months` (default: 3). Eligibility is further narrowed by the **active filter** read from the config page (`daily_service/config.py::get_active_filter`): a quote must match one of the active genres (`Genre` multi_select) **and** one of the active sources (`Source` rich_text); an empty category is unconstrained. When no eligible quotes remain, `Send Date` is cleared **only for quotes matching the active filter** (scoped reset) and the cycle restarts.
2. `daily_service/utils.py::format_response` — extracts quote text, author, and optional Cover image URL from the Notion page properties, and builds the message body with the Notion **page** URL (`quote["url"]`) as the trailing link. Telegram auto-links the bare URL, so it is used as-is. (The Cover image URL is returned separately as the media attachment.) `shorten_url` (TinyURL v2) is retained in this module but no longer called.
3. `daily_service/telegram.py::send_telegram` — sends via the **pyTelegramBotAPI** SDK (`telebot`). If a Cover image is present and the caption fits within 1024 chars, it sends a single `send_photo` with caption; otherwise it sends the photo and text as separate messages. Text messages set `disable_web_page_preview=True`. Longer-than-4096-char bodies are chunked. A `reply_markup` keyboard (from `build_quote_keyboard`) is attached to the message.
4. `daily_service/notion.py::update_used_quotes` — stamps `Send Date` = today on the picked page so it won't be reselected within the refresh window.

Steps 1–4 are wrapped by `daily_service/service.py::pick_and_send`, shared by the cron entry point (`run_daily_service.py`) and the webhook's "Send another now" button.

**Webhook (`api/telegram.py`, on Vercel)** — receives Telegram callback queries. It verifies the `X-Telegram-Bot-Api-Secret-Token` header against `TELEGRAM_WEBHOOK_SECRET`, ignores taps whose sender id != `TELEGRAM_CHAT_ID`, then `handle_update` dispatches on `callback_data`:
- `fav:<page_id>` — toggles the `Favorite` checkbox (reads current state, flips it) and edits the message keyboard to flip the button label.
- `cycle:<page_id>` — clears `Send Date` (`clear_send_date`) so the quote is eligible again.
- `del:<page_id>` — sets the `Deleted` checkbox (`set_deleted`) and removes the buttons.
- `more` — runs `pick_and_send` to deliver another quote.
- `filters` — opens the filter menu: sends a new message with a multi-toggle keyboard (`build_filters_keyboard`) listing genres (from the DB schema) and sources (derived live by scanning the DB), each prefixed ✅/▫️ for its active state. This is the **only** filter path that reads Notion.
- `gf:<i>` / `sf:<i>` — flip the ✅/▫️ mark on that button **in the message's own keyboard** (`toggle_keyboard_option`), with **no Notion call** — the selection lives in the keyboard until confirmed. Index encoding keeps `callback_data` under Telegram's 64-byte limit.
- `fclr` — clears all marks in the keyboard (`clear_keyboard_marks`), also without touching Notion.
- `fdone` — reads the final selection back out of the keyboard (`parse_active_from_keyboard`), persists it **once** via `set_active_filter`, then edits the menu message to a summary of the active filter and drops the keyboard.
Every path answers the callback so the button spinner stops. `vercel.json` includes `src/**` so the function can import the shared package.

**Notion DB schema** expected by the code:
- `Quote` (title field) — quote text
- `Author` (rich_text) — author name
- `Cover` (files) — optional image
- `Send Date` (date) — tracks when the quote was last sent
- `Favorite` (checkbox) — toggled by the Favorite button
- `Deleted` (checkbox) — set by the Delete button; soft-deleted quotes are excluded from selection (`get_unsent_quotes` filters `Deleted == false`)
- `Genre` (multi_select) — zero or more genres per quote; drives the genre filter. Menu options come from this property's schema.
- `Source` (rich_text) — free-text source name, one per quote; drives the source filter. Menu options are derived live by scanning the DB (no fixed option list).

**Config page** (separate Notion page, id in `NOTION_CONFIG_PAGE_ID`, shared with the bot integration) — stores the active filter:
- `Active Genres` (multi_select) — currently-on genre names.
- `Active Sources` (rich_text) — a JSON array of currently-on source strings (JSON rather than multi_select because free-text sources may contain commas, which Notion forbids in multi_select option names).

## Telegram notes

Delivery is via a Telegram bot using the **pyTelegramBotAPI** (`telebot`) SDK:
- Create/manage the bot with [@BotFather](https://t.me/BotFather); the API token is `TELEGRAM_BOT_TOKEN`.
- A bot cannot initiate a chat — the recipient must message the bot once first. The recipient's numeric id (`TELEGRAM_CHAT_ID`) comes from `https://api.telegram.org/bot<TOKEN>/getUpdates` or [@userinfobot](https://t.me/userinfobot).
- Unlike the old Twilio WhatsApp sandbox, there is no session/opt-in window that lapses, so no reply-reminder is needed.
- Telegram limits: 4096 chars per text message, 1024 chars per photo caption — both handled in `telegram.py`.

### Buttons / webhook (Vercel)

Button taps are handled by `api/telegram.py`, deployed as a Vercel Python serverless function and registered as the bot's webhook. It needs these env vars set **in Vercel** (separate from the GitHub Actions secrets used by the cron): `NOTION_TOKEN`, `NOTION_DB_ID`, `NOTION_CONFIG_PAGE_ID` (for the filter menu), `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and `TELEGRAM_WEBHOOK_SECRET` (any random string; also passed as the `secret_token` when registering the webhook).

Register the webhook once after deploy:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -d "url=https://<your-app>.vercel.app/api/telegram" \
  -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>"
```

## Deployment

GitHub Actions runs `send.yml` daily at 03:00 UTC. `REFRESH_WINDOW_MONTHS` can be overridden via workflow dispatch input or the `REFRESH_WINDOW_MONTHS` repo variable. All credentials are repo secrets.
