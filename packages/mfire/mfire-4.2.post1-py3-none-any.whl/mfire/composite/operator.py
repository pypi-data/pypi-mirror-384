from __future__ import annotations

import operator
from enum import Enum
from typing import Any, List

import numpy as np

import mfire.utils.mfxarray as xr
from mfire.settings import get_logger

# Logging
LOGGER = get_logger(name="composite.operators.mod", bind="composite.operators")


class Operator(str, Enum):
    """
    Operator object that translates configuration data into Python operators or
    specific functions.
    """

    def __new__(cls, *args) -> Operator:
        obj = str.__new__(cls, args[0])
        obj._value_, obj.oper = args[0], args[1]
        return obj

    def __call__(self, v1: object, v2: object) -> Any:
        return self.oper(v1, v2)


class LogicalOperator(Operator):
    """
    Logical AND and OR operators.

    Inherits: Operator
    """

    @staticmethod
    def or_operator(
        first_field: xr.DataArray | xr.Dataset, second_field: xr.DataArray | xr.Dataset
    ) -> bool:
        if first_field.count().equals(second_field.count()):
            return operator.or_(first_field, second_field)

        dfirst = first_field.expand_dims("place").assign_coords(place=[1])
        dsecond = second_field.expand_dims("place").assign_coords(place=[2])
        return xr.concat([dfirst, dsecond], dim="place").max(dim="place") > 0

    @staticmethod
    def and_operator(
        first_field: xr.DataArray | xr.Dataset, second_field: xr.DataArray | xr.Dataset
    ) -> bool:
        if first_field.count().equals(second_field.count()):
            return operator.and_(first_field, second_field)

        dfirst = first_field.expand_dims("place").assign_coords(place=[1])
        dsecond = second_field.expand_dims("place").assign_coords(place=[2])
        return (
            xr.concat([dfirst, dsecond], dim="place").fillna(0.0).min(dim="place") > 0.0
        )

    @staticmethod
    def apply(operators: List[LogicalOperator], elements: List[Any]) -> Any:
        """
        Performs the following operation:
        operators[n](element[n+1], operators[n-1](evt[n],... op[0](evt[1],evt[0])...))

        Args:
            operators: Operators to apply.
            elements: List of elements to apply given operators.

        Raises:
            ValueError: If the length of operators is not equal to len(elements) - 1.

        Returns:
            Any: Result of the operation.
        """
        if len(operators) + 1 != len(elements):
            raise ValueError(
                "Length of operands and operators are not compatible. Operand: "
                f"{len(elements)}, Operator: {len(operators)}. Operand should have a "
                f"length of {len(operators) + 1}."
            )
        result = elements[0]
        for op, element in zip(operators, elements[1:]):
            result = op(element, result)
        return result

    AND = ("and", and_operator)
    OR = ("or", or_operator)


class ComparisonOperator(Operator):
    """
    Comparison operator object.

    Inherits: Operator
    """

    SUP = ("sup", operator.gt)
    SUPEGAL = ("supegal", operator.ge)
    INF = ("inf", operator.lt)
    INFEGAL = ("infegal", operator.le)
    EGAL = ("egal", operator.eq)
    DIF = ("dif", operator.ne)
    ISIN = ("isin", lambda da, val_list: da.isin(val_list))
    NOT_ISIN = ("not_isin", lambda da, val_list: ~da.isin(val_list))

    @property
    def is_order(self):
        return self in [
            ComparisonOperator.SUP,
            ComparisonOperator.SUPEGAL,
            ComparisonOperator.INF,
            ComparisonOperator.INFEGAL,
        ]

    @property
    def is_increasing_order(self):
        return self in [ComparisonOperator.SUP, ComparisonOperator.SUPEGAL]

    @property
    def is_decreasing_order(self):
        return self in [ComparisonOperator.INF, ComparisonOperator.INFEGAL]

    @property
    def strict(self) -> ComparisonOperator:
        if self == ComparisonOperator.SUPEGAL:
            return ComparisonOperator.SUP
        if self == ComparisonOperator.INFEGAL:
            return ComparisonOperator.INF
        return self

    def critical_value(
        self, val: List | xr.DataArray | xr.Dataset, **kwargs
    ) -> float | xr.DataArray | xr.Dataset:
        if not self.is_order:
            return np.nan
        try:
            return val.max(**kwargs) if self.is_increasing_order else val.min(**kwargs)
        except AttributeError:
            return max(val) if self.is_increasing_order else min(val)
