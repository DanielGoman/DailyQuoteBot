"""Active-filter state (persisted on a dedicated Notion config page) and the
menu vocabulary (genres/sources the user can pick from).

The filter has to survive between the stateless halves of the system — the daily
cron and the per-tap webhook — so it lives in Notion rather than in memory. Genre
options come from the Quotes DB schema (a controlled multi_select); source options
are derived live by scanning the DB, since Source is free text with no fixed list.
"""
import json

from notion_client import Client

from src.daily_service.consts import Prop


def get_active_filter(notion_client: Client, config_page_id: str) -> tuple[list[str], list[str]]:
    """Return (active_genres, active_sources) from the config page. Missing or
    malformed values degrade to empty lists (i.e. no filter)."""
    page = notion_client.pages.retrieve(page_id=config_page_id)
    props = page.get("properties", {})

    genres = [opt.get("name", "")
              for opt in props.get(Prop.ACTIVE_GENRES, {}).get("multi_select", [])]

    sources_raw = _rich_text_plain(props.get(Prop.ACTIVE_SOURCES, {}).get("rich_text", []))
    try:
        sources = json.loads(sources_raw) if sources_raw else []
        if not isinstance(sources, list):
            sources = []
    except (ValueError, TypeError):
        sources = []

    return [g for g in genres if g], [s for s in sources if s]


def set_active_filter(notion_client: Client, config_page_id: str,
                      genres: list[str], sources: list[str]) -> None:
    """Persist both categories back to the config page."""
    notion_client.pages.update(
        page_id=config_page_id,
        properties={
            Prop.ACTIVE_GENRES: {"multi_select": [{"name": g} for g in genres]},
            Prop.ACTIVE_SOURCES: {
                "rich_text": [{"text": {"content": json.dumps(sources)}}]
            },
        },
    )


def list_genre_options(notion_client: Client, notion_db_id: str) -> list[str]:
    """Every genre in the Quotes DB schema — no page scan needed."""
    db = notion_client.databases.retrieve(database_id=notion_db_id)
    genre_prop = db.get("properties", {}).get(Prop.GENRE, {}).get("multi_select", {})
    return [opt.get("name", "") for opt in genre_prop.get("options", []) if opt.get("name")]


def list_source_values(notion_client: Client, notion_db_id: str) -> list[str]:
    """Distinct Source strings across all pages, sorted for a stable index.

    Source is free text, so there is no schema option list — we scan the DB. This
    runs only when the filter menu is opened, never on the daily send.
    """
    seen: set[str] = set()
    cursor = None
    while True:
        kwargs = {"database_id": notion_db_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        response = notion_client.databases.query(**kwargs)
        for page in response["results"]:
            value = _rich_text_plain(
                page.get("properties", {}).get(Prop.SOURCE, {}).get("rich_text", []))
            if value:
                seen.add(value)
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return sorted(seen, key=str.casefold)


def _rich_text_plain(rich_text: list) -> str:
    """Concatenate a Notion rich_text array into a plain string."""
    return "".join(part.get("plain_text", part.get("text", {}).get("content", ""))
                   for part in rich_text).strip()
