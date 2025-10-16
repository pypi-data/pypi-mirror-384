from typing import List

import numpy as np

import mfire.utils.mfxarray as xr
from mfire.composite.base import BaseModel
from mfire.settings import get_logger

# Logging
LOGGER = get_logger(name="temporal_localisation.mod", bind="temporal_localisation")


class TemporalLocalisation(BaseModel):
    data: xr.DataArray

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        times = self.data.sum("id").mask.f32.dropna("valid_time").valid_time
        self.data = self.data.sel(
            {"valid_time": slice(times.min(), times.max())}
        ).astype("float32")

    @staticmethod
    def period_summary(data: xr.DataArray) -> xr.Dataset:
        """
        Summarize information for the period by taking the maximum over the period as
        the value and renaming with the period bounds.

        Args:
            data: Data to summarize.

        Returns:
            xr.Dataset: The summary of the data.
        """
        period_name = (
            data.valid_time[0].dt.strftime("%Y%m%dT%H").data
            + "_to_"
            + data.valid_time[-1].dt.strftime("%Y%m%dT%H").data
        )
        return (
            data.max("valid_time")
            .to_dataset(name="elt")
            .expand_dims("period")
            .assign_coords(period=[period_name])
        )

    @property
    def two_colums(self) -> List:
        """
        Tries to split the data into two columns.

        Returns:
            A list of date representing the split.
        """

        # Compute the number of hours in the data
        min_time = np.datetime64(self.data.valid_time.min().data)
        max_time = np.datetime64(self.data.valid_time.max().data)
        nb_hour = int((max_time - min_time) / np.timedelta64(1, "h"))

        # Initialize the minimum error and the selected bounds
        min_error, selected_bound = np.inf, [min_time, max_time]

        # Iterate over the possible bounds
        for x in range(2, nb_hour - 2):
            # Compute the error for the current bounds
            bound = min_time + np.timedelta64(x, "h")
            tab1 = self.data.sel({"valid_time": slice(min_time, bound)})
            tab2 = self.data.sel(
                {"valid_time": slice(bound + np.timedelta64(1, "h"), max_time)}
            )
            error = ((tab1 - tab1.max("valid_time")) ** 2).sum() + (
                (tab2 - tab2.max("valid_time")) ** 2
            ).sum()

            # If the current error is smaller than the minimum error, update the minimum
            # error and the selected bounds
            if error < min_error:
                min_error = error
                selected_bound = [min_time, bound, max_time]
        return selected_bound

    @property
    def three_columns(self) -> List:
        """
        Tries to split the data into three columns.

        Returns:
            A list of date representing the bounds in hours.
        """

        # Compute the number of hours in the data
        min_time = np.datetime64(self.data.valid_time.min().data)
        max_time = np.datetime64(self.data.valid_time.max().data)
        nb_hour = int((max_time - min_time) / np.timedelta64(1, "h"))

        # Initialize the minimum error and the selected bounds
        min_error, selected_bounds = np.inf, [min_time, max_time]
        for x in range(2, nb_hour - 5):
            bound1 = min_time + np.timedelta64(x, "h")
            tab1 = self.data.sel({"valid_time": slice(min_time, bound1)})
            error1 = ((tab1 - tab1.max("valid_time")) ** 2).sum()
            for y in range(x + 3, nb_hour - 2):
                # Compute the error for the current bounds
                bound2 = min_time + np.timedelta64(y, "h")
                tab2 = self.data.sel(
                    {"valid_time": slice(bound1 + np.timedelta64(1, "h"), bound2)}
                )
                tab3 = self.data.sel(
                    {"valid_time": slice(bound2 + np.timedelta64(1, "h"), max_time)}
                )
                error = (
                    error1
                    + ((tab2 - tab2.max("valid_time")) ** 2).sum()
                    + ((tab3 - tab3.max("valid_time")) ** 2).sum()
                )

                # If the current error is smaller than the minimum error, update the
                # minimum error and the selected bounds
                if error < min_error:
                    min_error = error
                    selected_bounds = [min_time, bound1, bound2, max_time]
        return selected_bounds

    def compute(self) -> xr.DataArray:
        """
        Computes a new DataArray with a finer temporal resolution.

        The new DataArray is created by splitting the original DataArray into multiple
        columns, based on the number of hours in the data.

        Returns:
            xr.DataArray: New DataArray with a finer temporal resolution.
        """

        # Compute the number of hours in the data
        min_time = self.data.valid_time.min()
        max_time = self.data.valid_time.max()
        delta = max_time - min_time
        nb_hour = int(delta / np.timedelta64(1, "h")) + 1

        # Define the bounds for the new DataArray
        bounds = self.three_columns if nb_hour >= 9 else self.two_colums

        # Compute the summaries for each column
        summary = [
            self.period_summary(
                self.data.sel(
                    {"valid_time": slice(bound + int(idx > 0), bounds[idx + 1])}
                )
            )
            for idx, bound in enumerate(bounds[:-1])
        ]

        # Merge the summaries into a single DataArray and return the `elt` variable
        # from the merged DataArray.
        return xr.merge(summary)["elt"]
