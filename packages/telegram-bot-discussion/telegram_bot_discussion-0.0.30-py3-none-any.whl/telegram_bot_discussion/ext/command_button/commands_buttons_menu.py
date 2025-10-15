from typing import Sequence, Union


from telegram import InlineKeyboardButton, InlineKeyboardMarkup


from ...button.coder_interface import CoderInterface
from .command_button import CommandButton


class CommandsButtonsMenu:
    _commands_buttons: Sequence[Sequence[CommandButton]] = []
    _callback_data_coder: CoderInterface

    def __init__(
        self,
        coder: CoderInterface,
        commands_buttons: Union[Sequence[Sequence[CommandButton]], None] = None,
    ):
        self.coder = coder
        if commands_buttons is None:
            self._commands_buttons = self.__class__._commands_buttons
        else:
            self._commands_buttons = commands_buttons

    def set_commands_buttons(
        self,
        commands_buttons: Sequence[Sequence[CommandButton]],
    ) -> "CommandsButtonsMenu":
        self._commands_buttons = commands_buttons
        return self

    def get_commands_buttons(self) -> Sequence[Sequence[CommandButton]]:
        return self._commands_buttons

    def as_keyboard(self) -> InlineKeyboardMarkup:
        sequence: Sequence[Sequence[InlineKeyboardButton]] = []
        for commands_buttons_row in self.get_commands_buttons():
            sequence_row: Sequence[InlineKeyboardButton] = []
            for command_button_row in commands_buttons_row:
                sequence_row.append(command_button_row.as_button(self.coder))
            sequence.append(sequence_row)
        return InlineKeyboardMarkup(
            sequence,
        )
