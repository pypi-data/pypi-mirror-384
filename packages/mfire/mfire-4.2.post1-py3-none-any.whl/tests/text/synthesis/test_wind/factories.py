from typing import Optional

import numpy as np

import mfire.utils.mfxarray as xr
from mfire.composite.component import SynthesisModule
from mfire.text.synthesis.wind_reducers.wind.wind_intensity import WindIntensity
from mfire.utils.date import Datetime
from tests.composite.factories import (
    BaseCompositeFactory,
    SynthesisComponentCompositeFactory,
    SynthesisModuleFactory,
)

from .utils import expand_array


class CompositeFactory2x2:
    """CompositeFactory2x2 class.

    Factory to create Wind Weather Composite with 2x2 grid data.
    """

    LON = [30, 31]
    LAT = [40, 41]
    RANDOM_BOUNDS = {"wind": (0.0, 100.0), "direction": (0.0, 90.0), "gust": (0, 100.0)}
    __UNITS_COMPO = [["wind", "km/h"], ["direction", "deg"], ["gust", "km/h"]]

    @classmethod
    def _update_units_dict(cls, units_dict: dict):
        for param, unit in cls.__UNITS_COMPO:
            if param not in units_dict:
                units_dict[param] = unit

    @classmethod
    def _get_random_data_for_param(cls, param_name, data_size) -> np.ndarray:
        return np.random.uniform(
            low=cls.RANDOM_BOUNDS[param_name][0],
            high=cls.RANDOM_BOUNDS[param_name][1],
            size=data_size,
        )

    @classmethod
    def _create_composite(
        cls,
        data: dict,
        valid_time: list,
        units_compo: dict,
        lon: list,
        lat: list,
        altitude: list,
        geos_descriptive: list,
        units_data: Optional[dict] = None,
    ) -> SynthesisModule:
        # Create a wind WeatherComposite by using WeatherCompositeFactory.

        units_data = units_compo if units_data is None else units_data
        data_vars = {}

        for param in data.keys():
            unit = units_data.get(param)

            param_data = [
                ["valid_time", "latitude", "longitude"],
                data[param],
                {"units": unit},
            ]

            data_vars[param] = tuple(param_data)

        data_vars["wwmf"] = xr.DataArray(
            [0, 0], coords={"valid_time": [Datetime(2023, 3, 1), Datetime(2023, 3, 2)]}
        )

        composite = SynthesisModuleFactory.create_factory(
            geos_descriptive=geos_descriptive,
            valid_time=valid_time,
            lon=lon,
            lat=lat,
            data_vars=data_vars,
            altitude=altitude,
            id="wind",
            units=units_compo,
            component=SynthesisComponentCompositeFactory(
                production_datetime=Datetime(2023, 1, 2)
            ),
        )

        return composite

    @classmethod
    def _data_to_ndarray(cls, data: list | np.ndarray):
        if isinstance(data, list):
            return np.array(data)
        return data

    @classmethod
    def get(
        cls,
        valid_time: list[np.datetime64] | np.ndarray,
        lon: Optional[list] = None,
        lat: Optional[list] = None,
        geos_descriptive: Optional[list] = None,
        altitude: Optional[list] = None,
        data_wind: Optional[list | np.ndarray] = None,
        data_dir: Optional[list | np.ndarray] = None,
        data_gust: Optional[list | np.ndarray] = None,
        units_compo: Optional[dict] = None,
        units_data: Optional[dict] = None,
    ):
        # Set longitude and latitude
        if lon is None:
            lon = cls.LON
        if lat is None:
            lat = cls.LAT

        # Set geo_descriptive
        if geos_descriptive is None:
            geos_descriptive = [[[1] * len(lon)] * len(lat)]

        # Set altitude
        if altitude is None:
            altitude = [[0] * len(lon)] * len(lat)

        # Set units_compo and units_data
        if units_compo is None:
            units_compo = {}
        cls._update_units_dict(units_compo)

        # Set units_data
        if units_data is None:
            units_data = {}
        cls._update_units_dict(units_data)

        data_size = (len(valid_time), len(lat), len(lon))

        # Set data
        if data_wind is None:
            data_wind = cls._get_random_data_for_param("wind", data_size)
        else:
            data_wind = expand_array(cls._data_to_ndarray(data_wind))

        if data_dir is None:
            data_dir = cls._get_random_data_for_param("direction", data_size)
        else:
            data_dir = expand_array(cls._data_to_ndarray(data_dir))

        if data_gust is None:
            data_gust = cls._get_random_data_for_param("gust", data_size)
        else:
            data_gust = expand_array(cls._data_to_ndarray(data_gust))

        data = {"wind": data_wind, "direction": data_dir, "gust": data_gust}

        return cls._create_composite(
            data,
            valid_time,
            units_compo,
            lon,
            lat,
            altitude,
            geos_descriptive,
            units_data,
        )

    @classmethod
    def _extend_data_list(cls, data_list: Optional[list], size: int) -> list:
        # Extend data to feet it with the created composite dataset.
        if data_list is None:
            data_list = [0] * size
        return [[[elt]] for elt in data_list]  # extend the data


