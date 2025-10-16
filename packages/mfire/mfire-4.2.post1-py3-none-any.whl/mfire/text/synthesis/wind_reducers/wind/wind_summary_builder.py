from __future__ import annotations

from collections import OrderedDict
from functools import cached_property
from typing import Annotated, ClassVar, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import Field, SkipValidation

import mfire.utils.mfxarray as xr
from mfire.composite.component import SynthesisModule
from mfire.settings import get_logger
from mfire.text.synthesis.wind_reducers.base_param_summary_builder import (
    BaseParamSummaryBuilder,
)
from mfire.text.synthesis.wind_reducers.exceptions import (
    WindSynthesisError,
    WindSynthesisNotImplemented,
)
from mfire.text.synthesis.wind_reducers.mixins import BaseSummaryBuilderMixin
from mfire.text.synthesis.wind_reducers.utils import add_previous_time_in_dataset
from mfire.text.synthesis.wind_reducers.wind.utils import get_valid_time_of_wind_type
from mfire.text.synthesis.wind_reducers.wind.wind_intensity import WindIntensity
from mfire.utils.date import Datetime

from .case1 import Case1SummaryBuilder
from .case2 import Case2SummaryBuilder
from .case3 import Case3SummaryBuilder
from .wind_enum import WindCase, WindType

# Logging
LOGGER = get_logger(name=__name__, bind="wind")


