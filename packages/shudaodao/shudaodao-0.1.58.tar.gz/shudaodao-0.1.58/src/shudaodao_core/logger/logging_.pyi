from ..config.app_config import AppConfig as AppConfig
from _typeshed import Incomplete
from enum import Enum

class LoggingLevel(Enum):
    """日志级别枚举"""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40

class _Logger:
    """自定义日志系统，不影响标准 logging 模块的其他日志"""

    line_length: int
    logger: Incomplete
    def __init__(self) -> None: ...
    def debug(self, message: object, *args, **kwargs) -> None: ...
    def debug_line(self) -> None: ...
    def info(self, message: object, *args, **kwargs) -> None: ...
    def info_line(self) -> None: ...
    def warning(self, message: object, *args, **kwargs) -> None: ...
    def error(self, message: object, *args, **kwargs) -> None: ...
    def critical(self, message: object, *args, **kwargs) -> None: ...

logging: Incomplete
