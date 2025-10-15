from typing import Tuple, Type, Union


from telegram import Update, Message
from telegram.ext import CallbackContext


from ...command.command import Command
from ...command.commands_map import CommandsMap
from ...functions import get_from_id

from .exceptions.access_deny import (
    CommandClassAccessDeny as CommandClassAccessDeny,
)
from .exceptions.commands_map_is_empty import (
    CommandsMapIsEmpty as CommandsMapIsEmpty,
)
from .exceptions.not_registered import (
    CommandClassIsNotRegistered as CommandClassIsNotRegistered,
)


class CommandsHandler:
    commands_map: Union[CommandsMap, None] = None
    """ CommandsMap: accordance of action and `Command`-class."""

    def __init__(
        self,
        commands_map: Union[CommandsMap, None] = None,
    ):
        self.commands_map = commands_map

    def set_commands_map(self, commands_map: CommandsMap):
        self.commands_map = commands_map
        return self

    async def access_control_list(
        self,
        context: CallbackContext,
        user_id: int,
        command: Type[Command],
    ) -> bool:
        """Check user access to `Command`-class within `handle()`."""
        _, _, _ = context, user_id, command
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
        """Catch all commands calls."""
        if (
            await self.middleware(
                update,
                context,
            )
            is None
        ):
            return

        message: Union[Message, None] = update.message
        if not message:
            return
        if not message.text:
            return
        if not message.text.startswith("/"):
            return
        command_name = message.text
        await self._handle_by_name(update, context, command_name)

    async def _handle_by_name(
        self,
        update: Update,
        context: CallbackContext,
        command_name: str,
    ):
        if not isinstance(self.commands_map, CommandsMap):
            raise CommandsMapIsEmpty()

        command = self.commands_map.search(command_name)
        if command is None:
            raise CommandClassIsNotRegistered(command_name)

        from_id: int = get_from_id(update)

        if await self.access_control_list(
            context,
            from_id,
            command,
        ):
            await command().on_call(
                update,
                context,
            )
        else:
            raise CommandClassAccessDeny(
                from_id,
                command_name,
            )
