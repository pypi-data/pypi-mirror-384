from enum import StrEnum
from typing import Optional, TypeVar
from maleo.types.string import ListOfStrs


class MeasurementType(StrEnum):
    REGULAR = "regular"
    AGGREGATE = "aggregate"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


MeasurementTypeT = TypeVar("MeasurementTypeT", bound=MeasurementType)
OptionalMeasurementType = Optional[MeasurementType]


class AggregateMeasurementType(StrEnum):
    AVERAGE = "average"
    PEAK = "peak"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


AggregateMeasurementTypeT = TypeVar(
    "AggregateMeasurementTypeT", bound=AggregateMeasurementType
)
OptionalAggregateMeasurementType = Optional[AggregateMeasurementType]
OptionalAggregateMeasurementTypeT = TypeVar(
    "OptionalAggregateMeasurementTypeT", bound=OptionalAggregateMeasurementType
)


class Status(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    OVERLOAD = "overload"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]
