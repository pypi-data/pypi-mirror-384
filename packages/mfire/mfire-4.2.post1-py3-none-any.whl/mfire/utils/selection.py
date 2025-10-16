from __future__ import annotations

from itertools import combinations
from typing import Iterable, Optional

import numpy as np
from pydantic import field_validator, model_validator

import mfire.utils.mfxarray as xr
from mfire.composite.base import BaseModel
from mfire.composite.serialized_types import s_slice
from mfire.settings import get_logger
from mfire.utils.date import Datetime

# Logging
LOGGER = get_logger(name="composite.fields.mod", bind="composite.fields")


class Selection(BaseModel):
    sel: Optional[dict] = {}
    slice: Optional[dict[str, s_slice | float]] = {}
    isel: Optional[dict] = {}
    islice: Optional[dict[str, s_slice]] = {}

    @model_validator(mode="before")
    def check_all_keys(cls, values: dict):
        """
        Validates that all keys are present in the Selection object.

        Args:
            values: Input dictionary of values.

        Returns:
            Updated dictionary of values.

        Raises:
            ValueError: Raised when same keys were found.
        """
        set_sel = set(values.get("sel", {}))
        set_slice = set(values.get("slice", {}))
        set_isel = set(values.get("isel", {}))
        set_islice = set(values.get("islice", {}))

        if any(
            set_1.intersection(set_2)
            for set_1, set_2 in combinations(
                [set_sel, set_slice, set_isel, set_islice], r=2
            )
        ):
            raise ValueError("Same keys are found!")

        return values

    @field_validator("sel", mode="before")
    def check_valid_time(cls, value: dict) -> dict:
        """
        Checks and converts valid_time values to np.datetime64 format.

        Args:
            value: Input dictionary of values.

        Returns:
            dict: Updated dictionary of values.
        """
        if isinstance(value.get("valid_time"), Iterable):
            value["valid_time"] = cls.date_times_as_np_date_times(value["valid_time"])
        return value

    @field_validator("slice", "islice", mode="before")
    def init_slices(cls, value: dict) -> dict:
        """
        Checks and converts valid_time values to np.datetime64 format.

        Args:
            value: Input dictionary of values.

        Returns:
            dict: Updated dictionary of values.
        """
        if isinstance(value.get("valid_time"), Iterable):
            value["valid_time"] = slice(
                *cls.date_times_as_np_date_times(value["valid_time"])
            )

        return {
            k: slice(*v) if isinstance(v, Iterable) else v for k, v in value.items()
        }

    @classmethod
    def date_times_as_np_date_times(
        cls, date_times: list[Datetime | np.datetime64]
    ) -> list:
        return [
            Datetime(dt).as_np_dt64
            for dt in date_times
            if isinstance(dt, np.datetime64) is False
        ]

    def select(self, da: xr.DataArray) -> xr.DataArray:
        """
        Selects the data based on the defined indices and slices.

        Args:
            da: Input DataArray.

        Returns:
            xr.DataArray: Selected data.
        """
        return da.isel(**self.isel, **self.islice).sel(**self.sel, **self.slice)

    @property
    def all(self) -> dict:
        """
        Returns a dictionary containing all the selection criteria.

        Returns:
            dict: All selection criteria.
        """
        return {**self.sel, **self.slice, **self.isel, **self.islice}

    def update(self, new_sel: dict, new_slice: dict, new_isel: dict, new_islice: dict):
        """
        Updates the current selection criteria with new ones.

        Args:
            new_sel: Dictionary of selection criteria.
            new_slice: Dictionary of slice criteria.
            new_isel: Dictionary of isel criteria. Defaults to None.
            new_islice: Dictionary of islice criteria. Defaults to {}.
        """
        # creating new selection
        new_sel = Selection(
            new_sel=new_sel,
            new_slice=new_slice,
            new_isel=new_isel,
            new_islice=new_islice,
        )

        self.sel.update(new_sel.sel)
        self.slice.update(new_sel.slice)
        self.isel.update(new_sel.isel)
        self.islice.update(new_sel.islice)
