from typing import Union


from telegram import Update
from telegram.ext import CallbackContext


__CHAT_ID = "chat_id"


class ChatIdWasNotFetched(Exception):
    def __str__(self):
        return "ChatId was not fetched"


def get_chat_id(
    update: Update,
    context: Union[CallbackContext, None] = None,
) -> int:
    """get_chat_id() try fetch `chat_id` (from `update.message`, `update.callback_query` or `context`) of initiator (it can be User, Chat, Channel), which appeal to Telegram-bot.

    :raises ChatIdWasNotFetched: When initiator was not detected.
    """
    if update.message:
        if context:
            context.bot_data[__CHAT_ID] = update.message.chat_id
        return update.message.chat_id
    elif update.callback_query and update.callback_query.message:
        if context:
            context.bot_data[__CHAT_ID] = update.callback_query.message.chat.id
        return update.callback_query.message.chat.id
    elif context and context.bot_data.get(__CHAT_ID):
        return context.bot_data.get(__CHAT_ID)
    else:
        raise ChatIdWasNotFetched()
