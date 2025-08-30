
class Callbacks:
    MAKE_FAVORITE = "make_favorite"
    # MAKE_NOT_FAVORITE = "make_not_favorite"
    PUT_BACK_TO_CYCLE = 'put_back_to_cycle'
    DELETE_QUOTE = 'delete_quote'

class API:
    SERVICE_NAME = "daily_quote_bot"
    ROUTE = "add_keyboard_buttons_to_message"

    # URL = f"https://{SERVICE_NAME}.onrender.com/{ROUTE}"
    URL = F"http://localhost:8000/{ROUTE}"
