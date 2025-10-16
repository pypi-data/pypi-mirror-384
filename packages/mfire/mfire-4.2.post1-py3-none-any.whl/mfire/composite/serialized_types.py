"""This submodule serializing methods and serialized types.

They can be used to serialize pydantic.BaseModel inherited classes or to build JSON
encoders.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Any

import numpy as np
from pydantic import PlainSerializer


def serialize_numpy_int(numpy_int: np.integer) -> int:
    return int(numpy_int)


def serialize_numpy_float(numpy_float: np.floating) -> float:
    return float(numpy_float)


def serialize_numpy_array(numpy_array: np.ndarray) -> list:
    return numpy_array.tolist()


def numpy_datetime64_serializer(np_date: np.datetime64) -> str:
    """
    Serialize numpy_datetime64 as string.

    Args:
        np_date: Numpy datetime to serialize.

    Returns:
        Serialized datetime as string.
    """
    return np.datetime_as_string(np_date, unit="s")


def serialize_slice_elt(elt: Any) -> Any:
    if isinstance(elt, np.datetime64):
        return numpy_datetime64_serializer(elt)
    return elt


def serialize_slice(input_slice: slice) -> list:
    return [
        serialize_slice_elt(b)
        for b in [input_slice.start, input_slice.stop, input_slice.step]
        if b is not None
    ]


def serialize_as_str(
    elt: datetime | timedelta | np.datetime64 | np.timedelta64 | Path,
) -> str:
    return str(elt)


def serialize_threshold(threshold: int | bool | float | str | list[int | float | str]):
    if isinstance(threshold, bool):
        return int(threshold)

    if isinstance(threshold, (float, int)):
        return threshold

    if isinstance(threshold, str):
        tmp_float: float = float(threshold)
        tmp_int: int = int(threshold)
        return tmp_int if tmp_int == tmp_float else tmp_float

    if isinstance(threshold, list):
        for i, elt in enumerate(threshold):
            if isinstance(elt, (float, int)):
                threshold[i] = elt
            elif isinstance(elt, str):
                threshold[i] = serialize_threshold(elt)
            else:
                raise TypeError(f"Bad type found: {type(elt)}")

    else:
        raise TypeError(f"Bad type found: {type(threshold)}")

    return threshold


s_np_int32 = Annotated[np.int32, PlainSerializer(serialize_numpy_int, return_type=int)]

s_np_int64 = Annotated[np.int64, PlainSerializer(serialize_numpy_int, return_type=int)]

s_np_float32 = Annotated[
    np.float32, PlainSerializer(serialize_numpy_float, return_type=float)
]

s_np_float64 = Annotated[
    np.float64, PlainSerializer(serialize_numpy_float, return_type=float)
]

s_np_array = Annotated[
    np.ndarray, PlainSerializer(serialize_numpy_array, return_type=np.ndarray)
]

s_slice = Annotated[slice, PlainSerializer(serialize_slice, return_type=list)]


s_datetime = Annotated[datetime, PlainSerializer(serialize_as_str, return_type=str)]

s_timedelta = Annotated[timedelta, PlainSerializer(serialize_as_str, return_type=str)]

s_np_datetime64 = Annotated[
    np.datetime64, PlainSerializer(numpy_datetime64_serializer, return_type=str)
]

s_np_timedelta64 = Annotated[
    np.timedelta64, PlainSerializer(serialize_as_str, return_type=str)
]

s_path = Annotated[Path, PlainSerializer(serialize_as_str, return_type=str)]

s_threshold = Annotated[
    int | bool | float | str | list[int | float | str],
    PlainSerializer(
        serialize_threshold, return_type=int | float | str | list[int | float | str]
    ),
]
