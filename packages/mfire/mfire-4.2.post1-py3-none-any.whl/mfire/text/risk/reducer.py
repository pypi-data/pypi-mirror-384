from __future__ import annotations

import zoneinfo
from abc import abstractmethod
from collections import defaultdict
from functools import cached_property
from itertools import combinations
from typing import Annotated, ClassVar, Dict, List, Optional

import numpy as np
import pandas as pd
from pydantic import SkipValidation, model_validator

import mfire.utils.mfxarray as xr
from mfire.composite.base import BaseComposite
from mfire.composite.component import RiskComponentComposite
from mfire.composite.operator import ComparisonOperator
from mfire.localisation.risk_localisation import RiskLocalisation
from mfire.settings import SPACE_DIM, get_logger
from mfire.text.base.reducer import BaseReducer
from mfire.text.risk.rep_value import RepValueBuilder, RepValueReducer
from mfire.utils.date import Datetime, Timedelta
from mfire.utils.exception import LocalisationWarning
from mfire.utils.period import Period, PeriodDescriber, Periods
from mfire.utils.string import concatenate_string, decapitalize
from mfire.utils.template import CentroidTemplateRetriever, TemplateRetriever
from mfire.utils.unit_converter import unit_conversion
from mfire.utils.wwmf import Wwmf

# Logging
LOGGER = get_logger(name="text_reducer.mod", bind="text_reducer")


