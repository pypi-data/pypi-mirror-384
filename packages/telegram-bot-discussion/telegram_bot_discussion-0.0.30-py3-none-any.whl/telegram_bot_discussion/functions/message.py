from typing import Union


from telegram import (
    MaybeInaccessibleMessage,
    Message,
    Update,
)


class MessageWasNotFetched(Exception):
    def __str__(self):
        return "Message was not fetched"


def get_message(update: Update) -> Union[MaybeInaccessibleMessage, Message]:
    """get_message() try fetch `user_id` (from `update.message`, `update.callback_query`) of initiator (it can be User, Chat, Channel), which appeal to Telegram-bot.

    :raises MessageWasNotFetched: When message of initiator was not detected.
    """
    if update.callback_query and update.callback_query.message:
        return update.callback_query.message
    elif update.message:
        return update.message
    else:
        raise MessageWasNotFetched()
