from typing import Generic, TypeVar, Type


from telegram.ext import CallbackContext


from ..constants.constants import _DISCUSSION


T = TypeVar("T")


class Contextual(Generic[T]):
    """`Contextual`-generic help fetch your `Discussion` inheritance from context.

    .. highlight:: python
    .. code-block:: python

        // It is your bot
        class ChildBotOfDiscussion(Discussion):
            child_filed: str = "child field"
            ...

        // Everywhere where you need (dialogues, handlers, middlewares)
        // get your Telegram-bot properties (like config, params, additional methods and etc.)
        // use this construction

        discussion: ChildBotOfDiscussion = Contextual[ChildBotOfDiscussion](context)()
        print(discussion.child_filed)

    """

    _superclass: Type

    context: CallbackContext

    def __init__(self, context: CallbackContext) -> None:
        if not getattr(Contextual, "_superclass", None):
            from .bot import (
                Discussion,
            )  # TODO: This once import solves circular import

            Contextual._superclass = Discussion
        self.context = context

    def instance(self) -> T:
        """Fetch instance of your Discussion-child from context.

        But better use more shot syntax sugar:

        .. highlight:: python
        .. code-block:: python

            discussion: ChildBotOfDiscussion = Contextual[ChildBotOfDiscussion](context)()

        Raises:
            ContextObjectIsNotDiscussion: when fetched object is not detected as Discussion-child.
        """
        stored = getattr(
            self.context.application,
            _DISCUSSION,
        )

        if not issubclass(stored.__class__, Contextual._superclass):
            raise ContextObjectIsNotDiscussion()
        return stored

    def __call__(self) -> T:
        return self.instance()


class ContextObjectIsNotDiscussion(Exception):
    def __str__(self):
        return "Context object is not Discussion"