class CompositeFactory2x2Type1(CompositeFactory2x2):
    RANDOM_BOUNDS = {"wind": (0.0, 15.0), "direction": (0.0, 90.0), "gust": (0, 100.0)}


class CompositeFactory1x1(CompositeFactory2x2):
    """Composite factory which generates grid with 1x1 size."""

    LON = [30]
    LAT = [40]

    @classmethod
    def get_composite_when_term_data_is_one_number(
        cls,
        valid_time: list[np.datetime64] | np.ndarray,
        lon: Optional[list] = None,
        lat: Optional[list] = None,
        geos_descriptive: Optional[list] = None,
        altitude: Optional[list] = None,
        data_wind: Optional[list | np.ndarray] = None,
        data_dir: Optional[list | np.ndarray] = None,
        data_gust: Optional[list | np.ndarray] = None,
        units_compo: Optional[dict] = None,
        units_data: Optional[dict] = None,
    ):
        # Get a composite when the is one number for each data terms.

        # Get data size
        data_size: int = 0
        for data in [data_wind, data_dir, data_gust]:
            if data is not None:
                data_size_tmp = len(data)
                if data_size and data_size != data_size_tmp:
                    raise ValueError(
                        f"Sizes of data_wind, data_dir and data_gust mismatch: "
                        f"{data_size_tmp} != {data_size}"
                    )
                data_size = data_size_tmp

        return cls.get(
            valid_time,
            lon,
            lat,
            geos_descriptive,
            altitude,
            cls._extend_data_list(data_wind, data_size),
            cls._extend_data_list(data_dir, data_size),
            cls._extend_data_list(data_gust, data_size),
            units_compo,
            units_data,
        )


class CompositeFactory3x2(CompositeFactory2x2):
    """Composite factory which generates grid with 5x2 size."""

    LON = [30, 31, 32]
    LAT = [40, 41]


class CompositeFactory5x2(CompositeFactory2x2):
    """Composite factory which generates grid with 5x2 size."""

    LON = [30, 31]
    LAT = [40, 41, 42, 43, 44]


class CompositeFactory6x2(CompositeFactory2x2):
    """Composite factory which generates grid with 6x2 size."""

    LON = [30, 31]
    LAT = [40, 41, 42, 43, 44, 45]


class CompositeFactory6x4(CompositeFactory2x2):
    """Composite factory which generates grid with 6x4 size."""

    LON = [30, 31, 32, 33]
    LAT = [40, 41, 42, 43, 44, 45]


class CompositeFactory1x100(CompositeFactory2x2):
    """Composite factory which generates grid with 1x100 size."""

    LON = list(range(0, 100))
    LAT = [30]


class CompositeFactory1x2(CompositeFactory2x2):
    """Composite factory which generates grid with 1x100 size."""

    LON = [30, 31]
    LAT = [40]


class CompositeFactory1x7(CompositeFactory2x2):
    """Composite factory which generates grid with 1x100 size."""

    LON = [30, 31, 32, 33, 34, 35, 38]
    LAT = [40]


class WindIntensityFactory(WindIntensity, BaseCompositeFactory):
    pass
