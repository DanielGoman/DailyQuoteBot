
class Telegram:
    CAPTION_TEXT_LENGTH_LIMIT = 1024
    TEXT_MESSAGE_LENGTH_LIMIT = 4096
    # Telegram caps inline-button callback_data at 64 bytes, so filter toggles
    # encode the option by index rather than by its (possibly long) name.
    CALLBACK_DATA_LIMIT = 64


class Prop:
    """Notion property names. Centralised so a column rename is a one-line change."""
    # Quotes DB
    QUOTE = "Quote"
    AUTHOR = "Author"
    COVER = "Cover"
    SEND_DATE = "Send Date"
    FAVORITE = "Favorite"
    DELETED = "Deleted"
    GENRE = "Genre"        # multi_select, several per quote
    SOURCE = "Source"      # rich_text, one per quote
    # Config page
    ACTIVE_GENRES = "Active Genres"    # multi_select
    ACTIVE_SOURCES = "Active Sources"  # rich_text holding a JSON array of strings


class Callback:
    """Inline-button callback_data tokens."""
    FAVORITE = "fav"
    CYCLE = "cycle"
    DELETE = "del"
    MORE = "more"
    OPEN_FILTERS = "filters"
    TOGGLE_GENRE = "gf"     # gf:<index>
    TOGGLE_SOURCE = "sf"    # sf:<index>
    CLEAR_FILTERS = "fclr"
    DONE_FILTERS = "fdone"
    NOOP = "noop"          # non-actionable label buttons in the filter menu


DEFAULT_REFRESH_WINDOW_MONTHS = 3
