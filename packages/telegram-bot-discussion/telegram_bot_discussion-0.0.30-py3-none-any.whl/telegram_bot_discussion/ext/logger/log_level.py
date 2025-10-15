from enum import Enum
from logging import DEBUG, INFO, WARNING, ERROR


class LogLevel(Enum):
    ERROR = ERROR
    WARNING = WARNING
    INFO = INFO
    DEBUG = DEBUG