class WindSummaryBuilder(BaseParamSummaryBuilder, BaseSummaryBuilderMixin):
    """WindSummaryBuilder class.

    This class is able to compute a summary from a Dataset which contains wind and
    direction data. This summary is a dictionary.
    """

    THRESHOLD_MINUS_NUM: ClassVar[np.float64] = np.float64(10)
    WF_PERCENTILE_NUM: ClassVar[int] = 95
    WF_TYPE2_DETECTION_PERCENT: ClassVar[int] = 5
    WF_TYPE3_DETECTION_PERCENT: ClassVar[int] = 5
    WF_TYPE3_CONFIRMATION_PERCENT: ClassVar[int] = 10
    WF_TYPE_SEPARATORS: ClassVar[list[float]] = [15.0, 25.0]
    CACHED_EXCEPTIONS: ClassVar[tuple[Exception]] = (
        pd.errors.EmptyDataError,
        ValueError,
        WindSynthesisError,
        WindSynthesisNotImplemented,
        AttributeError,
    )

    parent: Annotated[
        Optional[SynthesisModule], Field(exclude=True, repr=False), SkipValidation
    ] = None

    units: dict[str, str] = {}
    dataset: xr.Dataset

    def __init__(self, **data):
        # Call SummaryBuilderMixin.__init__ and create the summary attribute
        super().__init__(**data)

        # Get composite units
        self.units = self._get_units_of_param(self.parent)

        self.dataset = self.dataset[["wind", "direction"]]

        # Initialize the dataset's attributes:
        # - compute the number of grid's points
        # - set to 0 t2_percent_max_detection and t3_percent_max_detection
        self._initialize_dataset_attrs()

        # Get wind force data
        self._process_param_data(self.dataset, "wind", units=self.units["wind"])

        # Get wind direction data: 0 representing the North, they are replace by nan
        self._process_param_data(
            self.dataset,
            "direction",
            units=self.units["direction"],
            values_to_replace=[(0.0, np.nan)],
        )

        self._preprocess()

    @cached_property
    def mask(self) -> np.ndarray:
        # Get the mask. It comes only from the 1st term.
        return ~np.isnan(
            self.dataset.wind.sel(valid_time=self.dataset.valid_time[0]).values
        )

    @property
    def wind(self) -> xr.DataArray:
        return self.dataset.wind

    @property
    def direction(self) -> xr.DataArray:
        return self.dataset.direction

    @property
    def wind_type(self) -> xr.DataArray:
        return self.dataset.wind_type

    @property
    def fingerprint_raw(self) -> Optional[str]:
        # Get the raw fingerprint from the pandas summary.
        return "".join([str(wt) for wt in self.wind_type.values])

    @property
    def threshold(self) -> float:
        # Get the threshold from the dataset attributes.
        return self.dataset.attrs["threshold"]

    @property
    def case_family(self) -> WindCase:
        # Returns WindCase family depending on term types.
        wind_type_set: set = set(self.wind_type.values)

        if not wind_type_set or wind_type_set == {WindType.TYPE_1}:
            return WindCase.CASE_1

        if WindType.TYPE_3.value not in self.wind_type.values:
            return WindCase.CASE_2

        return WindCase.CASE_3

    def _get_units_of_param(self, compo: SynthesisModule) -> dict[str, str]:
        return {
            param_name: self._get_composite_units(compo, param_name)
            for param_name in ["wind", "direction"]
        }

    def _initialize_dataset_attrs(self) -> None:
        """Set the counter of grid's points in the attributes of dataset."""
        # We get the mask from only the first term
        self.dataset.attrs["points_nbr"] = int(np.count_nonzero(self.mask))

        # Then we initialize detection and confirmation max percents
        self.dataset.attrs["t2_percent_max_detection"] = 0.0
        self.dataset.attrs["t3_percent_max_detection"] = 0.0
        self.dataset.attrs["t3_percent_max_confirmation"] = 0.0

    def count_points(self, term_data: xr.DataArray, condition) -> Tuple[int, float]:
        # Count the points of a term regarding a particular condition.
        mask = term_data.where(condition)
        count: int = int(mask.count())

        if count == 0:
            return 0, 0
        percent: float = round(count * 100.0 / int(self.dataset.attrs["points_nbr"]), 1)

        return count, percent

    def _does_term_wind_force_data_match_input_conditions(
        self,
        term_wind_force_data: xr.DataArray,
        wind_force_bound: float,
        percent_min: float,
        attr: Optional[str] = None,
    ) -> bool:
        # Check if the input wind force data match input bound and percent. If
        # dataset_attr is given, then the related attribute of dataset is updated.

        # Get the percent of points with a wind force >= wind_force_bound km/h
        _, percent = self.count_points(
            term_wind_force_data, term_wind_force_data >= wind_force_bound
        )

        # Update percent_max in dataset.attrs if asked
        if attr:
            self.dataset.attrs[attr] = max(self.dataset.attrs[attr], percent)

        # If percent >= percent_min, then return True, else False
        if percent >= percent_min:
            return True
        return False

    def _get_term_type(self, term_wind_force_data: xr.DataArray):
        # Check if the current term is a type 3 ?
        if (
            self._does_term_wind_force_data_match_input_conditions(
                term_wind_force_data,
                self.WF_TYPE_SEPARATORS[1],
                self.WF_TYPE3_DETECTION_PERCENT,
                "t3_percent_max_detection",
            )
            is True
        ):
            return WindType.TYPE_3

        # Check if the current term is a type 2 ?
        if (
            self._does_term_wind_force_data_match_input_conditions(
                term_wind_force_data,
                self.WF_TYPE_SEPARATORS[0],
                self.WF_TYPE2_DETECTION_PERCENT,
                "t2_percent_max_detection",
            )
            is True
        ):
            return WindType.TYPE_2

        return WindType.TYPE_1

    def _preprocess(self):
        """Type terms and get the thresholds."""
        wfq_max: np.float64 = np.float64(0.0)
        valid_times: np.ndarray = self.dataset.valid_time.values

        # Initialize wind_type
        wind_type = np.array([], dtype=np.int32)

        for valid_time in valid_times:
            term_data_wf: xr.DataArray = self.wind.sel(valid_time=valid_time)

            # Type the term data, _get_term_type compute t3_percent_max_detection and
            # t2_percent_max_detection as well
            wind_type = np.concatenate(
                (wind_type, [self._get_term_type(term_data_wf).value])
            )

            # Compute the maximum of the terms Q95
            wfq: float = WindIntensity.data_array_to_value(term_data_wf)
            wfq_max = np.nanmax([wfq, wfq_max])

        # Add the `previous_time` variable
        self.dataset = add_previous_time_in_dataset(self.dataset)

        # Add the `wind_type` variable
        self.dataset["wind_type"] = xr.DataArray(
            data=wind_type, coords=[valid_times], dims=["valid_time"]
        )

        # Compute the accumulated threshold
        q_accumulated: np.float64 = (
            np.nanpercentile(self.wind.values, self.WF_PERCENTILE_NUM)
            - self.THRESHOLD_MINUS_NUM
        )
        self.dataset.attrs["threshold_accumulated"] = round(
            float(np.nanmax([q_accumulated, 0])), 1
        )

        # Compute the hours_max threshold
        self.dataset.attrs["threshold_hours_max"] = round(
            float(np.nanmax([wfq_max - self.THRESHOLD_MINUS_NUM, 0])), 1
        )

        # Set the threshold
        self.dataset.attrs["threshold"] = self.dataset.attrs["threshold_accumulated"]

        # Filter type 3 terms
        if WindType.TYPE_3.value in self.wind_type.values:
            self._filter_wind_type3_terms(self.threshold)

        # Add case_family in dataset's attributes
        self.dataset.attrs["case_family"] = self.case_family.value

        # Filter wind force and wind direction data if case 3
        if self.case_family == WindCase.CASE_3:
            self._filter_type3_data()

    def _filter_wind_type3_terms(self, lower_bound: float) -> int:
        # Set type 3 terms with not enough high wind points to type 2.
        type3_terms_cnt: int = 0
        t3_percent_max_conf: float = self.dataset.attrs["t3_percent_max_confirmation"]

        for valid_time in self.dataset.valid_time.values:
            if self.wind_type.sel(valid_time=valid_time) != WindType.TYPE_3.value:
                continue

            # Compute percent of points where the wind speed is >= lower_bound
            data_wf: xr.DataArray = self.wind.sel(valid_time=valid_time)
            _, percent = self.count_points(data_wf, data_wf >= lower_bound)

            # update t3_percent_max_confirmation
            t3_percent_max_conf = max(t3_percent_max_conf, percent)

            if percent < self.WF_TYPE3_CONFIRMATION_PERCENT:
                self.dataset.wind_type.loc[valid_time] = WindType.TYPE_2.value
            else:
                type3_terms_cnt += 1

        if type3_terms_cnt == 0:
            LOGGER.debug("All type 3 terms have been filtered")

        # Round t3_percent_max_confirmation
        self.dataset.attrs["t3_percent_max_confirmation"] = round(
            t3_percent_max_conf, 1
        )

        return type3_terms_cnt

    def _filter_type3_data(self) -> None:
        """Filter the wind and direction of the type 3 terms.

        We keep only wind and direction data when wind force >= threshold.
        """
        valid_time = get_valid_time_of_wind_type(self.dataset, WindType.TYPE_3)
        data = self.dataset.wind.sel(valid_time=valid_time)
        mask = xr.where(data >= self.threshold, True, False)
        self.dataset.wind.loc[{"valid_time": valid_time}] = xr.where(mask, data, np.nan)
        data = self.dataset.direction.sel(valid_time=valid_time)
        self.dataset.direction.loc[{"valid_time": valid_time}] = xr.where(
            mask, data, np.nan
        )

    def _get_sorted_dataset_attrs(self) -> OrderedDict:
        output: OrderedDict = OrderedDict(
            {
                attr: self.dataset.attrs.get(attr)
                for attr in (
                    "points_nbr",
                    "threshold_accumulated",
                    "threshold_hours_max",
                    "threshold",
                    "t2_percent_max_detection",
                    "t3_percent_max_detection",
                    "t3_percent_max_confirmation",
                    "case_family",
                    "case",
                )
            }
        )

        return output

    def _generate_summary(self, reference_datetime: Datetime) -> dict:
        case_family: WindCase = self.case_family

        # Case 1: there is only data_arrays with type 1
        if case_family == WindCase.CASE_1:
            self.summary = Case1SummaryBuilder().run()

        else:
            # Initialize summary
            self.summary = {"units": self.units["wind"]}
            sub_summary: dict

            # Case 2: there is only data_arrays with type 1 and type 2
            if case_family == WindCase.CASE_2:
                summary_builder: Case2SummaryBuilder = Case2SummaryBuilder(parent=self)
                sub_summary = summary_builder.run(self.dataset)

            # Case 3: there is data_arrays with type 3
            elif case_family == WindCase.CASE_3:
                summary_builder: Case3SummaryBuilder = Case3SummaryBuilder(parent=self)
                sub_summary = summary_builder.run(self.dataset, reference_datetime)

            else:
                raise ValueError(f"Bad case_family '{case_family}' !")

            self.summary.update(sub_summary)

        # Set the case in the dataset attributes
        self.dataset.attrs[self.TEMPLATE_KEY] = self.case

        return {"wind": self.summary}
