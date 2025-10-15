from typing import Any, List, Type, Union


from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    MaybeInaccessibleMessage,
    Message,
    Update,
    ReplyKeyboardRemove,
)
from telegram.ext import CallbackContext


from ....bot.bot import Discussion
from ....bot.exceptions import ButtonsHandlerIsNotSet
from ....bot.contextual import Contextual
from ....dialogue.replicas import Replica
from ....functions import get_chat_id, get_message
from ..buttons.page_button_i import PageButtonInterface
from ..dao.item import Item
from .page_meta import PageReplicaMeta


class PageReplica(Replica):
    query: Any
    page: int = 1
    page_button_class: Type[PageButtonInterface]

    class Meta(PageReplicaMeta): ...

    def __init__(
        self,
        query: Any,
        page: int,
        page_button_class: Type[PageButtonInterface],
    ):
        self.query = query
        if page < 1:
            page = 1
        self.page = page
        self.page_button_class = page_button_class

    async def as_reply(
        self,
        update: Update,
        context: CallbackContext,
    ):
        message: Union[MaybeInaccessibleMessage, Message] = get_message(update)
        chat_id: int = get_chat_id(update)

        discussion: Discussion = Contextual[Discussion](context)()
        items: List[Item] = self.__class__.Meta.item_class.page(
            query=self.query,
            page=self.page,
        )

        items_as_text = ""
        for item in items:
            items_as_text += f"\n\n{item.item()}"
        if not items_as_text:
            items_as_text = "Not found"
        buttons = [[]]
        buttons_handler = discussion.get_buttons_handler()
        if not buttons_handler:
            raise ButtonsHandlerIsNotSet()

        items_as_buttons = [
            self.__class__.Meta.item_button_class(chat_id, item) for item in items
        ]
        items_as_telegram_buttons: List[List[InlineKeyboardButton]] = [
            [item_as_button.as_button(buttons_handler.coder)]
            for item_as_button in items_as_buttons
        ]
        next_page_exists = self.__class__.Meta.item_class.is_page_exist(
            query=self.query,
            page=self.page + 1 if self.page else 2,
        )
        pagination_buttons: List[InlineKeyboardButton] = []
        current_page_button = self.page_button_class(chat_id, self.query, self.page)
        prev_page_button = current_page_button.get_prev_page_button()
        if prev_page_button:
            pagination_buttons.append(prev_page_button.as_button(buttons_handler.coder))
        if next_page_exists:
            next_page_button = current_page_button.get_next_page_button()
            pagination_buttons.append(next_page_button.as_button(buttons_handler.coder))
        buttons = items_as_telegram_buttons
        buttons.append(pagination_buttons)

        inline_keyboard_markup = InlineKeyboardMarkup(buttons)
        if update.callback_query and update.callback_query.message:
            await discussion.bot().edit_message_text(
                chat_id=chat_id,
                message_id=message.message_id,
                text=items_as_text,
            )
            await discussion.bot().edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message.message_id,
                reply_markup=inline_keyboard_markup,
            )
        else:
            #############################
            # Telegram feature start
            temp_message = await discussion.bot().send_message(
                chat_id=chat_id,
                text="...",
                reply_markup=ReplyKeyboardRemove(),
            )
            await temp_message.delete()
            # Telegram feature end
            #############################
            await discussion.bot().send_message(
                chat_id=chat_id,
                text=items_as_text,
                reply_to_message_id=message.message_id,
                allow_sending_without_reply=True,
                reply_markup=inline_keyboard_markup,
            )
