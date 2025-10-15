from telegram import Update
from telegram.ext import CallbackContext


from ... import Discussion, Contextual
from ...button import Button
from ...command import Command
from .command_button_param import CommandButtonParams


class CommandButton(Button):

    class Meta(Button.Meta):
        action: str = "command"

    params: CommandButtonParams

    def __init__(
        self,
        chat_id: int,
        command: Command,
    ):
        self.params = CommandButtonParams(command_name=command.action())
        super().__init__(chat_id)
        self.set_title(command.get_title())

    @classmethod
    async def on_click(
        cls,
        update: Update,
        context: CallbackContext,
    ):
        discussion: Discussion = Contextual[Discussion](context)()
        params: CommandButtonParams = CommandButtonParams.fetch(
            callback_query=update.callback_query,
            coder=discussion.get_buttons_handler().coder,
        )
        await discussion.get_commands_handler()._handle_by_name(
            update,
            context,
            params.command_name,
        )
