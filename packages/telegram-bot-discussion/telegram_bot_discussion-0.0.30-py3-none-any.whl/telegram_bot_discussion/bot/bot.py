from typing import Dict, Iterable, Union


from telegram.ext import (
    filters,
    Application,
    CallbackQueryHandler,
    ExtBot,
    MessageHandler,
    PollAnswerHandler,
    PollHandler,
)

from ..bot.exceptions.buttons_handler_is_not_set import (
    ButtonsHandlerIsNotSet,
)
from ..bot.exceptions.commands_handler_is_not_set import (
    CommandsHandlerIsNotSet,
)
from ..bot.exceptions.replicas_handler_is_not_set import (
    ReplicasHandlerIsNotSet,
)


from ..config import Config
from ..constants.constants import _DISCUSSION
from ..handlers.buttons_handler.buttons_handler import ButtonsHandler
from ..handlers.commands_handler.commands_handler import CommandsHandler
from ..handlers.replicas_handler.replicas_handler import ReplicasHandler
from ..logger.logger_interface import LoggerInterface


class ApplicationWasNotInit(Exception):
    """Exception raise when Telegram-bot application was not init in some reason (in the general case Telegram-bot application initialized automatically)."""

    def __init__(self, *args) -> None:
        self.message = None
        if args:
            self.message = args[0]

    def __str__(self):
        if self.message:
            return f"First of all it need to init Telegram-application, {self.message}"
        return "Telegram-application was not init"


class Discussion:
    """`Discussion` is main class of your Telegram-bot application.

    It could be say that the `Discussion` is `Telegram`-bot."""

    _application: Application
    config: Config
    _dialogues = dict()
    _logger: LoggerInterface

    _buttons_handler: Union[ButtonsHandler, None]
    _commands_handler: Union[CommandsHandler, None]
    _replicas_handler: Union[ReplicasHandler, None]

    def __init__(self, logger: LoggerInterface, config: Config, *args, **kwargs):
        self.config = config
        self._logger = logger
        self._dialogues = dict()
        self._buttons_handler = None
        self._commands_handler = None
        self._replicas_handler = None
        self.init_application()

    def get_application(self) -> Application:
        if getattr(self, "_application", None) is None:
            raise ApplicationWasNotInit()
        return self._application

    def bot(self) -> ExtBot:
        """
        Returns:
            ExtBot: native Telegram-bot object.
        """
        return self.get_application().bot

    def get_dialogues(self) -> Dict[int, Iterable]:
        """
        Dialogues structure `Dict[int, Iterable]` - is main idea of `telegram-bot-discussion`.

        It is a dictionary collection of pairs of Bot User ID and the next stage of their dialogue.
        """

        return self._dialogues

    def get_logger(self) -> LoggerInterface:
        return self._logger

    def init_application(
        self,
        read_timeout=600,
        get_updates_read_timeout=600,
        write_timeout=600,
        get_updates_write_timeout=600,
        pool_timeout=600,
        get_updates_pool_timeout=600,
        connect_timeout=600,
        get_updates_connect_timeout=600,
    ) -> "Discussion":
        self.get_logger().debug(f"init_application()")
        self._application = (
            Application.builder()
            .token(self.config.token)
            .read_timeout(read_timeout)
            .get_updates_read_timeout(get_updates_read_timeout)
            .write_timeout(write_timeout)
            .get_updates_write_timeout(get_updates_write_timeout)
            .pool_timeout(pool_timeout)
            .get_updates_pool_timeout(get_updates_pool_timeout)
            .connect_timeout(connect_timeout)
            .get_updates_connect_timeout(get_updates_connect_timeout)
            .build()
        )
        setattr(
            self._application,
            _DISCUSSION,
            self,
        )
        return self

    def _reset_handlers(self) -> "Discussion":
        self.get_application().handlers = dict()
        commands_handler_exists: Union[CommandsHandler, None] = self._commands_handler
        if commands_handler_exists:
            self.get_application().add_handler(
                MessageHandler(
                    filters.COMMAND,
                    commands_handler_exists.handle,
                )
            )
        buttons_handler_exists: Union[ButtonsHandler, None] = self._buttons_handler
        if buttons_handler_exists:
            self.get_application().add_handler(
                CallbackQueryHandler(
                    buttons_handler_exists.handle,
                )
            )
        replicas_handler_exists: Union[ReplicasHandler, None] = self._replicas_handler
        if replicas_handler_exists:
            self.get_application().add_handler(
                MessageHandler(
                    filters.ALL,
                    replicas_handler_exists.handle,
                )
            )
            self.get_application().add_handler(
                PollAnswerHandler(
                    replicas_handler_exists.handle,
                )
            )
            self.get_application().add_handler(
                PollHandler(
                    replicas_handler_exists.handle,
                )
            )
        return self

    def set_commands_handler(self, commands_handler: CommandsHandler) -> "Discussion":
        self.get_logger().debug(f"Setup COMMAND-handler")
        commands_handler_exists: Union[CommandsHandler, None] = getattr(
            self, "_commands_handler", None
        )
        if commands_handler_exists:
            self.get_application().remove_handler(
                MessageHandler(
                    filters.COMMAND,
                    commands_handler_exists.handle,
                )
            )
        self._commands_handler = commands_handler
        self._reset_handlers()
        return self

    def set_replicas_handler(self, replicas_handler: ReplicasHandler) -> "Discussion":
        self.get_logger().debug(f"Setup REPLICAS-handler")
        replicas_handler_exists: Union[ReplicasHandler, None] = getattr(
            self, "_replicas_handler", None
        )
        if replicas_handler_exists:
            self.get_application().remove_handler(
                MessageHandler(
                    filters.ALL,
                    replicas_handler_exists.handle,
                )
            )
            self.get_application().remove_handler(
                PollAnswerHandler(
                    replicas_handler_exists.handle,
                )
            )
            self.get_application().remove_handler(
                PollHandler(
                    replicas_handler_exists.handle,
                )
            )
        self._replicas_handler = replicas_handler
        self._reset_handlers()
        return self

    def set_buttons_handler(self, buttons_handler: ButtonsHandler) -> "Discussion":
        self.get_logger().debug(f"Setup BUTTONS-handler")
        buttons_handler_exists: Union[ButtonsHandler, None] = getattr(
            self, "_buttons_handler", None
        )
        if buttons_handler_exists:
            self.get_application().remove_handler(
                CallbackQueryHandler(
                    buttons_handler_exists.handle,
                )
            )
        self._buttons_handler = buttons_handler
        self._reset_handlers()
        return self

    def get_buttons_handler(self) -> ButtonsHandler:
        if self._buttons_handler is None:
            raise ButtonsHandlerIsNotSet()
        return self._buttons_handler

    def get_commands_handler(self) -> CommandsHandler:
        if self._commands_handler is None:
            raise CommandsHandlerIsNotSet()
        return self._commands_handler

    def get_replicas_handler(self) -> ReplicasHandler:
        if self._replicas_handler is None:
            raise ReplicasHandlerIsNotSet()
        return self._replicas_handler

    def start(self):
        self.get_logger().debug(f"run_polling()")
        self.get_application().run_polling()
