from datetime import datetime, UTC
from typing import Dict, Tuple, Type, Union


from telegram import CallbackQuery, Update, User
from telegram.ext import CallbackContext


from ...bot.contextual import Contextual
from ...button.button import Button
from ...button.buttons_map import ButtonsMap
from ...button.coder_interface import CoderInterface
from ...button.params import Params
from ...dialogue.dialogue import Polemic
from ...functions import (
    get_chat_id,
    get_from_id,
)
from ...logger.logger_interface import LoggerInterface
from .exceptions.access_deny import (
    ButtonClassAccessDeny as ButtonClassAccessDeny,
)
from .exceptions.life_time_overflow import (
    ButtonClassLifeTimeOverflow as ButtonClassLifeTimeOverflow,
)
from .exceptions.not_registered import (
    ButtonClassIsNotRegistered as ButtonClassIsNotRegistered,
)
from .exceptions.signification_error import (
    ButtonDataSignificationError as ButtonDataSignificationError,
)
from .exceptions.buttons_map_is_empty import (
    ButtonsMapIsEmpty as ButtonsMapIsEmpty,
)


class _DiscussionInterface:
    def get_dialogues(self) -> Dict[int, Polemic]: ...
    def get_logger(self) -> LoggerInterface: ...
    def get_buttons_handler(self) -> "ButtonsHandler": ...


class ButtonsHandler:
    buttons_map: ButtonsMap
    """ ButtonsMap: accordance of action and `Button` class."""
    coder: CoderInterface
    """ CoderInterface: how to serialize and deserialize stored in button data."""

    def __init__(
        self,
        coder: CoderInterface,
        buttons_map: ButtonsMap,
    ):
        self.coder = coder
        self.buttons_map = buttons_map

    def set_buttons_map(self, buttons_map: ButtonsMap):
        self.buttons_map = buttons_map
        return self

    async def access_control_list(
        self,
        context: CallbackContext,
        user_id: int,
        button_class: Type[Button],
    ) -> bool:
        """Check user access to `Button`-class within `handle()`."""
        _, _, _ = context, user_id, button_class
        return True

    async def middleware(
        self,
        update: Update,
        context: CallbackContext,
    ) -> Union[Tuple[Update, CallbackContext], None]:
        """Middleware work within `handle()`. If it returns None, `handle()` will not work."""
        return update, context

    async def handle(
        self,
        update: Update,
        context: CallbackContext,
    ):
        """Catch all buttons clicks."""
        if (
            await self.middleware(
                update,
                context,
            )
            is None
        ):
            return

        callback_query: Union[CallbackQuery, None] = update.callback_query
        if not callback_query:
            return
        if not callback_query.data:
            return
        from_user: Union[User, None] = callback_query.from_user
        if not from_user:
            return

        if not self.buttons_map:
            raise ButtonsMapIsEmpty()

        discussion: _DiscussionInterface = Contextual[_DiscussionInterface](context)()
        if not discussion.get_buttons_handler().coder.check_signature(
            get_chat_id(update),
            callback_query.data,
            get_from_id(update),
        ):
            raise ButtonDataSignificationError(from_user.id, callback_query.data)

        params = Params.fetch(
            callback_query=callback_query,
            coder=self.coder,
        )
        discussion.get_logger().debug(f"Params {params}")

        button_action = params.action
        button_class = self.buttons_map.search(button_action)

        if button_class is None:
            raise ButtonClassIsNotRegistered(button_action)

        if not await self.access_control_list(
            context,
            from_user.id,
            button_class,
        ):
            raise ButtonClassAccessDeny(from_user.id, button_action)
        life_time = button_class.life_time()
        if (
            callback_query.message
            and life_time
            and datetime.now(tz=UTC) > callback_query.message.date + life_time
        ):
            raise ButtonClassLifeTimeOverflow(button_action)
        await button_class.on_click(update, context)
