from __future__ import annotations

import json
from datetime import datetime, timedelta
from io import IOBase
from pathlib import Path
from typing import IO, Any

import numpy as np
import pandas as pd
from pydantic import BaseModel
from shapely import Polygon
from shapely.geometry import mapping

from mfire.composite.serialized_types import (
    serialize_as_str,
    serialize_numpy_array,
    serialize_numpy_float,
    serialize_numpy_int,
    serialize_slice,
)
from mfire.utils import recursive_are_equals

Jsonable = (
    dict | list | tuple | str | int | float | bool | datetime | timedelta | BaseModel
)


def prepare_json(item):
    prepare = json.dumps(item, ensure_ascii=False, cls=MFireJSONEncoder, indent=0)
    return json.loads(prepare)


class MFireJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder made to easily encode types commonly used in MFire:
    - pydantic.BaseModel
    - datetime.datetime (and custom Datetime in extenso)
    - datetime.timedelta (and custom Timedelta in extenso)
    """

    ENCODINGS = {
        set: lambda x: sorted(x),
        np.integer: serialize_numpy_int,
        np.floating: serialize_numpy_float,
        np.ndarray: serialize_numpy_array,
        slice: serialize_slice,
        BaseModel: lambda x: json.loads(x.model_dump_json()),
        datetime | timedelta | np.datetime64 | np.timedelta64 | Path: serialize_as_str,
        (pd.DataFrame, pd.Series): lambda x: x.to_dict(),
        Polygon: mapping,
    }

    def default(self, o: Any) -> Any:
        for instance, function in self.ENCODINGS.items():
            if isinstance(o, instance):
                return function(o)
        return super().default(o)


class JsonFile:
    """Custom class for handling text or binary files containing JSON documents.

    This class provides methods for loading and potentially dumping JSON data.
    By default, it uses the built-in `json` module for handling JSON serialization
    and deserialization.
    """

    def __init__(self, file: str | Path | IO):
        self.file: str | Path | IO = file

    @staticmethod
    def loads(s: str, **kwargs) -> Any:
        """
        Loads JSON data from the given content and deserializes it to a Python object.

        Args:
            s: Content to deserialize
            **kwargs: Additional keyword arguments to be passed to the `json.load`
                    function.

        Returns:
            Any: The deserialized Python object from the given content.
        """

        return json.loads(s, **kwargs)

    def load(self, **kwargs: Any) -> Any:
        """
        Loads JSON data from the specified file and deserializes it to a Python object.

        This method opens the file (if a string path is provided) and uses the
        `json.load` function to deserialize the JSON content. You can optionally pass
        additional keyword arguments to the `json.load` function for customization.

        Args:
            **kwargs: Additional keyword arguments to be passed to the `json.load`
                    function.

        Returns:
            Any: The deserialized Python object from the JSON file.
        """

        if isinstance(self.file, IOBase):
            # File object already provided, use it directly
            return json.load(self.file, **kwargs)

        with open(self.file, "r") as fp:
            # Open the file for reading if a path is provided
            return json.load(fp, **kwargs)

    @staticmethod
    def dumps(obj: Any, **kwargs) -> str:
        """
        Serializes a Python object as JSON data and returns it.

        Args:
            obj: The Python object to be serialized as JSON.
            **kwargs: Additional keyword arguments to be passed to the `json.dumps`
                function. Common options include:
                    - `cls` (json.JSONEncoder, optional): Custom JSON encoder class.
                    - `indent`: Indentation for readability (default: 0).
                    - `ensure_ascii`: Escape non-ASCII characters (default:
                    False).

        Returns:
            Serialized object.
        """

        # Extract and remove commonly used keyword arguments for clarity
        encoder = kwargs.pop("cls", MFireJSONEncoder)  # Default to MFireJSONEncoder
        indent = kwargs.pop("indent", 0)
        ensure_ascii = kwargs.pop("ensure_ascii", False)

        return json.dumps(
            obj, ensure_ascii=ensure_ascii, cls=encoder, indent=indent, **kwargs
        )

    def dump(self, obj: Any, **kwargs):
        """
        Serializes a Python object (`obj`) as JSON data and writes it to the specified
        file.

        Args:
            obj: The Python object to be serialized as JSON.
            **kwargs: Additional keyword arguments to be passed to the `json.dumps`
                function. Common options include:
                    - `cls` (json.JSONEncoder, optional): Custom JSON encoder class.
                    - `indent`: Indentation for readability (default: 0).
                    - `ensure_ascii`: Escape non-ASCII characters (default:
                    False).
        """

        # Extract and remove commonly used keyword arguments for clarity
        encoder = kwargs.pop("cls", MFireJSONEncoder)  # Default to MFireJSONEncoder
        indent = kwargs.pop("indent", 0)
        ensure_ascii = kwargs.pop("ensure_ascii", False)

        if isinstance(self.file, IOBase):
            # File object already provided, write directly
            self.file.write(
                json.dumps(
                    obj, ensure_ascii=ensure_ascii, cls=encoder, indent=indent, **kwargs
                )
            )
        else:
            # Open the file for writing if a path is provided
            with open(self.file, "w") as fp:
                json.dump(
                    obj,
                    fp,
                    ensure_ascii=ensure_ascii,
                    cls=encoder,
                    indent=indent,
                    **kwargs,
                )

    def __eq__(self, other: JsonFile | str | Path) -> bool:
        """
        Compares this `JsonFile` object with another object.

        This method implements the equality operator for the `JsonFile` class. It
        delegates the comparison to the `is_equal_to` method for better encapsulation.

        Args:
            other: The object to compare with.

        Returns:
            True if the objects are equal, False otherwise.
        """

        return self.is_equal_to(other)

    def is_equal_to(self, other: JsonFile | Path, verbose: int = 2, **kwargs) -> bool:
        """
        Compares the differences between two JSON files and highlight the differences
        if needed.

        Args:
            other: Another JSON file.
            verbose: Level of description of the differences. Defaults to 2.
            **kwargs:: Keyword arguments.

        Returns:
            True if there are equals, False otherwise.
        """
        # Load JSON data from the left file
        with open(self.file) as lfp:
            left_dico = json.load(lfp)

        # Load JSON data from the right file
        other_filename = other.file if isinstance(other, JsonFile) else other
        with open(other_filename) as rfp:
            right_dico = json.load(rfp)

        # Compare the dictionaries and return the result
        return recursive_are_equals(
            left=left_dico, right=right_dico, verbose=verbose, **kwargs
        )
