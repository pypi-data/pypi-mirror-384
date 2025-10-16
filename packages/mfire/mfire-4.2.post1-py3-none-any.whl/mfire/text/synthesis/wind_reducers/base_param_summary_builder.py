import traceback
from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

import mfire.utils.mfxarray as xr
from mfire.composite.component import SynthesisModule
from mfire.settings import TEXT_ALGO, get_logger
from mfire.utils.date import Datetime
from mfire.utils.unit_converter import unit_conversion

# Logging
LOGGER = get_logger(name=__name__, bind="wind")


class BaseParamSummaryBuilder(ABC):
    """BaseParamSummaryBuilder."""

    CACHED_EXCEPTIONS: tuple[Exception]
    USED_DIMS: list = ["valid_time", "latitude", "longitude"]

    @staticmethod
    def _get_composite_units(compo: SynthesisModule, param_name: str) -> str:
        # Get the units of the param regarding the WeatherComposite.
        return compo.units.get(
            param_name,
            TEXT_ALGO[compo.id][compo.algorithm]["params"][param_name]["default_units"],
        )

    @staticmethod
    def _process_param_data(dataset: xr.Dataset, data_var: str, **kwargs) -> xr.Dataset:
        # Process the dataArray matching with the input data_var.

        # Get kwargs
        units: Optional[str] = kwargs.get("units")
        nan_replace: Optional[float] = kwargs.get("nan_replace")
        values_to_replace: Optional[list[tuple[float, float]]] = kwargs.get(
            "values_to_replace"
        )
        decimals: Optional[int] = kwargs.get("decimals")

        # Get the dataArray
        data_array = dataset[data_var]

        # Replace nan if necessary
        if nan_replace is not None:
            data_array = data_array.fillna(nan_replace)

        # Replace values if necessary
        if values_to_replace is not None:
            for value_old, value_new in values_to_replace:
                data_array = data_array.where(data_array != value_old, value_new)

        # Convert the data if asked
        if units is not None:
            data_array = unit_conversion(data_array, units)

        # Round if asked
        if decimals is not None:
            data_array = np.round(data_array, decimals=decimals)

        dataset[data_var] = data_array

        return dataset

    @staticmethod
    def _get_data_array(
        dataset: xr.Dataset,
        param_name: str,
        units: Optional[str] = None,
        nan_replace: Optional[float] = None,
        values_to_replace: Optional[list[tuple[float, float]]] = None,
    ) -> xr.DataArray:
        # Extract, clean and convert the dataArray matching the param_name var.

        # Get the data
        data_array = dataset[param_name]

        # Replace nan if necessary
        if nan_replace is not None:
            data_array = data_array.fillna(nan_replace)

        # Replace values if necessary
        if values_to_replace is not None:
            for value_old, value_new in values_to_replace:
                data_array = data_array.where(data_array != value_old, value_new)

        # Convert the data if asked
        if units:
            data_array = unit_conversion(data_array, units)

        return data_array

    @abstractmethod
    def _generate_summary(self, reference_datetime: Datetime) -> dict:
        pass

    def compute(self, reference_datetime: Datetime) -> dict:
        try:
            return self._generate_summary(reference_datetime)
        except self.CACHED_EXCEPTIONS as exp:
            msg: str = (
                f"{exp.__class__.__name__}: problem detected in "
                f"{self.__class__.__name__} -> {traceback.format_exc()}"
            )
            LOGGER.error(msg)
            raise exp
