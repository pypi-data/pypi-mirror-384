from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from .enums import ScalarType
from .resources import ColumnSchema

class AggregateFunction(str, Enum):
    """Supported aggregate functions for semantic features."""

    COUNT = "count"
    MEAN = "mean"
    MIN = "min"
    MAX = "max"
    SUM = "sum"
    APPROXIMATE_PERCENTILE = "approximate_percentile"
    APPROXIMATE_UNIQUE_COUNT = "approximate_unique_count"


@dataclass(frozen=True)
class AttributeFeature:
    """Represents a simple attribute feature.

    Attributes:
        name: Name assigned to the feature.
        input_column: Column used for the value of the feature.
        input_type: Type of the feature.
    """

    name: str
    input_column: ColumnSchema
    input_type: ScalarType


@dataclass(frozen=True)
class AggregateFeature:
    """Represents a time windowed aggregate feature."""

    name: str
    input_column: ColumnSchema
    input_type: ScalarType
    function: AggregateFunction
    time_window: timedelta

    def __post_init__(self) -> None:
        try:
            aggregate_function = AggregateFunction(self.function)
        except ValueError as error:
            allowed = ", ".join(
                sorted(function.value for function in AggregateFunction)
            )
            raise ValueError(
                f"Unsupported aggregate function: {self.function}. Allowed values are: {allowed}"
            ) from error
        object.__setattr__(self, "function", aggregate_function)


__all__ = [
    "AttributeFeature",
    "AggregateFeature",
    "AggregateFunction",
]
