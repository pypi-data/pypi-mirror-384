from datetime import datetime, timezone
from enum import Enum
from typing import Callable


class LogLevel(str, Enum):
    Info = "info"
    Warning = "warn"
    Error = "error"


Logger = Callable[[LogLevel, str], None]


def logger(level: LogLevel, message: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    print(f"[{timestamp}] [{level}] {message}")
