import random
import datetime

from notion_client import Client
from dateutil.relativedelta import relativedelta



def get_next_quote(notion_client: Client, notion_db_id: str, refresh_window_months: int) -> dict:
    unsent_quotes = get_unsent_quotes(notion_client, notion_db_id, refresh_window_months)
    if not unsent_quotes:
        reset_quotes_tracker(notion_client, notion_db_id)
        unsent_quotes = get_unsent_quotes(notion_client, notion_db_id, refresh_window_months)

    selected_quote = random.choice(unsent_quotes)

    return selected_quote


def get_unsent_quotes(notion_client: Client, notion_db_id: str, refresh_window_months: int) -> list[dict[str, str]]:
    before_date = datetime.date.today() - relativedelta(months=refresh_window_months)
    response = notion_client.databases.query(
        database_id=notion_db_id,
        filter={
            "or": [
                {
                    "property": "Send Date",
                    "date": {
                        "before": before_date.isoformat()
                    }
                },
                {
                    "property": "Send Date",
                    "date": {
                        "is_empty": True
                    }
                }
            ]
        }
    )

    return response['results']


def reset_quotes_tracker(notion_client: Client, notion_db_id: str) -> None:
    response = notion_client.databases.query(database_id=notion_db_id)
    all_quotes = response["results"]

    for quote_page in all_quotes:
        notion_client.pages.update(
            page_id=quote_page["id"],
            properties={
                "Send Date": {
                    "checkbox": None
                }
            }
        )


def update_used_quotes(notion_client: Client, quote: dict) -> None:
    notion_client.pages.update(
        page_id=quote['id'],
        properties={
            "Send Date": {
                "date": {
                    "start": datetime.date.today().isoformat()
                }
            }
        }
    )
