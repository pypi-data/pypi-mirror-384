from typing import Any, Union


from telegram import Update
from telegram.ext import CallbackContext


from ....bot.bot import Discussion
from ....bot.exceptions import ButtonsHandlerIsNotSet
from ....bot.contextual import Contextual
from ....button import Button
from .page_button_i import PageButtonInterface
from .page_button_meta import PageButtonMeta
from .page_button_params import PageButtonParams


class PageButton(PageButtonInterface, Button):

    class Meta(PageButtonMeta): ...

    query: Any
    params: PageButtonParams

    def __init__(
        self,
        chat_id: int,
        query: Any,
        page: int,
    ):
        self.chat_id = chat_id
        self.query = query
        self.params = PageButtonParams(
            action=self.action(),
            query=query,
            page=page,
        )
        Button.__init__(self, self.chat_id)

    def get_next_page_button(self) -> "PageButton":
        button = self.__class__(
            chat_id=self.chat_id,
            query=self.query,
            page=self.params.page + 1,
        )
        button.set_title("»")
        return button

    def get_prev_page_button(self) -> Union["PageButton", None]:
        if self.params.page <= 1:
            return None
        button = self.__class__(
            chat_id=self.chat_id,
            query=self.query,
            page=self.params.page - 1,
        )
        button.set_title("«")
        return button

    @classmethod
    async def on_click(
        cls,
        update: Update,
        context: CallbackContext,
    ):
        discussion: Discussion = Contextual[Discussion](context)()
        buttons_handler = discussion.get_buttons_handler()
        if not buttons_handler:
            raise ButtonsHandlerIsNotSet()
        params = PageButtonParams.fetch(
            callback_query=update.callback_query,
            coder=buttons_handler.coder,
        )
        await cls.Meta.page_replica(
            query=params.query,
            page=params.page,
            page_button_class=cls,
        ).as_reply(
            update,
            context,
        )
