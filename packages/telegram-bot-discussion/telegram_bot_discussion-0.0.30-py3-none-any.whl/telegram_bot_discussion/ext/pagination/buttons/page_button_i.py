from typing import Any, Union


from telegram import Update
from telegram.ext import CallbackContext


from ....button import Button


class PageButtonInterface(Button):

    def __init__(
        self,
        chat_id: int,
        query: Any,
        page: int,
    ):
        _, _, _ = chat_id, query, page
        raise Exception(f"Class `{self.__class__.__name__}` is interface!")

    def get_next_page_button(self) -> "PageButtonInterface":
        raise Exception(f"Class `{self.__class__.__name__}` is interface!")

    def get_prev_page_button(self) -> Union["PageButtonInterface", None]:
        raise Exception(f"Class `{self.__class__.__name__}` is interface!")

    @classmethod
    async def on_click(
        cls,
        update: Update,
        context: CallbackContext,
    ):
        _, _ = update, context
        raise Exception(f"Class `{cls.__name__}` is interface!")
