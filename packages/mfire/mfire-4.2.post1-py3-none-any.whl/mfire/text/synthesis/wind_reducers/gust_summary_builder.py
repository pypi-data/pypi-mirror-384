from functools import cached_property
from typing import Annotated, ClassVar, Optional

import numpy as np
from pydantic import Field, SkipValidation

import mfire.utils.mfxarray as xr
from mfire.composite.component import SynthesisModule
from mfire.settings import get_logger
from mfire.text.risk.rep_value import FFRafRepValueReducer
from mfire.text.synthesis.wind_reducers.base_param_summary_builder import (
    BaseParamSummaryBuilder,
)
from mfire.text.synthesis.wind_reducers.exceptions import WindSynthesisError
from mfire.text.synthesis.wind_reducers.mixins import BaseSummaryBuilderMixin
from mfire.text.synthesis.wind_reducers.utils import add_previous_time_in_dataset
from mfire.utils.calc import round_to_closest_multiple
from mfire.utils.date import Datetime
from mfire.utils.period import Period

# Logging
LOGGER = get_logger(name=__name__, bind="gust")


class GustSummaryBuilder(BaseParamSummaryBuilder, BaseSummaryBuilderMixin):
    FORCE_MIN: ClassVar[float] = 50.0
    PARAM_NAME: ClassVar[str] = "gust"
    INTERVAL_PERCENT: ClassVar[float] = 20.0
    INTERVAL_SIZE: ClassVar[int] = 20
    PERCENTILE_NUM: ClassVar[int] = 90
    CACHED_EXCEPTIONS: ClassVar[tuple[Exception]] = (
        WindSynthesisError,
        KeyError,
        ValueError,
    )
    HAZARD_NAMES: ClassVar[list[str]] = ["Vent", "Rafales"]
    FIELD_NAME: ClassVar[str] = "RAF__HAUTEUR10"

    parent: Annotated[
        Optional[SynthesisModule], Field(exclude=True, repr=False), SkipValidation
    ] = None

    dataset: xr.Dataset

    def __init__(self, **data):
        # Call SummaryBuilderMixin.__init__ and create the summary attribute
        super().__init__(**data)

        # Get gust data: nan values will be kept
        self.dataset: xr.Dataset = self.dataset[["gust"]]

        self._process_param_data(self.dataset, "gust", units=self.units)

        # Add the `previous_time` variable in dataset
        self.dataset = add_previous_time_in_dataset(self.dataset)

        # Get risk infos
        self._adapt_pm_sep()
        self._update_dataset_attrs()

    @cached_property
    def units(self) -> dict[str, str]:
        return self._get_composite_units(self.parent, self.PARAM_NAME)

    @cached_property
    def risk_infos(self) -> dict[str, float | int | bool | str]:
        return self._get_risk_infos(self.parent)

    @property
    def gust_da(self) -> xr.DataArray:
        return self.dataset.gust

    @cached_property
    def gust_max_da(self) -> xr.DataArray:
        # Get the gust max DataArray along the valid_time dim.
        return self.dataset.gust.max(dim="valid_time")

    @property
    def gust_max_raw(self) -> float:
        return float(np.round(self.gust_max_da.max(), decimals=2))

    @cached_property
    def sg_max(self) -> int:
        # Compute the representative value of synthesis gust max.
        # If gust max raw is nan, return 0
        if np.isnan(self.gust_max_raw):
            return 0

        # Keep only points where gust max > 50
        data_array = self.gust_max_da.where(self.gust_max_da > self.FORCE_MIN)

        if np.isnan(data_array).all():
            return 0

        # Compute the 90th percentile of max gust > 50
        q90: float = round(np.nanpercentile(data_array, 90), 2)

        return round_to_closest_multiple(q90, 10, cast_type=int)

    def _get_risk_infos(
        self, compo: SynthesisModule
    ) -> dict[str, float | int | bool | str]:
        # Get risk_infos of from the composite interface.
        return compo.interface.get_risk_infos(
            self.HAZARD_NAMES,
            self.FIELD_NAME,
            str(self.dataset.id.values),
            slice(
                self.dataset.valid_time.values[0], self.dataset.valid_time.values[-1]
            ),
            ["max"],
        )

    def _adapt_pm_sep(self) -> None:
        """Set pm_sep to False is the max is reached in plain and mountain."""
        if len(self.max_values) == 2 and (
            FFRafRepValueReducer.interval_rep(self.max_values[0])
            == FFRafRepValueReducer.interval_rep(self.max_values[1])
        ):
            self.risk_infos["pm_sep"] = False

    def _set_zone_max(self, rg_max_key: str):
        keys: tuple = "zone", "zone_c"
        values: tuple = self._("en plaine"), self._("sur les hauteurs")

        if self.pm_separation is True:
            if "plain" in rg_max_key:
                self.risk_infos.update(dict(zip(keys, values)))
            else:
                self.risk_infos.update(dict(zip(keys, tuple(reversed(values)))))

    @cached_property
    def max_values(self) -> list[float]:
        return [
            self.risk_infos.get(k)
            for k in ["plain_max", "mountain_max"]
            if self.risk_infos.get(k) is not None
        ]

    @cached_property
    def rg_max(self) -> Optional[int]:
        # Compute the maximum of the risk gust.
        if self.max_values:
            # Get the maximum value
            rg_max_value: float = max(self.max_values)

            # Else, set the zone
            if self.pm_separation is True:
                rg_max_key: str = (
                    "plain_max"
                    if self.risk_infos.get("plain_max") == rg_max_value
                    else "mountain_max"
                )
                self._set_zone_max(rg_max_key)

            if self.risk_infos.get("activated_risk") is True:
                return FFRafRepValueReducer.interval_rep(rg_max_value)[1]

            return round_to_closest_multiple(
                rg_max_value, FFRafRepValueReducer.interval_size, cast_type=int
            )

        return None

    @cached_property
    def mask(self) -> np.ndarray:
        # Get the mask. It comes only from the 1st term.
        return ~np.isnan(
            self.dataset.gust.sel(valid_time=self.dataset.valid_time[0]).values
        )

    @cached_property
    def points_nbr(self) -> int:
        # Compute the number of masked points.
        return np.count_nonzero(self.mask)

    @property
    def pm_separation(self) -> bool:
        # Allow to know if there is a separation between the plain and the mountain.
        return self.risk_infos.get("pm_sep", False)

    def _update_dataset_attrs(self) -> None:
        self.dataset.attrs["points_nbr"] = self.points_nbr
        self.dataset.attrs["gust_max_raw"] = self.gust_max_raw
        self.dataset.attrs["sg_max"] = self.sg_max
        self.dataset.attrs["rg_max"] = self.rg_max

    def count_points(self, term_data: xr.DataArray, condition) -> tuple[int, float]:
        # Count the points of a term regarding a particular condition.
        mask = term_data.where(condition)
        count: int = int(mask.count())

        if count == 0:
            return 0, 0

        return count, round(count * 100.0 / int(self.points_nbr), 1)

    def compute_percent_coverage_of_interval(
        self, bound_inf: float, bound_sup: float
    ) -> float:
        _, percent = self.count_points(
            self.gust_max_da,
            (self.gust_max_da >= bound_inf) & (self.gust_max_da <= bound_sup),
        )
        return percent

    def _initialize_bound_inf(self) -> Optional[int]:
        # If sg_max is nan or is <= 50 km/h, it means that there is no gust to
        # describe, so no bound_inf
        if self.sg_max <= self.FORCE_MIN:
            return None

        if self.sg_max <= self.FORCE_MIN + self.INTERVAL_SIZE:
            return int(self.FORCE_MIN)

        return self.sg_max - self.INTERVAL_SIZE

    def _sg_max_descriptors(self, reference_datetime: Datetime) -> str:
        # Find the best interval containing sg_max
        bound_inf_init: Optional[int] = self._initialize_bound_inf()
        case: str = ""

        # If interval not found, meaning sg_max is nan or <= 50 km/h, this is
        # the case 0
        if bound_inf_init is None:
            return "0"

        bound_inf: int = bound_inf_init
        bound_sup: int = bound_inf + self.INTERVAL_SIZE

        while bound_inf >= self.FORCE_MIN:
            percent: float = self.compute_percent_coverage_of_interval(
                bound_inf, bound_sup
            )

            if percent >= self.INTERVAL_PERCENT:
                if bound_inf == bound_inf_init:
                    case = "1"
                else:
                    case = "2"
                self.summary.update({"bound_inf": bound_inf, "bound_sup": bound_sup})
                break

            bound_inf -= 10
            bound_sup -= 10

        if case == "":
            case = "3"
            bound_inf = int(self.FORCE_MIN)
            self.summary["bound_inf"] = bound_inf

        self.summary.update(
            {
                "units": self.units,
                "period": self._find_gust_period(bound_inf).describe(
                    reference_datetime, self.time_zone, self.language
                ),
                "sg_max": self.sg_max,
            }
        )

        return case

    def _find_gust_period(self, bound_inf: float) -> Period:
        """
        Find the period between the 1st and the last term with gust >= bound_inf.

        Args:
            bound_inf: Inferior bound to consider.

        Returns:
            Gust period according to the given inferior bound.

        Raises:
            ValueError: Raised when no valid time is found.
        """
        gust_q90: list[float] = []
        valid_times: list[np.datetime64] = []

        for valid_time in self.dataset.valid_time.values:
            term_data: xr.DataArray = self.gust_da.sel(valid_time=valid_time)
            term_data = term_data.where(term_data > self.FORCE_MIN)
            gust_q90_cur: float = (
                round(np.nanpercentile(term_data.values, self.PERCENTILE_NUM), 2)
                if term_data.count() > 0
                else float("nan")
            )
            gust_q90.append(gust_q90_cur)

            if gust_q90_cur >= bound_inf:
                valid_times.append(valid_time)

        self.dataset["gust_q90"] = xr.DataArray(
            data=gust_q90, coords=[self.dataset.valid_time], dims=["valid_time"]
        )

        # This case should never happen
        if not valid_times:
            raise ValueError(f"No term with Q90 >= bound_inf '{bound_inf}' found !")

        return Period(
            begin_time=Datetime(
                self.dataset.previous_time.sel(valid_time=valid_times[0]).values
            ),
            end_time=Datetime(valid_times[-1]),
        )

    def _process_sg_case_0(self, sg_case: str) -> str:
        # Check that sg_case is '0'
        if sg_case != "0":
            raise ValueError(f"sg_max <= {self.FORCE_MIN} but sg_case != '0' !")

        case: str = sg_case
        if self.rg_max > self.FORCE_MIN:
            case += "_r"
            self.summary["units"] = self.units

        return case

    def _process_sg_max_is_greater(
        self, sg_case: str, reference_datetime: Datetime
    ) -> str:
        if self.pm_separation is True:
            bound_inf: int = self.summary["bound_inf"]
            self.summary.update(
                {
                    "zone": self.risk_infos["zone"],
                    "zone_c": self.risk_infos["zone_c"],
                    "period": self._find_gust_period(bound_inf).describe(
                        reference_datetime, self.time_zone, self.language
                    ),
                }
            )

            case = f"pm_r<s_{sg_case}"

            suffix: str = "_rs"
            if (sg_case in ["1", "3"] and self.rg_max <= self.FORCE_MIN) or (
                sg_case == "2" and self.rg_max <= self.summary["bound_sup"]
            ):
                suffix = "_s"

            return case + suffix

        if (
            sg_case == "3"
            and self.rg_max > self.FORCE_MIN
            and self.sg_max - self.rg_max >= 20
        ):
            return "r<s_3"

        return sg_case

    def _process_rg_max_is_greater(self, sg_case: str) -> str:
        if sg_case == "1" and self.rg_max <= self.summary["bound_sup"]:
            return sg_case

        case = f"r>s_{sg_case}"

        if self.pm_separation is True:
            self.summary.update(
                {"zone": self.risk_infos["zone"], "zone_c": self.risk_infos["zone_c"]}
            )
            return "pm_" + case

        if sg_case in ["2", "3"]:
            suffix: str = "_r"
            if self.rg_max - self.sg_max >= 20:
                suffix += "s"
            case = case + suffix

        return case

    def _compute_case_and_fill_summary(self, reference_datetime: Datetime) -> str:
        sg_case: str = self._sg_max_descriptors(reference_datetime)

        # If rg_max doesn't exist or if rg_max == sg_max, we just describe the
        # synthesis gust
        if self.rg_max is None or self.rg_max == self.sg_max:
            return sg_case

        # If sg_max <= 50 km/h (sg_case 0)
        if self.sg_max <= self.FORCE_MIN:
            return self._process_sg_case_0(sg_case)

        # Else if rg_max < sg_max (sg_case 1, 2 or 3)
        if self.rg_max < self.sg_max:
            return self._process_sg_max_is_greater(sg_case, reference_datetime)

        # Else if rg_max > sg_max
        return self._process_rg_max_is_greater(sg_case)

    def _generate_summary(self, reference_datetime: Datetime) -> dict:
        case: str = self._compute_case_and_fill_summary(reference_datetime)

        # Update the summary with rg_max and the case
        if self.rg_max is not None:
            self.summary["rg_max"] = self.rg_max
        self._set_summary_case(case)

        # Set the case in the dataset attributes
        self.dataset.attrs[self.TEMPLATE_KEY] = self.case

        return {self.PARAM_NAME: self.summary}
