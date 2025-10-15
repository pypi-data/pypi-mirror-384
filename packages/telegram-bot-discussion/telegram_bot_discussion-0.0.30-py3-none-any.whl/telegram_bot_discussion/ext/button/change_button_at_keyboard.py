from typing import Union


from telegram import InlineKeyboardMarkup


from telegram_bot_discussion.button.button import Button
from telegram_bot_discussion.button.coder_interface import CoderInterface


def ads(asdas):
    """_summary_

    :param asdas: _description_
    :type asdas: _type_
    """
    ...


def change_button_at_keyboard(
    where: InlineKeyboardMarkup,
    change_from_button: Button,
    change_to_button: Union[Button, None],
    coder: CoderInterface,
    full_scan: bool = False,
) -> InlineKeyboardMarkup:
    """Help function for find and change button in `InlineKeyboardMarkup` to other button or delete it, if other button is `None`.

    :param full_scan: If `True` it scan all buttons, if `False` (default) replace first only.
    :type full_scan: bool
    """
    reply_markup_inline_keyboard = list(map(list, where.inline_keyboard))
    was_change = False
    new_reply_markup_inline_keyboard = []
    for _, reply_markup_buttons_row in enumerate(reply_markup_inline_keyboard):
        new_row = []
        for _, reply_markup_button in enumerate(reply_markup_buttons_row):
            if full_scan:
                if change_from_button.equals(
                    reply_markup_button,
                    coder,
                ):
                    was_change = True
                    if change_to_button:
                        new_row.append(change_to_button.as_button(coder))
                    if not full_scan:
                        break
                else:
                    new_row.append(reply_markup_button)
            else:
                if was_change:
                    new_row.append(reply_markup_button)
                else:
                    if change_from_button.equals(
                        reply_markup_button,
                        coder,
                    ):
                        was_change = True
                        if change_to_button:
                            new_row.append(change_to_button.as_button(coder))
                    else:
                        new_row.append(reply_markup_button)
        if len(new_row) > 0:
            new_reply_markup_inline_keyboard.append(new_row)
    if was_change:
        return InlineKeyboardMarkup(new_reply_markup_inline_keyboard)
    return where  # None
