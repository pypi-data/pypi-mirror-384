from typing import Mapping, Sequence
from maleo.logging.enums import Level
from .enums import Status


STATUS_ORDER: Sequence[Status] = [
    Status.LOW,
    Status.NORMAL,
    Status.HIGH,
    Status.CRITICAL,
    Status.OVERLOAD,
]


STATUS_LOG_LEVEL: Mapping[Status, Level] = {
    Status.LOW: Level.INFO,
    Status.NORMAL: Level.INFO,
    Status.HIGH: Level.WARNING,
    Status.CRITICAL: Level.ERROR,
    Status.OVERLOAD: Level.CRITICAL,
}
