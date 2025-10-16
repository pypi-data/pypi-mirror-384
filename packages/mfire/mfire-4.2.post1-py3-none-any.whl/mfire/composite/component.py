from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from functools import cached_property
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Literal,
    Optional,
    Tuple,
)

import numpy as np
from pydantic import Field, SkipValidation, field_validator
from pydantic_core.core_schema import ValidationInfo

import mfire.utils.mfxarray as xr
from mfire.composite.base import BaseComposite, BaseModel
from mfire.composite.event import EventComposite
from mfire.composite.field import FieldComposite
from mfire.composite.geo import GeoComposite
from mfire.composite.level import LevelComposite, LocalisationConfig
from mfire.composite.operator import ComparisonOperator
from mfire.composite.period import PeriodComposite
from mfire.composite.serialized_types import s_datetime
from mfire.settings import TEXT_ALGO, get_logger
from mfire.utils.date import Datetime
from mfire.utils.exception import LoaderError
from mfire.utils.period import Period, PeriodDescriber
from mfire.utils.xr import ArrayLoader, da_set_up

# Logging
LOGGER = get_logger(name="components.mod", bind="components")


# COMPONENTS


class TypeComponent(str, Enum):
    """Enumeration class containing the types of components"""

    RISK = "risk"
    SYNTHESIS = "text"


class AbstractComponentComposite(BaseComposite, ABC):
    """
    This abstract class implements the ComponentComposite design pattern,
    which is used to create components of type text or risk.

    Inherits: BaseComposite
    """

    data: Any = None
    period: PeriodComposite
    id: str
    type: TypeComponent
    name: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    geos: Optional[List[str]] = None
    production_id: str
    production_name: str
    production_datetime: s_datetime
    configuration_datetime: Optional[s_datetime] = Datetime()

    def reset(self) -> BaseComposite:
        super().reset()
        self.data = None
        return self

    @field_validator("production_datetime", "configuration_datetime", mode="before")
    def init_dates(cls, date_config: str) -> Datetime:
        return Datetime(date_config)

    @abstractmethod
    def alt_area_name(self, geo_id: str) -> str:
        """
        Get the alt area name associated with the given geo_id from the weather dataset.

        Args:
            geo_id: Geo ID

        Returns:
            str: Alt area name
        """

    @abstractmethod
    def area_name(self, geo_id: str) -> str:
        """
        Get the area name associated with the given geo_id from the weather dataset.

        Args:
            geo_id: Geo ID

        Returns:
            str: Area name
        """

    def _compute(self):
        raise NotImplementedError

    def compute(self) -> Any:
        if self.data is not None:
            return self.data
        try:
            self.data = self._compute()
        except LoaderError as err:
            LOGGER.error(
                "Missing data to make the component.",
                production_id=self.production_id,
                production_name=self.production_name,
                component_id=self.id,
                component_name=self.name,
                component_type=self.type,
                msg=str(err),
            )
        return self.data

    @cached_property
    def period_describer(self) -> PeriodDescriber:
        return PeriodDescriber(
            cover_period=Period(
                begin_time=self.period.start, end_time=self.period.stop
            ),
            request_time=self.production_datetime,
            parent=self,
        )


