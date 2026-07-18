import random
import datetime

from notion_client import Client
from dateutil.relativedelta import relativedelta

from src.daily_service.consts import Prop


def get_next_quote(notion_client: Client, notion_db_id: str, refresh_window_months: int,
                   active_genres: list[str] | None = None,
                   active_sources: list[str] | None = None) -> dict:
    active_genres = active_genres or []
    active_sources = active_sources or []
    unsent_quotes = get_unsent_quotes(notion_client, notion_db_id, refresh_window_months,
                                      active_genres, active_sources)
    if not unsent_quotes:
        reset_quotes_tracker(notion_client, notion_db_id, active_genres, active_sources)
        unsent_quotes = get_unsent_quotes(notion_client, notion_db_id, refresh_window_months,
                                          active_genres, active_sources)

    if not unsent_quotes:
        return {}

    selected_quote = random.choice(unsent_quotes)

    return selected_quote


def _filter_blocks(active_genres: list[str], active_sources: list[str]) -> list[dict]:
    """The genre/source clauses shared by the query and the reset. Within each
    category it's OR (any active value); the caller AND's the blocks together, so
    across categories it's AND. Empty categories contribute nothing (unconstrained)."""
    blocks: list[dict] = []
    if active_genres:
        blocks.append({"or": [
            {"property": Prop.GENRE, "multi_select": {"contains": g}}
            for g in active_genres
        ]})
    if active_sources:
        blocks.append({"or": [
            {"property": Prop.SOURCE, "rich_text": {"equals": s}}
            for s in active_sources
        ]})
    return blocks


def get_unsent_quotes(notion_client: Client, notion_db_id: str, refresh_window_months: int,
                      active_genres: list[str] | None = None,
                      active_sources: list[str] | None = None) -> list[dict[str, str]]:
    active_genres = active_genres or []
    active_sources = active_sources or []
    before_date = datetime.date.today() - relativedelta(months=refresh_window_months)
    conditions = [
        {
            "or": [
                {"property": Prop.SEND_DATE, "date": {"before": before_date.isoformat()}},
                {"property": Prop.SEND_DATE, "date": {"is_empty": True}},
            ]
        },
        {"property": Prop.DELETED, "checkbox": {"equals": False}},
    ]
    conditions.extend(_filter_blocks(active_genres, active_sources))

    response = notion_client.databases.query(
        database_id=notion_db_id,
        filter={"and": conditions},
    )

    return response['results']


def reset_quotes_tracker(notion_client: Client, notion_db_id: str,
                         active_genres: list[str] | None = None,
                         active_sources: list[str] | None = None) -> None:
    """Clear Send Date so the cycle restarts — scoped to the active filter, so
    quotes outside the current filter keep their Send Date untouched."""
    active_genres = active_genres or []
    active_sources = active_sources or []
    conditions = [{"property": Prop.DELETED, "checkbox": {"equals": False}}]
    conditions.extend(_filter_blocks(active_genres, active_sources))

    response = notion_client.databases.query(
        database_id=notion_db_id,
        filter={"and": conditions},
    )

    for quote_page in response["results"]:
        notion_client.pages.update(
            page_id=quote_page["id"],
            properties={Prop.SEND_DATE: {"date": None}},
        )


def update_used_quotes(notion_client: Client, quote: dict) -> None:
    notion_client.pages.update(
        page_id=quote['id'],
        properties={
            Prop.SEND_DATE: {
                "date": {
                    "start": datetime.date.today().isoformat()
                }
            }
        }
    )


def get_favorite(notion_client: Client, page_id: str) -> bool:
    page = notion_client.pages.retrieve(page_id=page_id)
    return bool(page.get("properties", {}).get(Prop.FAVORITE, {}).get("checkbox", False))


def set_favorite(notion_client: Client, page_id: str, value: bool) -> None:
    notion_client.pages.update(
        page_id=page_id,
        properties={Prop.FAVORITE: {"checkbox": value}}
    )


def clear_send_date(notion_client: Client, page_id: str) -> None:
    notion_client.pages.update(
        page_id=page_id,
        properties={Prop.SEND_DATE: {"date": None}}
    )


def set_deleted(notion_client: Client, page_id: str, value: bool = True) -> None:
    notion_client.pages.update(
        page_id=page_id,
        properties={Prop.DELETED: {"checkbox": value}}
    )
