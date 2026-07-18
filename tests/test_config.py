import json
from unittest.mock import MagicMock

from src.daily_service.config import (
    get_active_filter,
    set_active_filter,
    toggle_genre,
    toggle_source,
    clear_filter,
    list_genre_options,
    list_source_values,
)


CFG = "cfg-1"
DB_ID = "db-1"


def _config_page(genres, sources_json):
    return {
        "properties": {
            "Active Genres": {"multi_select": [{"name": g} for g in genres]},
            "Active Sources": {"rich_text": [{"plain_text": sources_json}] if sources_json else []},
        }
    }


def test_get_active_filter_reads_genres_and_json_sources():
    client = MagicMock()
    client.pages.retrieve.return_value = _config_page(
        ["Stoicism", "Zen"], json.dumps(["Meditations", "Tao Te Ching"]))

    genres, sources = get_active_filter(client, CFG)

    assert genres == ["Stoicism", "Zen"]
    assert sources == ["Meditations", "Tao Te Ching"]


def test_get_active_filter_degrades_on_bad_json():
    client = MagicMock()
    client.pages.retrieve.return_value = _config_page(["Stoicism"], "not-json")

    genres, sources = get_active_filter(client, CFG)

    assert genres == ["Stoicism"]
    assert sources == []


def test_get_active_filter_empty_when_unset():
    client = MagicMock()
    client.pages.retrieve.return_value = {"properties": {}}

    assert get_active_filter(client, CFG) == ([], [])


def test_set_active_filter_writes_multiselect_and_json():
    client = MagicMock()

    set_active_filter(client, CFG, ["Stoicism"], ["Meditations"])

    props = client.pages.update.call_args.kwargs["properties"]
    assert props["Active Genres"] == {"multi_select": [{"name": "Stoicism"}]}
    written = props["Active Sources"]["rich_text"][0]["text"]["content"]
    assert json.loads(written) == ["Meditations"]


def test_toggle_genre_adds_then_removes():
    client = MagicMock()
    client.pages.retrieve.return_value = _config_page([], json.dumps([]))

    toggle_genre(client, CFG, "Zen")  # add
    added = client.pages.update.call_args.kwargs["properties"]["Active Genres"]
    assert added == {"multi_select": [{"name": "Zen"}]}

    client.pages.retrieve.return_value = _config_page(["Zen"], json.dumps([]))
    toggle_genre(client, CFG, "Zen")  # remove
    removed = client.pages.update.call_args.kwargs["properties"]["Active Genres"]
    assert removed == {"multi_select": []}


def test_toggle_source_adds_source():
    client = MagicMock()
    client.pages.retrieve.return_value = _config_page([], json.dumps([]))

    toggle_source(client, CFG, "Meditations")

    props = client.pages.update.call_args.kwargs["properties"]
    written = props["Active Sources"]["rich_text"][0]["text"]["content"]
    assert json.loads(written) == ["Meditations"]


def test_clear_filter_empties_both():
    client = MagicMock()

    clear_filter(client, CFG)

    props = client.pages.update.call_args.kwargs["properties"]
    assert props["Active Genres"] == {"multi_select": []}
    assert json.loads(props["Active Sources"]["rich_text"][0]["text"]["content"]) == []


def test_list_genre_options_from_schema():
    client = MagicMock()
    client.databases.retrieve.return_value = {
        "properties": {"Genre": {"multi_select": {"options": [
            {"name": "Stoicism"}, {"name": "Zen"}]}}}
    }

    assert list_genre_options(client, DB_ID) == ["Stoicism", "Zen"]


def test_list_source_values_dedups_sorts_and_paginates():
    client = MagicMock()

    def _page(name):
        return {"properties": {"Source": {"rich_text": [{"plain_text": name}]}}}

    client.databases.query.side_effect = [
        {"results": [_page("Tao Te Ching"), _page("Meditations")], "has_more": True,
         "next_cursor": "c2"},
        {"results": [_page("Meditations"), _page("Analects")], "has_more": False,
         "next_cursor": None},
    ]

    values = list_source_values(client, DB_ID)

    assert values == ["Analects", "Meditations", "Tao Te Ching"]
    assert client.databases.query.call_count == 2
