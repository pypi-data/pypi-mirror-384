import numpy as np
import xarray as xr

from mfire.settings import get_logger

# Logging
LOGGER = get_logger(name=__name__, bind="reducers_utils")


def initialize_previous_time(valid_time: np.ndarray[np.datetime64]) -> np.datetime64:
    if len(valid_time) > 1:
        return valid_time[0] - (valid_time[1] - valid_time[0])

    LOGGER.warning("There is only one valid_time to compute wind text.")
    return valid_time[0] - np.timedelta64(1, "h")


def add_previous_time_in_dataset(dataset: xr.Dataset) -> xr.Dataset:
    dataset["previous_time"] = xr.DataArray(
        data=np.concatenate(
            (
                np.array([initialize_previous_time(dataset.valid_time.values)]),
                dataset.valid_time.values[:-1],
            )
        ),
        coords=[dataset.valid_time.values],
        dims=["valid_time"],
    )

    return dataset
