import logging
import sys


from ...logger.logger_interface import LoggerInterface


from .log_level import LogLevel


class Printer(LoggerInterface):
    logger: logging.Logger

    def __init__(self, name: str, level: LogLevel):
        logging.getLogger(name).addHandler(logging.NullHandler())
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)8s %(message)s")
        )
        handler.setLevel(level.value)
        self.logger.setLevel(level.value)
        self.logger.addHandler(handler)

    def debug(self, *args, **kwargs):
        self.logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        self.logger.info(*args, **kwargs)

    def warning(self, *args, **kwargs):
        self.logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        self.logger.error(*args, **kwargs)
