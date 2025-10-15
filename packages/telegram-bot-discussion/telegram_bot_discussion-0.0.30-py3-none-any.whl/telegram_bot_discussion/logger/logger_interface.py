from abc import ABC, abstractmethod


class LoggerInterface(ABC):
    """`LoggerInterface` is interface for logging-classes.

    Already exist:

    - stdout logger (`telegram-bot-discussion.ext.logger.printer.Printer`);
    - file output logger (`telegram-bot-discussion.ext.logger.time_rotating_file.TimeRotatingFile`).

    In example also present:

    - json-format logger based on `pythonjsonlogger.jsonlogger.JsonFormatter`.
    """

    @abstractmethod
    def debug(self, *args, **kwargs):
        """Fix data as debug-level message"""
        ...

    @abstractmethod
    def info(self, *args, **kwargs):
        """Fix data as info-level message"""
        ...

    @abstractmethod
    def warning(self, *args, **kwargs):
        """Fix data as warning-level message"""
        ...

    @abstractmethod
    def error(self, *args, **kwargs):
        """Fix data as error-level message"""
        ...

    def __call__(self, *args, **kwargs):
        self.info(*args, **kwargs)
