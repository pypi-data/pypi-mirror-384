from collections import Counter, defaultdict
from functools import cached_property
from itertools import product
from typing import ClassVar, Dict, List, Optional, Tuple

import numpy as np

import mfire.utils.mfxarray as xr
from mfire.localisation.area_algebra import compute_iol
from mfire.settings import get_logger
from mfire.text.synthesis.builder import SynthesisBuilder
from mfire.text.synthesis.reducer import SynthesisReducer
from mfire.utils.calc import combinations_and_remaining, round_to_closest_multiple
from mfire.utils.date import Timedelta
from mfire.utils.period import Period, Periods
from mfire.utils.string import concatenate_string, decapitalize
from mfire.utils.unit_converter import from_w1_to_wwmf
from mfire.utils.wwmf import Wwmf

# Logging
LOGGER = get_logger(name="weather.mod", bind="weather")


class WeatherReducer(SynthesisReducer):
    """WeatherReducer  class for the weather module."""

    # Structure of computed data
    _ts: defaultdict = defaultdict(lambda: {"temp": Periods()})
    _cloudiness: list = []

    # Default label for cloudiness WWMF code
    default_cloudiness: ClassVar[int] = 5
    default_cloudiness_grouping: ClassVar[int] = [1, 2]

    _wwmf_utils: Optional[Wwmf] = None

    # Dictionary giving the minimum values to be considered not isolated
    # The keys are the corresponding WWMF codes
    densities: dict = {
        "DT": {
            "required": defaultdict(lambda: 0.05),
            "precipitation": 0.0,
            "visibility": 0.0,
        },
        "DHmax": {
            "required": defaultdict(lambda: 0.05),
            "precipitation": 0.0,
            "visibility": 0.0,
        },
    }

    def reset(self):
        super().reset()
        self._wwmf_utils = None
        self._ts.clear()
        self._cloudiness.clear()

    @property
    def wwmf_utils(self) -> Wwmf:
        if self._wwmf_utils is None:
            self._wwmf_utils = Wwmf(language=self.language)
        return self._wwmf_utils

    def _are_same_temporalities(self, info1: dict, info2: dict) -> bool:
        if self._describe_temporality(info1) == self._describe_temporality(info2):
            return True
        if info1["temp"].intersects(info2["temp"]):
            return True
        return any(
            abs((p2.begin_time - p1.end_time).total_hours) < 6
            or abs((p2.end_time - p1.begin_time).total_hours) < 6
            for p1, p2 in product(info1["temp"], info2["temp"])
        )

    def has_required_density(self, density: str) -> bool:
        return (
            self.densities["DT"][density] >= self.densities["DT"]["required"][density]
            or self.densities["DHmax"][density]
            >= self.densities["DHmax"]["required"][density]
        )

    @cached_property
    def has_risk_fog(self) -> Optional[bool]:
        return self.has_risk("Brouillard dense et/ou givrant")

    @cached_property
    def has_risk_snow(self) -> Optional[bool]:
        return self.has_risk("Neige")

    def _manage_lpn_inconstistencies(self):
        """Handle the inconsistency problem with LPN and Alpha"""
        consistencies_map = ~Wwmf.is_snow(self.weather_data["wwmf"]) | (
            self.weather_data["lpn"] < self.parent.altitude("lpn")
        )
        if not consistencies_map.all():
            LOGGER.warning(
                "Some inconsistencies with snow and LPN were found and fixed"
            )
            self.weather_data["wwmf"] = self.weather_data["wwmf"].where(
                consistencies_map, other=50
            )

    def _compute_densities(self):
        self.densities["DT"]["precipitation"] = 0
        self.densities["DHmax"]["precipitation"] = 0
        self.densities["DT"]["visibility"] = 0
        self.densities["DHmax"]["visibility"] = 0

        for i in range(1, len(self.times)):
            data_for_fixed_time: xr.DataArray = self.weather_data.wwmf.sel(
                valid_time=self.times[i].as_np_dt64
            )
            all_ts, counts = np.unique(data_for_fixed_time, return_counts=True)

            # Handling of cloudiness
            if ((0 <= data_for_fixed_time) & (data_for_fixed_time <= 6)).any():
                cloudiness = {
                    wwmf: (data_for_fixed_time == wwmf).sum().item()
                    for wwmf in range(7)
                }
                self._cloudiness.append(max(cloudiness, key=cloudiness.get))
            else:
                self._cloudiness.append(self.default_cloudiness)

            # Handling of visibility and precipitation TS
            dh = {"visibility": 0.0, "precipitation": 0.0}
            for ts, count in zip(all_ts, counts):
                # Mist is not considered in order to avoid over-representation of the
                # Alpha model
                # Skip if it's not a TS
                if ts == 31 or not Wwmf.families(ts):
                    continue

                self._ts[ts]["temp"].append(
                    Period(begin_time=self.times[i - 1], end_time=self.times[i])
                )

                # Store the DHMax to remove isolated phenomenon later
                dh_ts = (count / data_for_fixed_time.count()).item()

                ts_type = "visibility" if Wwmf.is_visibility(ts) else "precipitation"
                dh[ts_type] += dh_ts

            for ts_type in ["visibility", "precipitation"]:
                self.densities["DT"][ts_type] += dh[ts_type] / len(self.times)
                self.densities["DHmax"][ts_type] = max(
                    self.densities["DHmax"][ts_type], dh[ts_type]
                )

    def _pre_process(self):
        """Pre-processing step."""
        # Clean old values
        self._ts.clear()

        # Convert if necessary
        if self.weather_data["wwmf"].units == "w1":
            self.weather_data["wwmf"] = from_w1_to_wwmf(self.weather_data["wwmf"])

        # Replace current codes with nebulosity
        replacing_codes = {72: 71, 73: 70, 78: 77, 82: 81, 83: 80}
        for old, new in replacing_codes.items():
            self.weather_data["wwmf"] = self.weather_data["wwmf"].where(
                self.weather_data["wwmf"] != old, other=new
            )

        if "lpn" in self.weather_data:
            self._manage_lpn_inconstistencies()

        self._compute_densities()

        # Apply different rules
        self._process_densities()
        self._process_temporalities()

    def _process_densities(self):
        """Process all densities to remove isolated phenomena"""
        ts_to_exclude = []
        if not any(
            Wwmf.is_severe(ts) for ts in self._ts
        ) and not self.has_required_density("precipitation"):
            ts_to_exclude += [ts for ts in self._ts if Wwmf.is_precipitation(ts)]

        if not self.has_required_density("visibility") and not self.has_risk_fog:
            ts_to_exclude += [ts for ts in self._ts if Wwmf.is_visibility(ts)]

        for ts in ts_to_exclude:
            del self._ts[ts]

    def _process_temporalities(self):
        """
        Process all temporalities to remove short phenomena and apply grouping rules.

        This method reduces the temporalities and removes short phenomena from the data.
        It helps generate sentences and apply grouping rules accordingly.
        """
        ts_to_remove = []

        # Calculate the number of temporalities to keep based on the time range
        nbr_temporalities_to_keep = 2 + (self.times[-1] - self.times[0]).days

        for ts, info in self._ts.items():
            # Reduce the temporality using PeriodDescriber
            info["temp"] = self.period_describer.reduce(
                info["temp"], n=nbr_temporalities_to_keep
            )

            # Let temporalities with total hours greater than 3
            if info["temp"].total_hours >= 3:
                continue

            if Wwmf.is_visibility(ts) and self.has_risk_fog:
                continue

            if Wwmf.is_severe(ts):
                continue

            ts_to_remove.append(ts)

        # Remove the temporalities marked for removal
        for ts in ts_to_remove:
            del self._ts[ts]

    def _merge_ts_by_label(self, *args) -> List[tuple]:
        # Merge groups of TS with same labels
        labels = defaultdict(lambda: ([], {"temp": Periods()}))
        for ts_group, info in args:
            label = self.wwmf_utils.label(*ts_group)
            labels[label] = (
                labels[label][0] + ts_group,
                self._concat_infos(
                    info, labels[label][1], severe=info.get("is_severe", False)
                ),
            )

        # Sort the TS codes based on the begin_time of temporality
        return sorted(
            labels.values(),
            key=lambda x: (x[1]["temp"].begin_time, -x[1]["temp"].total_hours),
        )

    def _describe_label(self, ts_group, info):
        label = self.wwmf_utils.label(*ts_group)

        # Handle short severe phenomena - see #43300 and #38534
        if info["temp"].total_hours < 3:
            return self._("temporairement {label}").format(label=decapitalize(label))

        return label

    def _describe_temporality(self, info) -> Optional[str]:
        if (
            len(info["temp"]) == 1
            and info["temp"][0].begin_time <= self.times[0] + Timedelta(hours=3)
            and info["temp"][0].end_time >= self.times[-1] - Timedelta(hours=3)
        ):
            return None

        return self.period_describer.describe(info["temp"])

    def set_localisations(self, ts_group, info) -> Dict:
        localisations = {}
        for key, ts_family in [
            ("loc", ts_group),
            ("locVerglas", [ts for ts in ts_group if Wwmf.is_ice(ts)]),
            ("locNeige", [ts for ts in ts_group if Wwmf.is_snow(ts)]),
            ("locOrages", [ts for ts in ts_group if Wwmf.is_thunderstorm(ts)]),
        ]:
            loc, default_localisation = self._process_localisation(
                ts_family, info["temp"]
            )

            if default_localisation:
                localisations[f"{key}-suffix"] = f" {loc}"
            else:
                localisations[key] = loc
        return localisations

    def _describe(self, *args: int) -> List[Dict]:
        """
        Generate a dictionary of descriptions based on the list of TS codes.

        Args:
            *args: List of TS codes.

        Returns:
            Dictionaries of reduced data.
        """

        main_ts, severe_ts = [], []
        for ts_group, info in self._merge_ts_by_label(*args):
            # Handling of very localized phenomenons
            localisations = self.set_localisations(ts_group, info)
            if info.get("is_severe"):  # Handling of severe phenomenon
                severe_ts.append(
                    {
                        "key": "severe",
                        "lab": decapitalize(self.wwmf_utils.label(*ts_group)),
                    }
                    | localisations
                )
                continue

            # Check if there are multiple temporalities or if the first temporality
            # doesn't cover the entire requested time range
            temporality = self._describe_temporality(info)
            label = self._describe_label(ts_group, info)
            main_ts.append(
                {
                    "lab": label if temporality is None else decapitalize(label),
                    "key": "1xTS" if temporality is None else "1xTS_temp",
                    "temp": None if temporality is None else temporality.capitalize(),
                }
                | localisations
            )

        return (main_ts or [{"key": "0xTS"}]) + severe_ts

    def _concat_infos(self, *args, severe: bool = False) -> dict:
        """
        Concatenate information by summing the temporalities.

        Args:
            *args: List of TS codes.
            severe: Flag indicating if it's a severe phenomenon.

        Returns:
            dict: Concatenated information.
        """

        # Combine all the temporalities of the TS codes
        all_temporalities = Periods()
        for arg in args:
            all_temporalities += (arg if isinstance(arg, dict) else self._ts[arg])[
                "temp"
            ]

        result = {"temp": self.period_describer.reduce(all_temporalities)}
        if severe:
            result["is_severe"] = True

        return result

    def _process_localisation(
        self, wwmfs: List[int], temp: Periods
    ) -> Tuple[Optional[str], bool]:
        """
        Process localisation based on given wwmfs codes.

        This method processes the localisation based on data.
        It determines the location based on the map and altitude information.
        The determined location is assigned to the corresponding time series.

        Args:
            wwmfs: Wwmf codes to localise.
            temp: Temporality to consider.

        Returns:
            Tuple containing the best localized area name or None if not possible and a
            boolean indicating if it's  a default localisation (a less bad area).
        """
        if not wwmfs:
            return None, False

        # If there are snow and other kind of precipitations, only the snow is localized
        any_snow = any(Wwmf.is_snow(ts) for ts in wwmfs)
        if any_snow and any(not Wwmf.is_snow(ts) for ts in wwmfs):
            wwmfs = [ts for ts in wwmfs if Wwmf.is_snow(ts)]

        precipitation_map = (
            self.weather_data["wwmf"]
            .isin(wwmfs)
            .sel(
                valid_time=slice(
                    temp.begin_time.without_tzinfo, temp.end_time.without_tzinfo
                )
            )
            .sum("valid_time")
            > 0
        )

        geos_data = self.parent.geos_data(self.geo_id)
        geos_data_size = geos_data.sum().data

        # Determine the location based on map and altitude information
        if precipitation_map.sum().data / geos_data_size >= 0.9:
            return geos_data.altAreaName.item(), False

        geos_descriptive = self.parent.geos_descriptive(self.geo_id)

        # Hide the name of axis if very localized - see #45098
        if geos_descriptive.size == 0:
            return "", True

        iol, default_localisation = compute_iol(geos_descriptive, precipitation_map)

        if iol is not None and iol.sum().data / geos_data_size < 0.9:
            loc = concatenate_string(
                iol.areaName.values, last_delimiter=f" {self._('et')} "
            )
        else:
            # Hide the name of axis if very localized - see #45098
            loc = "" if default_localisation else geos_data.altAreaName.item()

        return loc, default_localisation

    def _merge_same_ts_family(self, *args: int) -> List[Tuple[List[int], dict]]:
        """
        This function takes a list of TS of the same family as an argument, merges them,
        and returns a list of tuples (list of TS, info) for all descriptions.

        Args:
            *args: Variable-length list of TS.

        Returns:
            List[Tuple[List[int], dict]]: List of tuples containing the TS code and
            information for each merged description.
        """
        ts1, ts2 = args[0], args[1]
        info1, info2 = self._ts[ts1], self._ts[ts2]

        if len(args) == 2:
            # If TS are considered to have different temporalities
            if (
                any(Wwmf.is_severe(wwmf) for wwmf in args)
                and info1["temp"].hours_of_intersection(info2["temp"])
                / info1["temp"].hours_of_union(info2["temp"])
                < 0.75
            ) or not self._are_same_temporalities(info1, info2):
                return [([ts1], info1), ([ts2], info2)]

            return [([ts1, ts2], self._concat_infos(ts1, ts2))]

        # In this case we have three args
        ts3 = args[2]

        # We try to gather two of them according to the same possible temporality
        # and TS
        for [_ts1, _ts2], [_ts3] in combinations_and_remaining([ts1, ts2, ts3], 2):
            if (
                self._are_same_temporalities(self._ts[_ts1], self._ts[_ts2])
                and not self._are_same_temporalities(self._ts[_ts1], self._ts[_ts3])
                and not self._are_same_temporalities(self._ts[_ts2], self._ts[_ts3])
            ):
                return [
                    ([_ts1, _ts2], self._concat_infos(_ts1, _ts2)),
                    ([_ts3], self._ts[_ts3]),
                ]

        # If we can't gather two of them with the same temporality and TS
        return [([ts1, ts2, ts3], self._concat_infos(ts1, ts2, ts3))]

    def _process(self) -> List[Dict]:
        """
        Post-processes the data to be treated by the template key selector.

        Returns:
            List[Dict]: Post-processed data.
        """
        nbr_ts = len(self._ts)
        if nbr_ts == 0:
            return self._process_0_ts()
        if nbr_ts == 1:
            return self._process_1_ts()
        if nbr_ts == 2:
            return self._process_2_ts()
        if nbr_ts == 3:
            return self._process_3_ts()
        return self._process_more_than_3_ts()

    def _process_0_ts(self) -> List[Dict]:
        """
        Post-processes data when there is no TS.

        Returns:
            List[Dict]: Post-processed data.
        """
        if not self.parent.nebulosity:
            return [{"key": "0xTS"}]

        most_common_ts = Counter(self._cloudiness).most_common(2)
        if len(most_common_ts) == 0:
            return [{"key": "0xTS"}]
        if len(most_common_ts) == 1:
            return [
                {
                    "key": "0xTS_nebulosity",
                    "lab": self.wwmf_utils.label(most_common_ts[0][0]),
                }
            ]

        ts1, ts2 = most_common_ts[0][0], most_common_ts[1][0]
        cloudiness_da = xr.DataArray(
            self._cloudiness,
            coords={"valid_time": [vt.as_np_dt64 for vt in self.times[1:]]},
        )
        cloudiness_da = cloudiness_da.where(
            cloudiness_da.isin([ts1, ts2]), drop=True
        ).interp_like(
            cloudiness_da, method="nearest", kwargs={"fill_value": "extrapolate"}
        )
        check_ts = [ts == cloudiness_da[0] for ts in cloudiness_da]
        idx = check_ts[1:].index(not check_ts[0]) + 1

        # Handle when two nebulosities follow each other
        if self.times[idx] > self.times[0] + Timedelta(hours=3) and all(
            check == check_ts[idx] for check in check_ts[idx + 1 :]
        ):
            label = Wwmf(
                ordered_keys=True,
                language=self.language,
                template_name="nebulosity_following_labels",
            ).label(
                cloudiness_da[0].item(),
                ts2 if cloudiness_da[0] == ts1 else ts1,
                concatenate=False,
            )

            if label is not None:
                return [
                    {
                        "key": "0xTS_nebulosity_following",
                        "lab": label,
                        "temp": self.period_describer.describe(
                            Period(begin_time=self.times[idx])
                        ),
                    }
                ]

        return [
            {
                "key": "0xTS_nebulosity",
                "lab": self.wwmf_utils.label(ts1, ts2, concatenate=False)
                or self.wwmf_utils.label(*self.default_cloudiness_grouping),
            }
        ]

    def _process_1_ts(self) -> List[Dict]:
        """
        Post-processes data when there is only one TS.

        Returns:
            List[Dict]: Post-processed data.
        """
        items_iter = iter(self._ts.items())
        ts1, info1 = next(items_iter)
        return self._describe(([ts1], info1))

    def _process_2_ts(self) -> List[Dict]:
        """
        Post-processes data when there are two TS.

        Returns:
            List[Dict]: Post-processed data.
        """
        items_iter = iter(self._ts.keys())
        ts1 = next(items_iter)
        ts2 = next(items_iter)

        # If families are different we don't merge even if temporalities are the same
        if Wwmf.is_visibility(ts1) ^ Wwmf.is_visibility(ts2):
            info1, info2 = [self._ts[ts] for ts in [ts1, ts2]]
            return self._describe(([ts1], info1), ([ts2], info2))

        descriptions = self._merge_same_ts_family(ts1, ts2)
        return self._describe(*descriptions)

    def _process_3_ts(self) -> List[Dict]:
        """
        Post-processes data when there are three TS.

        Returns:
            List[Dict]: Post-processed data.
        """
        items_iter = iter(self._ts.items())
        ts1, _ = next(items_iter)
        ts2, _ = next(items_iter)
        ts3, _ = next(items_iter)

        # Handle TS of same family
        if all(Wwmf.is_visibility(ts) for ts in [ts1, ts2, ts3]) or all(
            Wwmf.is_precipitation(ts) for ts in [ts1, ts2, ts3]
        ):
            descriptions = self._merge_same_ts_family(ts1, ts2, ts3)
            return self._describe(*descriptions)

        # Handle TS of different families
        if all(Wwmf.is_visibility(ts) for ts in [ts1, ts2]) or all(
            Wwmf.is_precipitation(ts) for ts in [ts1, ts2]
        ):
            same_family, other_family = [ts1, ts2], ts3
        elif all(Wwmf.is_visibility(ts) for ts in [ts1, ts3]) or all(
            Wwmf.is_precipitation(ts) for ts in [ts1, ts3]
        ):
            same_family, other_family = [ts1, ts3], ts2
        else:
            same_family, other_family = [ts2, ts3], ts1
        return self._describe(
            (same_family, self._concat_infos(*same_family)),
            ([other_family], self._ts[other_family]),
        )

    def _process_more_than_3_ts_visibilities(self) -> list:
        wwmfs = [wwmf for wwmf in self._ts.keys() if Wwmf.is_visibility(wwmf)]
        return [(wwmfs, self._concat_infos(*wwmfs))] if wwmfs else []

    def _process_more_than_3_ts_precipitations(self) -> list:
        wwmfs = [wwmf for wwmf in self._ts.keys() if Wwmf.is_precipitation(wwmf)]
        if not wwmfs:
            return []

        nbr_ts = len(wwmfs)
        if nbr_ts == 1:
            return [([wwmfs[0]], self._ts[wwmfs[0]])]
        if nbr_ts in [2, 3]:
            return self._merge_same_ts_family(*wwmfs)

        grp1, grp2, make_two_grps = [wwmfs[0]], [], True
        for ts in wwmfs[1:]:
            if self._are_same_temporalities(self._concat_infos(*grp1), self._ts[ts]):
                grp1.append(ts)
            elif not grp2 or self._are_same_temporalities(
                self._concat_infos(*grp2), self._ts[ts]
            ):
                grp2.append(ts)
            else:
                make_two_grps = False
                break

        make_two_grps &= all(
            (
                self.wwmf_utils.label(*grp1, concatenate=False) is not None,
                grp2,
                self.wwmf_utils.label(*grp2, concatenate=False) is not None,
            )
        )
        if not make_two_grps:
            if self.wwmf_utils.label(*wwmfs, concatenate=False) is not None:
                return [(wwmfs, self._concat_infos(*wwmfs))]
            grp1, grp2 = Wwmf.Subgrp.split_groups(*wwmfs)

        result = []
        if grp1:
            result.append((grp1, self._concat_infos(*grp1)))
        if grp2:
            result.append(
                (grp2, self._concat_infos(*grp2, severe=grp1 and not make_two_grps))
            )
        return result

    def _process_more_than_3_ts(self) -> List[Dict]:
        description_args = (
            self._process_more_than_3_ts_visibilities()
            + self._process_more_than_3_ts_precipitations()
        )
        return self._describe(*description_args)

    @cached_property
    def show_lpn(self) -> bool:
        return all(
            (
                "lpn" in self.weather_data,
                any(Wwmf.is_snow(wwmf) for wwmf in self._ts),
                not self.has_risk_snow,
                self.has_field("Neige", "LPN__SOL"),
            )
        )

    def _process_lpn(self) -> List[Dict]:
        if not self.show_lpn:
            return []

        lpn = int(
            round_to_closest_multiple(
                self.weather_data["lpn"]
                .where(Wwmf.is_snow(self.weather_data["wwmf"]))
                .min()
                .item(),
                100,
            )
        )
        if lpn <= max(self.parent.altitude("lpn").min().data, 0):
            return [{"key": "LPN_ground"}]
        return [{"key": "LPN", "low": lpn}]

    def compute_reduction(self) -> List[Dict]:
        self._pre_process()
        return self._process() + self._process_lpn()


class WeatherBuilder(SynthesisBuilder):
    """
    BaseBuilder class that must build texts for weather
    """

    reducer: Optional[WeatherReducer] = None
    reducer_class: type = WeatherReducer

    @property
    def template_name(self) -> str:
        return "weather"

    @property
    def template_key(self) -> str | List[str]:
        return [reduction["key"] for reduction in self.reduction]