class RiskReducer(BaseReducer):
    parent: Annotated[RiskComponentComposite, SkipValidation]
    localisation: Optional[RiskLocalisation] = None

    @model_validator(mode="after")
    def init_localisation(self):
        if self.localisation is None:
            try:
                self.localisation = RiskLocalisation(
                    parent=self.parent, geo_id=self.geo_id
                )
                self.localisation.compute()
            except LocalisationWarning:
                self.localisation = None
        return self

    @property
    def alt_area_name(self) -> str:
        return self.parent.alt_area_name(self.geo_id)

    @cached_property
    def strategy(self) -> RiskReducerStrategy:
        """
        Decides which comment generation module to use between ME, snow, monozone or
        multizone.

        Returns:
            Specific strategy according to the hazard_name (like snow or ME) or case
            (like monozone or multizone).
        """
        if self.parent.hazard_name.startswith("ME_"):
            return RiskReducerStrategyME(parent=self)
        if self.parent.hazard_name == "Neige":
            return RiskReducerStrategySnow(parent=self)
        if self.parent.hazard_name == "Pluies":
            return RiskReducerStrategyRain(parent=self)

        if self.is_multizone:
            return RiskReducerStrategyMultizone(parent=self)
        return RiskReducerStrategyMonozone(parent=self)

    @property
    def is_multizone(self) -> bool:
        return self.localisation is not None and self.localisation.is_multizone

    @cached_property
    def final_risk_da(self) -> xr.DataArray:
        return self.parent.final_risk_da.sel(id=self.geo_id)

    @cached_property
    def final_risk_max_level(self) -> int:
        return self.parent.final_risk_max_level(self.geo_id)

    @cached_property
    def comparison(self) -> dict:
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

        Returns:
            dict: Comparison dictionary
        """
        # Retrieve the comparison dictionary for the desired level
        if self.final_risk_max_level == 0:
            return {}

        d1_comp = self.parent.levels_of_risk(self.final_risk_max_level)[0].comparison

        # Iterate over each variable and check for identical variables in other levels
        for variable in d1_comp:
            other_level = self.parent.levels_of_risk(self.final_risk_max_level + 1)
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

    @property
    def risk_ds(self) -> xr.Dataset:
        return (
            self.localisation.spatial_localisation.localised_risk_ds
            if self.is_multizone
            else self.parent.risk_ds.sel(id=self.geo_id).expand_dims({"id": 1})
        )

    def _compute_critical_values(
        self, evt_ds: xr.Dataset, dict_comp: dict, kind: str
    ) -> dict:
        key = f"rep_value_{kind}"
        if key not in evt_ds or kind not in dict_comp or np.isnan(evt_ds[key]).all():
            return {}

        if dict_comp[kind].comparison_op.is_increasing_order:
            values = evt_ds[key].max(["valid_time", "id"]).values
            area = (
                evt_ds[key]
                .isel(id=evt_ds[key].max("valid_time").argmax("id"))["id"]
                .item()
            )
        elif dict_comp[kind].comparison_op.is_decreasing_order:
            values = evt_ds[key].min(["valid_time", "id"]).values
            area = (
                evt_ds[key]
                .isel(id=evt_ds[key].min("valid_time").argmin("id"))["id"]
                .item()
            )
        else:
            raise ValueError(
                "Operator is not understood when trying to find the critical "
                "representative values."
            )
        value = float(values) if values.ndim == 0 else float(values[0])

        return {
            kind: {
                "id": area,
                "operator": ComparisonOperator(dict_comp[kind].comparison_op),
                "threshold": dict_comp[kind].threshold,
                "units": dict_comp[kind].units,
                "next_critical": dict_comp[kind].next_critical,
                "value": value,
                "occurrence": evt_ds[f"occurrence_{kind}"].any().item(),
            }
        }

    def get_critical_values(
        self, valid_time: Optional[slice] = None, var_name: Optional[str] = None
    ) -> dict:
        """
        Get the critical values.

        Args:
            valid_time: Slice of the expected valid time.
            var_name: Expected name of the variable.

        Returns:
            Dictionary containing the critical values, keyed by variable name.
        """
        if not self.comparison:
            return {}

        # Get the risk dataset
        risk_ds = self.risk_ds.sel(risk_level=self.final_risk_max_level)
        if valid_time is not None:
            risk_ds = risk_ds.sel(valid_time=valid_time)

        # Create a dictionary to store the critical values.
        critical_values = {}

        # Iterate over the events in the spatial table_localisation.
        for evt in risk_ds.evt:
            # Get the variable name for the event.
            evt_ds = risk_ds.sel(evt=evt)
            weather_var_name = evt_ds.weatherVarName.item()
            if (var_name and weather_var_name != var_name) or pd.isna(weather_var_name):
                continue

            # Get the dictionary of comparison for the concerned variable.
            dict_comp = self.comparison[weather_var_name]

            # Create a dictionary to store the critical values for the event.
            event_critical_values = self._compute_critical_values(
                evt_ds, dict_comp, "plain"
            ) | self._compute_critical_values(evt_ds, dict_comp, "mountain")

            mountain_altitude = dict_comp.get("mountain_altitude")
            if mountain_altitude is not None:
                event_critical_values["mountain_altitude"] = mountain_altitude

            # If there are any critical values for the event, add them to the
            # dictionary of critical values.
            if event_critical_values and weather_var_name not in critical_values:
                critical_values[weather_var_name] = event_critical_values

        # Return the dictionary of critical values.
        return critical_values

    def post_process(self):
        """Make a post-process operation in the reduction."""
        super().post_process()
        self.strategy.process_period()

    def compute_reduction(self) -> dict:
        """
        Decides which comment generation module to use.

        Returns:
            Dedicated strategy.
        """
        self.reduction = self.strategy.compute()
        self.reduction["alt_area_name"] = self.parent.alt_area_name(self.geo_id)
        return self.reduction


class RiskReducerStrategy(BaseComposite):
    parent: RiskReducer

    @property
    def period_describer(self) -> PeriodDescriber:
        return self.risk_component.period_describer

    @property
    def geo_id(self) -> str:
        return self.parent.geo_id

    @property
    def risk_component(self) -> RiskComponentComposite:
        return self.parent.parent

    @property
    def is_multizone(self) -> bool:
        return self.parent.is_multizone

    @property
    def reduction(self):
        return self.parent.reduction

    @reduction.setter
    def reduction(self, value):
        self.parent.reduction = value

    @cached_property
    def localisation(self) -> str:
        if self.is_multizone:
            return self.parent.localisation.all_name
        return self.parent.alt_area_name

    @abstractmethod
    def compute(self):
        """Main compute method"""

    @abstractmethod
    def process_period(self):
        """Process period method for reduction operation"""


class RiskReducerStrategyDDI(RiskReducerStrategy):
    intensity_parameter: ClassVar[str] = ...

    @cached_property
    def intensity(self) -> float:
        spatial_risk_da = xr.concat(
            [
                lvl.spatial_risk_da.sel(id=self.parent.geo_id)
                for lvl in self.risk_component.levels_of_risk(
                    self.parent.final_risk_max_level
                )
            ],
            dim="valid_time",
        )
        data = self.risk_component.params[self.intensity_parameter].compute()
        intensity = data * spatial_risk_da
        intensity.name = data.name  # in order to convert with context
        return float(unit_conversion(intensity, "cm").max())

    @property
    @abstractmethod
    def intensity_key(self) -> str:
        """Returns the intensity key used for the template"""

    def compute(self) -> dict:
        """
        Make the reduction in the case of snow risk - see #40981

        Returns:
            Reduced information.
        """
        if self.parent.final_risk_max_level == 0:
            return {"key": "RAS"}

        return {"key": self.intensity_key, "localisation": self.localisation}

    @abstractmethod
    def process_period(self):
        """Process the period."""


class RiskReducerStrategySnow(RiskReducerStrategyDDI):
    intensity_parameter: ClassVar[str] = "NEIPOT3__SOL"

    @property
    def intensity_key(self) -> str:
        if self.intensity < 3:
            return "low"
        if self.intensity < 5:
            return "moderate"
        return "high"

    def process_period(self):
        """Process the period."""
        if self.parent.final_risk_max_level == 0:
            return

        wwmf = self.risk_component.params["WWMF__SOL"].compute()
        wwmf = Wwmf.is_snow(wwmf) & (wwmf != 58)

        density = wwmf.sum(dim=SPACE_DIM) / wwmf.sum()
        density = (density[:-1].to_numpy() + density[1:].to_numpy()) >= 0.05
        if density.sum() == 0:
            self.reduction["periods"] = self._("par moments")
            return

        stops = [Datetime(vt) for vt in wwmf.valid_time]
        starts = [
            wwmf.valid_time[0] - (wwmf.valid_time[1] - wwmf.valid_time[0])
        ] + stops[:-1]

        density = np.concatenate(([False], density, [False]))
        starts = [starts[idx] for idx in (density[1:] & ~density[:-1]).nonzero()[0]]
        stops = [stops[idx] for idx in (~density[1:] & density[:-1]).nonzero()[0]]

        periods = Periods(
            [
                Period(begin_time=start, end_time=stop)
                for start, stop in zip(starts, stops)
            ]
        )
        self.reduction["periods"] = self.period_describer.describe(periods)


class RiskReducerStrategyRain(RiskReducerStrategyDDI):
    intensity_parameter: ClassVar[str] = "EAU1__SOL"

    @property
    def intensity_key(self) -> str:
        if self.intensity >= 0.76:
            return "high"

        wwmf = self.risk_component.params["WWMF__SOL"].compute()
        spatial_risk_da = xr.concat(
            [
                lvl.spatial_risk_da.sel(id=self.parent.geo_id)
                for lvl in self.risk_component.levels_of_risk(
                    self.parent.final_risk_max_level
                )
            ],
            dim="valid_time",
        )
        has_thunder = (wwmf * spatial_risk_da).isin([98, 99]).any()

        if self.intensity < 0.25:
            return "low_thunder" if has_thunder else "low"
        return "moderate_thunder" if has_thunder else "moderate"

    def process_period(self):
        """Process the period."""
        if self.parent.final_risk_max_level == 0:
            return

        final_risk_da = self.parent.final_risk_da
        stops = [Datetime(vt) for vt in final_risk_da.valid_time]
        if len(stops) == 1:
            starts = [stops[0] - Timedelta(hours=1)] + stops[:-1]
        else:
            starts = [stops[0] - (stops[1] - stops[0])] + stops[:-1]

        idx = [
            i
            for i, level in enumerate(self.parent.final_risk_da)
            if level == self.parent.final_risk_max_level
        ]
        periods = Periods(
            [Period(begin_time=starts[i], end_time=stops[i]) for i in idx]
        )
        self.reduction["periods"] = self.period_describer.describe(periods)


class RiskReducerStrategyMonozone(RiskReducerStrategy):
    def process_value(self, param: str, evts_ds: List, kind: str) -> Optional[Dict]:
        """
        Retrieves all significant values (min, max, rep_value, units, etc.)
        for plain or mountain (kind argument).

        Args:
            param: Parameter (e.g. NEIPOT24__SOL).
            evts_ds: List of datasets containing events for a parameter.
            kind: Plain or mountain.

        Returns:
            Dict: Dictionary containing the information or None if the information is
                not available (e.g., for a qualitative parameter or when kind is
                mountain but no mountain is available).
        """
        occurrence_evt = False
        data_vars = evts_ds[0].data_vars
        threshold, min_v, max_v, rep_value = np.NaN, np.NaN, np.NaN, np.NaN
        if all(
            (
                f"min_{kind}" in data_vars,
                f"max_{kind}" in data_vars,
                f"rep_value_{kind}" in data_vars,
                kind in self.operator_dict[param],
            )
        ):
            ev_values = []
            for ev in evts_ds:
                occurrence_evt = occurrence_evt or ev[f"occurrence_{kind}"].item()
                if ev[f"min_{kind}"].values < min_v or np.isnan(min_v):
                    min_v = ev[f"min_{kind}"].values

                if ev[f"max_{kind}"].values > max_v or np.isnan(max_v):
                    max_v = ev[f"max_{kind}"].values

                ev_values.append(ev[f"rep_value_{kind}"].values)

            rep_value = self.operator_dict[param][kind].critical_value(ev_values)
            threshold = evts_ds[0][f"threshold_{kind}"].item()

        def format_func(x):
            return float(x) if not np.isnan(x) else None

        values_dict = {
            "min": format_func(min_v),
            "max": format_func(max_v),
            "value": format_func(rep_value),
            "units": str(evts_ds[0].units.data),
            "operator": self.operator_dict[param].get(kind),
            "threshold": threshold,
            "occurrence": occurrence_evt,
        }

        return values_dict if None not in values_dict.values() else None

    def compute_infos(self, infos: List[xr.Dataset] | List[xr.DataArray]) -> Dict:
        """
        Retrieves the information for each block Bi.

        Args:
            infos: List of DataArray or Dataset for the same level.

        Returns:
            Dictionary summarizing the desired information.
        """
        if isinstance(infos[0], xr.DataArray):
            return {
                "centroid": infos[0].centroid.item(),
                "level": 0,
                "start": Datetime(min(infos)),
                "stop": Datetime(max(infos)),
            }

        time = []
        level = int(infos[0].risk_level.values)
        bloc = {"centroid": infos[0].centroid.item(), "level": level}

        event_dict = defaultdict(lambda: [])
        for ech in infos:
            time.append(ech.valid_time.values)
            for ev in ech.evt:
                event = ech.sel(evt=ev)
                key_event = str(event.weatherVarName.values)
                # to handle no condition for some event for some level
                # e.g. lvl1 with evt1 and evt2 but lvl2 with only evt1
                if key_event != "nan":
                    event_dict[str(event.weatherVarName.data)].append(event)

        for param, evt_ds in event_dict.items():
            bloc[param] = {}
            plain = self.process_value(param, evt_ds, "plain")
            if plain:
                bloc[param]["plain"] = {**plain}

            mountain = self.process_value(param, evt_ds, "mountain")
            if mountain:
                bloc[param]["mountain"] = {**mountain}
            if (
                mountain_altitude := self.risk_component.levels_of_risk(level=level)[0]
                .events[0]
                .mountain_altitude
            ) is not None:
                bloc[param]["mountain_altitude"] = mountain_altitude
        bloc["start"], bloc["stop"] = Datetime(min(time)), Datetime(max(time))
        return bloc

    @staticmethod
    def mask_start_end(risk: xr.DataArray) -> xr.DataArray:
        # let start and end to False and True elsewhere
        # to get mask between first to last risk steps
        # to avoid expanding risk at start or end
        start = risk.cumulative(dim="valid_time").sum()
        start = xr.where(start == 0, False, True)
        end = risk.sortby("valid_time", ascending=False)
        end = end.cumulative(dim="valid_time").sum()
        end = xr.where(end == 0, False, True)
        end = end.sortby("valid_time", ascending=True)
        return start & end

    @property
    def final_risk_da(self) -> xr.DataArray:
        # Handling of local 3h blocs to avoid to repeat same period name - see #34947
        tz = zoneinfo.ZoneInfo(self.time_zone)
        final_risk_da = self.parent.final_risk_da.copy()
        start_end_mask = self.mask_start_end(final_risk_da)

        final_risk_da["valid_time"] = (
            final_risk_da.valid_time.to_index()
            .tz_localize(zoneinfo.ZoneInfo("UTC"))
            .tz_convert(tz)
            .tz_localize(None)
        )

        final_risk_da = (
            final_risk_da.resample(valid_time="3h")
            .max()
            .reindex(valid_time=final_risk_da.valid_time, method="ffill")
        )

        final_risk_da["valid_time"] = (
            final_risk_da.valid_time.to_index()
            .tz_localize(tz)
            .tz_convert(zoneinfo.ZoneInfo("UTC"))
            .tz_localize(None)
        )
        final_risk_da = final_risk_da.where(start_end_mask, 0)
        # Handling of beginning and ending blocs to avoid to repeat same period name
        # - see #34947
        final_risk_da.values[:3] = max(final_risk_da[:3])
        final_risk_da.values[-3:] = max(final_risk_da[-3:])
        return final_risk_da

    @property
    def norm_risk(self) -> np.ndarray:
        """
        Returns normalized risk levels in the range 0 to 1.

        Returns:
            np.ndarray: Normalized risk levels.
        """
        final_risk = self.final_risk_da.values
        if (max_level := self.parent.risk_ds.risk_level.max().item()) > 1:
            # Normalize risk levels
            final_risk = np.where(
                final_risk, 1 - (((max_level - final_risk) * 0.5) / (max_level - 1)), 0
            )
        return final_risk

    @cached_property
    def operator_dict(self) -> Dict[str, Dict[str, ComparisonOperator]]:
        """Get the comparison operators used for rounding the representative values.

        Returns:
            Dictionary containing the comparison operators per event.
        """
        operator_dict = {}
        for level in self.risk_component.levels:
            for ev in level.events:
                operator_dict[ev.field.name] = {}
                try:
                    operator_dict[ev.field.name]["plain"] = ev.plain.comparison_op
                except AttributeError:
                    pass
                try:
                    operator_dict[ev.field.name]["mountain"] = ev.mountain.comparison_op
                except AttributeError:
                    pass
        return operator_dict

    def _find_levels_data_loop(self, data: dict):
        # Determine the level key based on the centroid value.
        if data["centroid"] == 1:
            level_key = "level_max"
        elif data["level"] != 0:
            level_key = "level_int"
        else:
            return

        for key, param in data.items():
            # Skip keys that are not relevant to the level comparison
            if key in ["level", "start", "stop", "centroid"]:
                continue

            # If the key is already present in the level dictionary and the
            # representative values is not better than the stored one, skip the
            # parameter.
            if key in self.reduction[level_key] and RepValueReducer.compare(
                self.reduction[level_key][key], param
            ):
                continue

            # Otherwise, add the parameter to the level dictionary.
            self.reduction[level_key][key] = param

    def find_levels(self):
        """
        Add information about the maximum and intermediate levels to the reduction.

        This function iterates over the blocks in the reduction and adds information
        about the maximum and intermediate levels to the `level_max` and `level_int`
        dictionaries.

        The maximum level is determined by the centroid value. The intermediate levels
        are determined by comparing the representative values of the same parameter for
        the same level.
        """

        # Initialize the maximum and intermediate level dictionaries.
        self.reduction["level_max"] = {}
        self.reduction["level_int"] = {}

        # Iterate over the blocks in the reduction.
        for bloc, data in self.reduction.items():
            if bloc.startswith("B"):
                self._find_levels_data_loop(data)

    def process_period(self):
        """Process period-related tags in the comment for monozone case."""
        # Process each key-value pair in the reduction dictionary
        if self.reduction is None:
            return

        for key, val in self.reduction.items():
            # Check if the value is a dictionary with 'start' and 'stop' keys
            if isinstance(val, dict) and "start" in val and "stop" in val:
                # Add the period elements to the period table_localisation
                period_describer = self.risk_component.period_describer
                self.reduction[key]["period"] = period_describer.describe(
                    Period(begin_time=val["start"], end_time=val["stop"])
                )
                self.reduction[key]["start"] = period_describer.describe(
                    Period(begin_time=val["start"])
                )
                self.reduction[key]["stop"] = period_describer.describe(
                    Period(begin_time=val["stop"])
                )

    def compute(self) -> dict:
        """
        Reduces the risk into blocks based on the blocks found after using dtw.

        Returns:
            Reduced risk as a list and a dictionary containing information for each
            block.
        """
        final_risk_da = self.final_risk_da

        self.reduction = CentroidTemplateRetriever.read_file(
            TemplateRetriever.path_by_name("risk/monozone", self.parent.language),
            index_col=["0", "1", "2", "3", "4"],
        ).get_by_dtw(self.norm_risk)

        final_risk_da["blocks"] = ("valid_time", [v[1] for v in self.reduction["path"]])
        centroid_list = []
        last = final_risk_da["blocks"].values[0]
        for x in final_risk_da["blocks"].values:
            if last == x:
                centroid_list.append(self.reduction["centroid"][last])
            else:
                centroid_list.append(self.reduction["centroid"][last + 1])
            last = x
        final_risk_da["centroid"] = ("valid_time", centroid_list)

        # Construction of B blocks
        same_level_list = []
        for idx, risk in enumerate(final_risk_da):
            if (
                idx > 0
                and risk["centroid"].data != final_risk_da["centroid"].data[idx - 1]
            ):
                previous_block = risk["blocks"].data - 1
                self.reduction[f"B{previous_block}"] = self.compute_infos(
                    same_level_list
                )
                same_level_list.clear()

            if risk["centroid"].values == 0:
                same_level_list.append(risk["valid_time"])
            elif risk.values in self.parent.risk_ds.risk_level.values:
                same_level_list.append(
                    self.parent.risk_ds.sel(
                        id=self.geo_id,
                        valid_time=risk["valid_time"],
                        risk_level=risk.values,
                    )
                )
        last_block = final_risk_da[-1]["blocks"].data
        self.reduction[f"B{last_block}"] = self.compute_infos(same_level_list)
        self.find_levels()

        return self.reduction


class RiskReducerStrategyMultizone(RiskReducerStrategy):
    def process_period(self):
        """Process period-related tags in the comment for multizone case."""
        periods = []
        for period_name in self.parent.localisation.periods_name:
            time_list = period_name.split("_to_")
            periods += [Period(begin_time=time_list[0], end_time=time_list[-1])]

        elements = range(len(periods))

        for i in elements:
            for combin in combinations(elements, i + 1):
                keys, values = [], Periods()
                for j in combin:
                    keys += [str(j + 1)]
                    values += [periods[j]]
                key = "periode" + "_".join(keys)
                self.reduction[key] = self.risk_component.period_describer.describe(
                    values
                )

    def compute(self) -> dict:
        self.reduction = self.parent.localisation.table_localisation.table
        return self.reduction


class RiskReducerStrategyME(RiskReducerStrategy):
    def process_period(self):
        if self.parent.final_risk_max_level == 0:
            return

        valid_time = [
            Datetime(vt) for vt in self.parent.risk_ds["occurrence"]["valid_time"]
        ]
        step = (
            Timedelta(hours=1)
            if len(valid_time) == 1
            else valid_time[1] - valid_time[0]
        )

        periods = np.array(
            [Period(begin_time=valid_time[0] - step, end_time=valid_time[0])]
            + [
                Period(begin_time=valid_time[t - 1], end_time=valid_time[t])
                for t in range(1, len(valid_time))
            ]
        )

        periods = Periods(
            periods[
                self.parent.risk_ds.sel(
                    risk_level=self.parent.final_risk_max_level
                ).occurrence.max("id")
                > 0
            ]
        ).reduce()

        if (
            periods.total_hours
            < 0.8 * (valid_time[-1] - valid_time[0] + step).total_hours
        ):
            self.reduction["temporality"] = (
                self.risk_component.period_describer.describe(periods)
            )

    def compute(self) -> dict:
        result = {}

        # split by sentences
        values = RepValueBuilder.compute_all(
            self.parent,
            {k: v | {"ME": True} for k, v in self.parent.get_critical_values().items()},
        ).split(". ")

        values[-1] = values[-1][:-1]  # Remove the last point
        value = concatenate_string(
            (decapitalize(v) for v in values), last_delimiter=f" {self._('et')} "
        )
        if value:
            result["value"] = value

        if self.is_multizone and self.localisation != self.parent.alt_area_name:
            result["localisation"] = self.localisation

        return result
