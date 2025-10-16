"""Unit tests of wind direction classes."""

from typing import Optional

import numpy as np
import xarray as xr

from mfire.text.synthesis.wind_reducers.utils import add_previous_time_in_dataset


class CreateDataMixin:
    LON: list
    LAT: list

    @classmethod
    def _create_dataset(
        cls,
        valid_time: list | np.ndarray,
        data_wind: Optional[list | np.ndarray] = None,
        data_direction: Optional[list | np.ndarray] = None,
    ) -> xr.Dataset:
        # Create a WindSummaryBuilder's dataset.
        data_wind_rand: bool = False
        data_direction_rand: bool = False

        if data_wind is None:
            data_wind = np.random.uniform(
                low=1.0, high=30.0, size=(len(valid_time), len(cls.LAT), len(cls.LON))
            )
            data_wind_rand = True

        if data_direction is None:
            data_direction = np.random.uniform(
                low=1.0, high=30.0, size=(len(valid_time), len(cls.LAT), len(cls.LON))
            )
            data_direction_rand = True

        if len(cls.LON) == 1 and len(cls.LAT) == 1:
            if data_wind_rand is False:
                data_wind = [[[elt]] for elt in data_wind]
            if data_direction_rand is False:
                data_direction = [[[elt]] for elt in data_direction]

        dataset = xr.Dataset(
            {
                "wind": (["valid_time", "latitude", "longitude"], data_wind),
                "direction": (["valid_time", "latitude", "longitude"], data_direction),
            },
            coords={
                "id": "0",
                "valid_time": valid_time,
                "latitude": cls.LAT,
                "longitude": cls.LON,
                "areaType": "Axis",
                "areaName": "localisation 0",
            },
        )

        dataset = add_previous_time_in_dataset(dataset)
        dataset.attrs["points_nbr"] = len(cls.LAT) * len(cls.LON)

        return dataset


class Data1x1(CreateDataMixin):
    LON = [30]
    LAT = [40]


class Data1x2(CreateDataMixin):
    LON = [30, 31]
    LAT = [40]


class Data2x2(CreateDataMixin):
    LON = [30, 31]
    LAT = [40, 41]


class Data2x5(CreateDataMixin):
    LON = [30, 31, 32, 33, 34]
    LAT = [40, 41]
