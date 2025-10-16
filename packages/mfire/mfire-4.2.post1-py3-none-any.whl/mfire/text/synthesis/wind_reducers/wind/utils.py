import xarray as xr

from .wind_enum import WindType


def get_valid_time_of_wind_type(
    dataset: xr.Dataset, wind_type: WindType
) -> xr.DataArray:
    # Get valid_time array matching with a given WindType.
    data = dataset.wind_type.where(dataset.wind_type == wind_type.value).dropna(
        dim="valid_time"
    )
    return data.valid_time


def get_valid_time_excluding_wind_type(
    dataset: xr.Dataset, wind_type: WindType
) -> xr.DataArray:
    # Get valid_time array excluding with a given WindType.
    data = dataset.wind_type.where(dataset.wind_type != wind_type.value).dropna(
        dim="valid_time"
    )
    return data.valid_time


def filter_dataset_from_wind_type(
    dataset: xr.Dataset, wind_type: WindType
) -> xr.Dataset:
    # Filter the input dataset by keeping only terms which have a given WindType.
    valid_time: xr.DataArray = get_valid_time_of_wind_type(dataset, wind_type)

    return dataset.sel(valid_time=valid_time)


def filter_dataset_excluding_wind_type(
    dataset: xr.Dataset, wind_type: WindType
) -> xr.Dataset:
    # Filter the input dataset by excluding all terms which have a given WindType.
    valid_time: xr.DataArray = get_valid_time_excluding_wind_type(dataset, wind_type)

    return dataset.sel(valid_time=valid_time)
