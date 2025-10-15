from typing import Dict, Tuple, Type, Union


from telegram import Update
from telegram.ext import CallbackContext


from ...bot.contextual import Contextual
from ...dialogue.dialogue import Dialogue, Polemic
from ...dialogue.replicas.base import (
    NoNeedReactionReplica,
    Replica,
    StopReplica,
)
from ...functions import (
    get_chat_id,
    get_from_id,
)
from ...functions.chat_id import (
    ChatIdWasNotFetched,
)
from ...functions.from_user import (
    FromUserWasNotFetched,
)
from ...logger.logger_interface import LoggerInterface
from .exceptions.access_deny import (
    ReplicaClassAccessDeny as ReplicaClassAccessDeny,
)


class _DiscussionInterface:
    def get_dialogues(self) -> Dict[int, Polemic]: ...
    def get_logger(self) -> LoggerInterface: ...


class ReplicasHandler:

    async def access_control_list(
        self,
        user_id: int,
        replica_class: Type[Replica],
    ) -> bool:
        _, _ = user_id, replica_class
        """Check user access to `Replica`-class within `handle()`."""
        return True

    async def middleware(
        self,
        update: Update,
        context: CallbackContext,
    ) -> Union[Tuple[Update, CallbackContext], None]:
        """Middleware work within `handle()`. If it returns None, `handle()` will not work."""
        return update, context

    async def when_there_are_no_any_dialog(
        self,
        update: Update,
        context: CallbackContext,
    ) -> Union[Tuple[Update, CallbackContext], None]:
        """Do something if Telegram-bot have not any dialog with initiator (often User)."""
        return update, context

    async def handle(
        self,
        update: Update,
        context: CallbackContext,
    ):
        """Catch all events, which are not commands calls and buttons clicks.

        :raises ChatIdWasNotFetched: If User was not detected, `handle()` try find other event initiator. If event initiator not found `ChatIdWasNotFetched` will be raised.
        """
        if (
            await self.middleware(
                update,
                context,
            )
            is None
        ):
            return

        discussion: _DiscussionInterface = Contextual[_DiscussionInterface](context)()

        try:
            from_id = get_from_id(update, context)
            if not from_id:
                discussion.get_logger().warning("from_id is None")
                return

            if from_id in discussion.get_dialogues():
                await self.get_replica_from_dialogue(
                    update,
                    context,
                )
            else:
                await self.when_there_are_no_any_dialog(
                    update,
                    context,
                )
        except FromUserWasNotFetched as _:
            discussion.get_logger().warning("from_id does not exist")
            try:
                chat_id = get_chat_id(update, context)
                if not chat_id:
                    discussion.get_logger().warning("chat_id is None")
                    return

                if chat_id in discussion.get_dialogues():
                    await self.get_replica_from_dialogue(
                        update,
                        context,
                    )
                else:
                    await self.when_there_are_no_any_dialog(
                        update,
                        context,
                    )
            except ChatIdWasNotFetched as chat_id_exc:
                discussion.get_logger().warning("chat_id does not exist")
                raise chat_id_exc

    async def get_replica_from_dialogue(
        self,
        update: Update,
        context: CallbackContext,
    ):
        from_id = get_from_id(update, context)
        if not from_id:
            return

        discussion: _DiscussionInterface = Contextual[_DiscussionInterface](context)()

        while True:
            try:
                replica: Replica = discussion.get_dialogues()[from_id].send(update)
                if isinstance(replica, StopReplica):
                    self.stop_dialogue(
                        context=context,
                        with_user_id=from_id,
                    )

                if await self.access_control_list(
                    from_id,
                    replica.__class__,
                ):
                    await replica.as_reply(update, context)
                else:
                    raise ReplicaClassAccessDeny(from_id, replica.__class__)
                if isinstance(replica, StopReplica):
                    break
                if isinstance(replica, NoNeedReactionReplica):
                    continue
                break

            except KeyError as e:
                discussion.get_logger().error(e)
                raise e
            except Exception as e:
                discussion.get_logger().error(e)
                self.stop_dialogue(
                    context=context,
                    with_user_id=from_id,
                )
                raise e

    async def start_dialogue(
        self,
        update: Update,
        context: CallbackContext,
        with_user_id: int,
        dialogue: Dialogue,
    ):
        discussion: _DiscussionInterface = Contextual[_DiscussionInterface](context)()

        if not with_user_id:
            with_user_id = get_from_id(update, context)

        self.stop_dialogue(context, with_user_id)
        discussion.get_dialogues()[with_user_id] = dialogue.replicas_flow()
        _ = next(discussion.get_dialogues()[with_user_id])
        await self.get_replica_from_dialogue(update, context)

    def stop_dialogue(
        self,
        context: CallbackContext,
        with_user_id: int,
    ):
        discussion: _DiscussionInterface = Contextual[_DiscussionInterface](context)()
        if with_user_id in discussion.get_dialogues():
            del discussion.get_dialogues()[with_user_id]
