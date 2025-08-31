from notion_client import Client
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.bot_service.consts import FavoriteToggleStates


async def action_make_favorite(notion_client: Client, quote_id: str, **kwargs):
    page = notion_client.pages.retrieve(page_id=quote_id)
    is_favorite = page["properties"]["Favorite"]["checkbox"]
    new_state = not is_favorite

    notion_client.pages.update(
        page_id=quote_id,
        properties={
            "Favorite": {
                "checkbox": not is_favorite
            }
        }
    )
    new_button_text = FavoriteToggleStates.MAKE_NOT_FAVORITE if new_state else FavoriteToggleStates.MAKE_FAVORITE

    query = kwargs['query']
    keyboard = query.message.reply_markup.inline_keyboard
    keyboard = list(map(list, keyboard))
    # Find the button that was clicked and update only its text
    for i, row in enumerate(keyboard):
        for j, btn in enumerate(row):
            if btn.callback_data == query.data:  # this is the clicked button
                # Create a new button with same callback_data but new text
                new_text = new_button_text
                keyboard[i][j] = InlineKeyboardButton(new_text, callback_data=btn.callback_data)


    # Push the update
    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def action_put_back_to_cycle(notion_client: Client, quote_id: str, **kwargs) -> None:
    notion_client.pages.update(
        page_id=quote_id,
        properties={
            "Send Date": {
                "date": None
            }
        }
    )


async def action_delete_quote(notion_client: Client, quote_id: str, **kwargs) -> None:
    notion_client.pages.update(
        page_id=quote_id,
        archived=True
    )
