import logging
from logging.handlers import TimedRotatingFileHandler
import os
from typing import Union


from ...logger.logger_interface import LoggerInterface


from .log_level import LogLevel


class TimeRotatingFile(LoggerInterface):
    logger: logging.Logger

    def __init__(
        self,
        name: str,
        level: LogLevel,
        dir: Union[str, None] = None,
    ):
        if level is None:
            level = LogLevel.INFO
        logging.getLogger(name).addHandler(logging.NullHandler())
        self.logger = logging.getLogger(name)
        if dir is None:
            dir = "./"
        log_dir_path = os.path.join(dir, f"logs")
        if not os.path.exists(log_dir_path):
            os.makedirs(
                log_dir_path,
                mode=0o740,
                exist_ok=True,
            )
        log_file_path = os.path.join(log_dir_path, f"{name}.log")
        handler = TimedRotatingFileHandler(
            log_file_path,
            when="midnight",
            interval=1,
            backupCount=5,
        )
        handler.setFormatter(
            logging.Formatter(fmt="%(asctime)s %(levelname)8s %(message)s")
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
