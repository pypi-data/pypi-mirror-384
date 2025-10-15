from enum import Enum


class LogLevel(str, Enum):
    INFO = "info"
    DEBUG = "debug"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"
