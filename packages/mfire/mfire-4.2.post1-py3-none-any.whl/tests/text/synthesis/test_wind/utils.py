from typing import Optional

import numpy as np

import mfire.utils.mfxarray as xr
from mfire.text.synthesis.wind_reducers.wind import WindSummaryBuilder


def expand_array(array: np.ndarray, geos_desc_size: Optional[int] = None) -> np.ndarray:
    # Expand a numpy array to fit with dims of composite datasets.
    size = []
    if geos_desc_size:
        size.append(geos_desc_size)
    size.extend([1, 1, 1])
    return np.tile(array, tuple(size))


def array_from_list(data: list, geos_desc_size: Optional[int] = None):
    array: np.ndarray = np.array(data)
    return expand_array(array, geos_desc_size)


def create_dataset(
    data: list | np.ndarray, valid_time: list | np.ndarray, lon: list, lat: list
) -> xr.DataArray:
    # Create a DataArray of wind param.
    # The generated DataArray looks like GustSummaryBuilder.data or
    # WindSummaryBuilder.data_wf or WindSummaryBuilder.data_wd attribute after when
    # the summary builder instance has been created.
    data_array: xr.DataArray = xr.DataArray(
        data,
        coords={
            "id": "0",
            "valid_time": valid_time,
            "latitude": lat,
            "longitude": lon,
            "areaType": "Axis",
            "areaName": "localisation 0",
        },
        dims=["valid_time", "latitude", "longitude"],
    )

    return data_array


def compute_threshold_accumulated(arrays_list) -> float:
    arrays = []

    for array in arrays_list:
        if isinstance(array, list):
            ndarray = np.array(array)
        elif isinstance(array, np.ndarray):
            ndarray = array
        else:
            raise TypeError

        ndarray[np.isnan(ndarray)] = 0.0
        arrays.append(ndarray)

    concatenation = np.concatenate(arrays, axis=None)

    res = np.percentile(concatenation, WindSummaryBuilder.WF_PERCENTILE_NUM) - 10

    return round(float(res), 1)


def compute_threshold_hours_max(arrays_list, terms_nbr: int):
    res = []

    if terms_nbr == 1:
        arrays_list = [arrays_list]

    for array in arrays_list:
        if isinstance(array, list):
            ndarray = np.array(array)
        elif isinstance(array, np.ndarray):
            ndarray = np.array(array)
        else:
            raise TypeError

        ndarray[np.isnan(ndarray)] = 0.0

        res.append(np.percentile(ndarray, WindSummaryBuilder.WF_PERCENTILE_NUM) - 10)

    return round(float(max(res)), 1)