class RiskComponentComposite(AbstractComponentComposite):
    """Component object of type risk."""

    type: Literal[TypeComponent.RISK] = TypeComponent.RISK.value
    levels: List[LevelComposite]
    hazard_id: str
    hazard_name: str
    product_comment: bool
    params: Dict[str, FieldComposite]

    @property
    def risk_ds(self) -> xr.Dataset:
        """
        Get the risks dataset.

        Returns:
            xr.Dataset: Aleas dataset
        """
        return self.data

    @cached_property
    def final_risk_da(self) -> Optional[xr.DataArray]:
        """
        Get the final risk DataArray.

        Returns:
            xr.DataArray: Final risk DataArray
        """
        if self.is_risks_empty:
            return None
        return (
            (self.risk_ds["occurrence"] * self.risk_ds.risk_level)
            .max(dim="risk_level", skipna=True)
            .rolling({"valid_time": 3}, center=True, min_periods=1)
            .reduce(self._replace_middle)
        ).astype("float32", copy=False)

    @staticmethod
    def _special_merge(d1: xr.Dataset, d2: xr.Dataset) -> xr.Dataset:
        """
        Merges "non-mergeable" variables in datasets.

        Args:
            d1: First dataset to merge.
            d2: Second dataset to merge.

        Returns:
            xr.Dataset: Merged dataset.
        """
        dout = xr.Dataset()

        # Iterate over the intersection of non-mergeable variables in the two datasets.
        inter = (
            {
                "summarized_density",
                "risk_summarized_density",
                "occurrence",
                "occurrence_event",
                "occurrence_plain",
                "occurrence_mountain",
            }
            .intersection(d1.data_vars)
            .intersection(d2.data_vars)
        )

        for var in inter:
            lev1 = set(d1[var].risk_level.values)
            lev2 = set(d2[var].risk_level.values)
            lev_inter = lev2.intersection(lev1)

            # If there is an intersection of risk levels, merge the variables.
            if lev_inter != set():
                d2_var_new = d2[var].broadcast_like(d1[var]).fillna(0.0)
                d1_var_new = d1[var].broadcast_like(d2_var_new).fillna(0.0)
                dout[var] = np.fmax(d1_var_new, d2_var_new)

                d1 = d1.drop_vars(var)
                d2 = d2.drop_vars(var)

        dout = xr.merge([d1, d2, dout])

        # Transform occurrences to booleans since it was converted into float during
        # the merge operation.
        dout["occurrence"] = dout.occurrence.mask.bool
        if "occurrence_event" in dout:
            dout["occurrence_event"] = dout["occurrence_event"].mask.bool
        if "occurrence_plain" in dout:
            dout["occurrence_plain"] = dout["occurrence_plain"].mask.bool
        if "occurrence_mountain" in dout:
            dout["occurrence_mountain"] = dout["occurrence_mountain"].mask.bool

        return dout

    @staticmethod
    def _replace_middle(x: np.ndarray, axis: Optional[int] = None) -> np.ndarray:
        """
        Replaces the middle value of a risk if it is lower than its neighbors.

        This function scans and replaces the values. For example:
        [2,1,2] => [2,2,2]
        [5,1,4] => [5,4,4]
        [5,4,1] => [5,4,1]

        This function fills in the gaps. It doesn't matter if the other values are not
        consistent.

        Args:
            x: Array containing the risks to fill in. This array must be passed through
                a rolling operation (over 3 time dimensions). The resulting array has
                one additional dimension compared to the original.
            axis:
                Axis along which the rolling operation was performed.

        Returns:
            np.ndarray: Array with the original dimension (before rolling).
        """
        if isinstance(axis, tuple) and len(axis) == 1:
            axis = axis[0]
        x_borders = np.min(x.take([0, 2], axis=axis), axis=axis)
        x_middle = x.take(1, axis=axis)
        x_out = np.nanmax([x_borders, x_middle], axis=0)
        return x_out

    def _compute(self) -> xr.Dataset:
        """Compute the risk dataset.

        Raises:
            Exception: Merging errors

        Returns:
            The computed risk dataset.
        """
        # Computing of the risk
        risk_ds = xr.Dataset()
        for level in self.levels:
            try:
                level_risk_da = level.compute()
                level_risk_da.attrs["level"] = int(level.level)
                level_risk_da = level_risk_da.expand_dims(
                    dim="risk_level"
                ).assign_coords(risk_level=[int(level.level)])
                risk_ds = self._special_merge(risk_ds, level_risk_da)
            except Exception as excpt:
                LOGGER.error(
                    "Error in merging dataset",
                    hazard=self.hazard_id,
                    bulletin=self.production_id,
                    func="Component.compute",
                    exc_info=True,
                )
                raise excpt
        return risk_ds

    def get_comparison(self, level: int = 1) -> dict:
        """
        Get the comparison dictionary for the specified risk level as follows:
            {
                "T__HAUTEUR2": {
                    "plain": Threshold(...),
                    "mountain": Threshold(...),
                    "category": ...,
                    "mountain_altitude": ...,
                    "aggregation": ...,
                },
                "NEIPOT1__SOL": {...},
            }

        Args:
            level: The risk level. Defaults to 1.

        Returns:
            Comparison dictionary
        """
        # Retrieve the comparison dictionary for the desired level
        d1_comp = self.levels_of_risk(level=level)[0].comparison

        # Iterate over each variable and check for identical variables in other levels
        for variable in d1_comp:
            other_level = self.levels_of_risk(level=level + 1)
            if not other_level:
                continue

            d2_comp = other_level[0].comparison
            if variable in d1_comp and variable in d2_comp:
                if "plain" in d1_comp[variable] and "plain" in d2_comp[variable]:
                    d1_comp[variable]["plain"].update_next_critical(
                        d2_comp[variable]["plain"]
                    )
                if "mountain" in d1_comp[variable] and "mountain" in d2_comp[variable]:
                    d1_comp[variable]["mountain"].update_next_critical(
                        d2_comp[variable]["mountain"]
                    )
        return d1_comp

    @staticmethod
    def replace_critical(
        critical_value: Dict,
    ) -> Tuple[Optional[float], Optional[float]]:
        op, value, next_critical, threshold = (
            critical_value.get("operator"),
            critical_value.get("value"),
            critical_value.get("next_critical"),
            critical_value.get("threshold"),
        )
        if value is None or op is None:
            return None, None
        op = ComparisonOperator(op)
        if next_critical is not None and op(value, next_critical):
            rep_value = next_critical + np.sign(next_critical - value)
            local = value
        else:
            rep_value = value
            local = (
                threshold
                if critical_value.get("occurrence") and op(threshold, value)
                else None
            )  # handling of too low/high values compared with the threshold(#38212)
        return rep_value, local

    @property
    def is_risks_empty(self) -> bool:
        """
        Check if the risks dataset is empty.

        Returns:
            bool: True if the risks dataset is empty, False otherwise
        """
        return not bool(self.risk_ds)

    def levels_of_risk(self, level: int) -> List[LevelComposite]:
        """
        Returns the list of levels that match the specified risk level.

        Args:
            level: The required risk level.

        Returns:
            List of LevelComposite objects of the given level.
        """
        return (
            [lvl for lvl in self.levels if lvl.level == level]
            if 1 <= level <= 3
            else []
        )

    def final_risk_max_level(self, geo_id: Optional[str] = None) -> int:
        """
        Return the maximum risk level for a given area.

        Args:
            geo_id: The area ID

        Returns:
            int: The maximum risk level
        """
        if self.is_risks_empty:
            return 0
        da = self.final_risk_da
        if geo_id is not None:
            da = da.sel(id=geo_id)
        return int(da.max().item())

    def alt_area_name(self, geo_id: str) -> str:
        """
        Get the alt name of the geographical area based on its ID.

        Args:
            geo_id: The ID of the geographical area

        Returns:
            str: The name of the geographical area, or "N.A" if no risks are available.
        """
        if not self.is_risks_empty:
            return str(self.risk_ds.sel(id=geo_id)["altAreaName"].data)
        return "N.A"

    def area_name(self, geo_id: str) -> str:
        """
        Get the name of the geographical area based on its ID.

        Args:
            geo_id: The ID of the geographical area

        Returns:
            str: The name of the geographical area, or "N.A" if no risks are available.
        """
        if not self.is_risks_empty:
            return str(self.risk_ds.sel(id=geo_id)["areaName"].data)
        return "N.A"

    def has_risk(self, ids: List[str], valid_time: slice) -> Optional[bool]:
        """
        Checks if any of the provided IDs have a risk within the specified time slice.

        Args:
            ids: A list of IDs to check for risks.
            valid_time: A time slice object representing the valid time range to
                consider.

        Returns:
            Optional[bool]:
                - True if at least one ID has a risk within the time slice.
                - False if none of the IDs have a risk within the time slice.
                - None if there are no entries for the provided IDs.
        """
        if self.final_risk_da is None:
            return None

        occurrence = self.final_risk_da.where(
            self.final_risk_da.id.isin(ids), drop=True
        ).sel(valid_time=valid_time)
        return occurrence.any().item() if occurrence.size > 0 else None

    def has_field(self, field: str, ids: List[str]) -> Optional[bool]:
        for level in self.levels:
            for event in level.events:
                if set(ids).intersection(event.geos_id) and field in event.field.name:
                    return True
        return False

    @staticmethod
    def _get_extreme_values(
        data_types: list[str], values_ds: xr.Dataset, activated_risk: bool
    ):
        # If values_ds is empty, then return empty dictionary
        if values_ds.valid_time.size == 0:
            return {}

        # Initialize the extreme values dictionary
        extreme_values: dict[str, Optional[float | int]] = {}

        functions: dict[str, Callable] = {"min": min, "max": max}

        for dt in data_types:
            for qualif in ["plain", "mountain"]:
                var_name: str

                if activated_risk is True:
                    var_name = f"rep_value_{qualif}"
                else:
                    var_name = f"{dt}_{qualif}"

                if (
                    var_name not in values_ds.data_vars
                    or np.isnan(values_ds[var_name].values).all()
                ):
                    continue

                extreme_values[f"{qualif}_{dt}"] = round(
                    float(functions[dt](values_ds[var_name].values)), 2
                )

        return extreme_values

    def level_event_couples(
        self, field_name: str
    ) -> Generator[Tuple[LevelComposite, EventComposite]]:
        """
        Generates the level/event couples for which events have the input field.

        Args:
            field_name: Name of the field

        Yields:
            Generator of all level/event couples
        """
        for level in sorted(self.levels, key=lambda lvl: lvl.level, reverse=True):
            for event in level.events:
                if event.field.name == field_name:
                    yield level, event

    def is_plain_mountain_separated(self, field_name: str) -> bool:
        for _, event in self.level_event_couples(field_name):
            if event.mountain is not None:
                return True
        return False

    @staticmethod
    def _is_plain_mountain_separation(levels_events: List[Tuple], geo_id: str) -> bool:
        """
        Checks if there is a separation between the plain and the mountain.

        Args:
            levels_events: List of tuple containing levels and events.
            geo_id: Id of the geo to check.

        Returns:
            True if there is a separation between the plain and the mountain, False
            otherwise.
        """
        for _, event in levels_events:
            if geo_id not in event.values_ds.id:
                continue

            # If event.mountain exists, then it means that there is a separation
            # between the plain and the mountain
            if event.mountain is not None:
                return True
        return False

    def get_risk_infos(
        self, field_name: str, geo_id: str, valid_time: slice, data_types: list[str]
    ) -> dict[str, float | int | bool]:
        """Get the risk information regarding some parameters.

        Args:
            field_name: Field name of the risk.
            geo_id: Geo id of the risk.
            valid_time: A time slice object representing the valid time range to
                consider.
            data_types: Data types as a list which can be [], ['min'], ['max'] or
                ['min', 'max'].

        Returns:
            A dictionary with the risk's infos.
        """
        risk_infos: dict[str, float | int | bool] = {
            "pm_sep": False,
            "activated_risk": False,
        }

        # Check ig geo_id is known
        if geo_id not in self.final_risk_da.id.values:
            return risk_infos

        level_event_couples: list = list(self.level_event_couples(field_name))
        if not level_event_couples:
            return risk_infos

        risk_level_min: int = min((c[0].level for c in level_event_couples))

        for level, event in level_event_couples:
            # Check if geo_id is in event.values_ds.id and if not continue with the
            # next level/event couple
            if geo_id not in event.values_ds.id:
                continue

            risk_level: int = level.level

            occurrence: xr.DataArray = self.risk_ds.sel(
                valid_time=valid_time, risk_level=level.level, id=geo_id
            ).occurrence
            activated_risk = bool(occurrence.values.any())

            if activated_risk is False and risk_level != risk_level_min:
                continue

            # Get values_ds
            values_ds: xr.Dataset = event.values_ds.sel(
                valid_time=valid_time, id=geo_id
            )

            # Keep min and/or max of extreme_values in risk_infos
            risk_infos = self._get_extreme_values(data_types, values_ds, activated_risk)

            risk_infos.update(
                {
                    "activated_risk": activated_risk,
                    "risk_level": risk_level,
                    "pm_sep": self._is_plain_mountain_separation(
                        level_event_couples, geo_id
                    ),
                }
            )

            break

        return risk_infos

    def geo(self, geo_id: str) -> Optional[xr.DataArray]:
        for level in self.levels:
            for event in level.events:
                geo = event.geos.compute()
                if geo_id in geo.id:
                    return geo.sel(id=geo_id)
        return None

    @staticmethod
    def _percent_uncertaintiy_format(x) -> int:
        return int(round(100 * min(1.0, max(0.0, float(x)))))

    def percent_uncertainty(self, geo_id: str) -> Optional[int]:
        level = self.final_risk_max_level(geo_id)
        next_level = level + 1 if level > 0 else self.risk_ds.risk_level.min().item()

        current_level = level if level > 0 else next_level
        threshold = (
            self.risk_ds["threshold_dr"].sel(risk_level=current_level)
            if level > 0
            else 0
        )

        densities = self.risk_ds[
            "risk_density" if "risk_density" in self.risk_ds else "density"
        ]

        # Max level case
        if next_level not in self.risk_ds.risk_level:
            values = densities.sel(id=geo_id, risk_level=level).max("valid_time")

            return self._percent_uncertaintiy_format(
                (
                    (values - threshold) / threshold
                    if (threshold > 0).any()
                    else values
                ).mean()
            )

        # If no risk with occurrence condition for first level
        next_threshold = self.risk_ds["threshold_dr"].sel(risk_level=next_level)
        if level == 0 and np.allclose(next_threshold, 0.0):
            return 0

        # If required density of next level is different those of the current
        # level then density is compared to the required density of next level
        if level == 0 or (
            (next_threshold != threshold).any()
            and self.levels_of_risk(level)[0].is_same_than(
                self.levels_of_risk(next_level)[0]
            )
        ):
            values = densities.sel(id=geo_id, risk_level=current_level).max(
                "valid_time"
            )
            return self._percent_uncertaintiy_format(
                ((values - threshold) / (next_threshold - threshold)).mean()
            )
        return self._percent_uncertainty_VR(geo_id, current_level, next_level)

    def _percent_uncertainty_VR(
        self, geo_id: str, current_level: int, next_level: int
    ) -> Optional[int]:
        # Otherwise the representative value is compared to the threshold of the next
        # level
        percents = []
        for kind in ["plain", "mountain"]:
            if f"rep_value_{kind}" not in self.risk_ds:
                continue

            values = self.risk_ds[f"rep_value_{kind}"].sel(
                risk_level=current_level, id=geo_id
            )
            threshold = self.risk_ds[f"threshold_{kind}"].sel(risk_level=current_level)
            next_threshold = self.risk_ds[f"threshold_{kind}"].sel(
                risk_level=next_level
            )
            computed_percent = (
                (values - threshold) / (next_threshold - threshold)
            ).mean()
            if np.isnan(computed_percent):
                continue

            percents.append(self._percent_uncertaintiy_format(computed_percent))

        return int(np.mean(percents)) if percents else None

    def code_uncertainty(self, geo_id: str) -> int:
        percent = self.percent_uncertainty(geo_id)
        if percent is None or np.isnan(percent):
            return 0

        max_level = self.final_risk_max_level(geo_id)
        code = min(int(percent // (100 / 3)) + 1, 3)

        if max_level == 0:
            return 10 + code
        if max_level < self.risk_ds.risk_level.max().item():
            return 20 + code
        return 30 + code


class SynthesisComponentComposite(AbstractComponentComposite):
    """Component object of type text."""

    _keep_data = True

    type: Literal[TypeComponent.SYNTHESIS] = TypeComponent.SYNTHESIS.value
    product_comment: bool
    weathers: List[SynthesisModule]

    def _compute(self) -> xr.Dataset:
        """
        Computes the weather dataset by merging the computed weather data for each
        weather in the list.

        Returns:
            Merging of all computed weather dataset.
        """
        return xr.merge([weather.weather_data() for weather in self.weathers])

    def alt_area_name(self, geo_id: str) -> str:
        """
        Get the alt area name associated with the given geo_id from the weather dataset.

        Args:
            geo_id: Geo ID

        Returns:
            str: Area name
        """
        return str(self.compute().sel(id=geo_id)["altAreaName"].values)

    def area_name(self, geo_id: str) -> str:
        """
        Get the area name associated with the given geo_id from the weather dataset.

        Args:
            geo_id: Geo ID

        Returns:
            str: Area name
        """
        return str(self.compute().sel(id=geo_id)["areaName"].values)

    @property
    def weather_period(self) -> PeriodComposite:
        """Get the period covered by the summary text.

        Returns:
            PeriodComposite: Period without an associated name (it will be computed by
            CDPPeriod)
        """
        # The period name will be automatically computed by CDPPeriod,
        # so no need to set it here.
        return PeriodComposite(
            id=self.period.id, start=self.period.start, stop=self.period.stop
        )


# COMPONENT MODULES


class SynthesisCompositeInterface(BaseModel):
    has_risk: Callable[[str, List[str], slice], Optional[bool]]
    has_field: Callable[[str, str, List[str]], Optional[bool]]
    get_risk_infos: Callable[
        [list[str], str, str, slice, list[str]], dict[str, float | int | bool | str]
    ]


class SynthesisModule(BaseComposite):
    """
    Represents a WeatherComposite object containing the configuration of weather
    conditions for the Promethee production task.
    """

    id: str
    condition: Optional[EventComposite] = None
    params: Dict[str, FieldComposite]
    geos: Optional[GeoComposite] = None
    localisation: LocalisationConfig
    units: Dict[str, Optional[str]] = {}
    algorithm: Optional[str] = "generic"
    nebulosity: Optional[bool] = False

    interface: Optional[SynthesisCompositeInterface] = None
    parent: Annotated[
        Optional[SynthesisComponentComposite],
        Field(exclude=True, repr=False),
        SkipValidation,
    ] = None

    @field_validator("params")
    def validate_params(cls, v: dict, info: ValidationInfo):
        """
        Validates the keys of the params dictionary.

        Args:
            v: The params dictionary.
            info: The values of the model.

        Returns:
            The validated params dictionary.

        Raises:
            ValueError: If the keys of the params dictionary do not match the expected
                keys.
        """
        params_expected = TEXT_ALGO[info.data["id"]][info.data.get("algo", "generic")][
            "params"
        ].keys()

        if v.keys() != params_expected:
            raise ValueError(
                f"Wrong field: {list(v.keys())}, expected {list(params_expected)}"
            )
        return v

    def check_condition(self, geo_id: str) -> bool:
        """
        Checks if the condition is satisfied.

        Args:
            geo_id: Geo id to check the condition.

        Returns:
            bool: True if the condition is satisfied, False otherwise.
        """
        if self.condition is None:
            return True

        # Set mask_id to be able to check the condition
        self.condition.geos.mask_id = geo_id
        event_da = self.condition.compute()
        return bool(event_da.any().values)

    def geos_data(self, geo_id: Optional[str] = None) -> xr.DataArray:
        """
        Computes the geos data.

        Args:
            geo_id: Id of geo to take the geos data.

        Returns:
            xr.Dataset: The computed weather dataset.
        """
        geos = self.geos.compute()
        if geo_id is not None:
            geos = geos.sel(id=geo_id)
        return geos

    def geos_descriptive(self, geo_id: str) -> xr.DataArray:
        """
        Returns the descriptive geos DataArray.

        Args:
            geo_id: Id of geo to take the geos_descriptive.

        Returns:
            xr.DataArray: The descriptive geos DataArray.
        """
        geos = self.geos.mask_da
        allowed_area_types = ["Axis"]
        if self.localisation.altitude_split:
            allowed_area_types += ["Altitude"]
        if self.localisation.compass_split:
            allowed_area_types += ["compass"]
        ids = [
            id
            for id in geos.id.data
            if (
                (
                    id.startswith(geo_id)
                    and geos.sel(id=id).areaType in allowed_area_types
                )
                or id in self.localisation.geos_descriptive
            )
        ]

        return geos.sel(id=ids)

    def weather_data(self, geo_id: Optional[str] = None) -> xr.Dataset:
        """
        Computes weather dataset.

        Args:
            geo_id: Id of the geo to get weather data. If None, all weather data are
                taken

        Returns:
            xr.Dataset: The computed weather dataset.
        """
        output_ds = xr.Dataset(
            {
                name: field.compute().reset_coords(drop=True)
                for name, field in self.params.items()
            }
        )

        # Take into account the geo mask
        if self.geos is not None:
            output_ds = (
                output_ds * da_set_up(self.geos_data(geo_id), output_ds).mask.f32
            )

        return output_ds

    def altitude(self, param: str) -> Optional[xr.DataArray]:
        """
        Returns the altitude DataArray for a given parameter.

        Args:
            param: The parameter name.

        Returns:
            Optional[xr.DataArray]: The altitudes DataArray or None if not found.
        """
        try:
            return ArrayLoader.load_altitude(self.params[param].grid_name)
        except KeyError:
            return None
