from __future__ import annotations

from functools import cached_property
from typing import Annotated, Optional, Tuple

import numpy as np
from pydantic import SkipValidation

import mfire.utils.mfxarray as xr
from mfire.composite.base import BaseComposite
from mfire.composite.component import RiskComponentComposite
from mfire.composite.event import EventComposite
from mfire.composite.geo import GeoComposite
from mfire.composite.level import LevelComposite
from mfire.localisation.area_algebra import compute_iol, compute_iou_left
from mfire.settings import N_CUTS, get_logger
from mfire.utils.exception import LocalisationError, LocalisationWarning

# Logging
LOGGER = get_logger(name="localisation", bind="localisation")

# Threshold to consider that a set of zones covers the axis
DOMAIN_THRESHOLD = 0.9

ZONE_ZERO_COORDS = {
    "id": ["zero"],
    "areaName": (["id"], ["Zone Zero"]),
    "altAreaName": (["id"], ["Zone Zero"]),
    "areaType": (["id"], [""]),
}


class SpatialLocalisation(BaseComposite):
    parent: Annotated[RiskComponentComposite, SkipValidation]
    geo_id: str

    domain: xr.DataArray = None
    areas: xr.DataArray = None
    risk_ds: xr.Dataset = None
    default_localisation: Optional[bool] = None

    # percentage of the zone shared with the Axis needed be be considered
    # inside it
    MIN_ZONE_INCLUSION: float = 0.80

    @property
    def covers_domain(self) -> bool:
        return (
            not self.default_localisation
            and (self.areas.max("id").sum() / self.domain.sum()).data
            >= DOMAIN_THRESHOLD
        )

    @property
    def completed_areas(self) -> xr.DataArray:
        # Completion of areas by zero zone if there is not enough
        if not self.covers_domain and len(self.areas.id) < N_CUTS:
            return xr.concat(
                [self.areas, xr.DataArray(coords=ZONE_ZERO_COORDS, dims=["id"])],
                dim="id",
            )
        return self.areas

    @cached_property
    def risk_level(self) -> int:
        """
        Get the risk level for the composite and geographical area.

        The risk level is calculated using the `final_risk_max_level()` method of
        the composite.

        Returns:
            int: The risk level.
        """
        return self.parent.final_risk_max_level(self.geo_id)

    @cached_property
    def localised_risk_ds(self):
        """
        Computes the risk for the given level over the localized area for the full
        period.

        Returns:
            xr.Dataset: The Dataset containing the composite's risks.
        """
        # Create a new composite.
        new_component = self.parent.make_copy().reset()

        # Decrease the threshold in order to avoid ignoring the risk in selected areas
        # see #42267
        # must be [0,1]. area can be greater than domain whilst area
        # has no relation with or is not restricted to  domain
        threshold_factor = min(
            1.0, self.areas.max("id").sum().data / self.domain.sum().data
        )

        # Get the list of levels for the given risk level
        level_list = [
            lvl.multiply_all_dr_by(threshold_factor)
            for lvl in self.parent.levels_of_risk(level=self.risk_level)
        ]

        # For each level, force the calculation of the geographical areas and elements.
        for level in level_list:
            # For each event in the level, set the geos and the list of elements to
            # calculate.
            for event in level.events:
                event.geos = self.areas

        # Set the levels of the new composite.
        new_component.levels = level_list

        # Compute the new composite.
        return new_component.compute().sel(valid_time=self.risk_ds.valid_time)

    @cached_property
    def risk_areas(self) -> xr.DataArray:
        """
        Get the areas with occurrence for the localized risk.

        The areas with occurrence are the areas where the risk has a non-zero
        occurrence.

        Returns:
            xr.DataArray: A DataArray containing the areas with occurrence.
        """

        # Get occurrences
        occ_areas = self.localised_risk_ds["occurrence"].squeeze("risk_level")
        occ_axis = self.risk_ds["occurrence"].isel(id=0)

        # Avoid the occurrence on area if there is no risk in axis - see #42267
        occ_areas.values &= np.array([occ_axis.values] * len(occ_areas.id)).transpose()

        # Avoid to have no occurrence on all areas if there is risk in axis - see #42267
        for vt in occ_axis.where(
            occ_axis & ~occ_areas.max("id"), drop=True
        ).valid_time.values:
            argmax_idx = (
                self.localised_risk_ds["risk_density"].sel(valid_time=vt).argmax("id")
            ).item()
            occ_areas.loc[{"valid_time": vt}] = [
                i == argmax_idx for i in range(len(occ_areas.id))
            ]

        # Completion by a zero zone if necessary
        if not self.covers_domain and len(occ_areas.id) < N_CUTS:
            occ_areas = xr.concat(
                [occ_areas, xr.DataArray(False, coords=ZONE_ZERO_COORDS, dims=["id"])],
                dim="id",
            )

        # Return the areas with occurrence
        return occ_areas

    def _compute_event(self, event: EventComposite):
        # Filter the events in the best level to only include those in the
        # given geographical area.
        if isinstance(event.geos, GeoComposite):
            event_masks = event.geos.mask_id
            if isinstance(event_masks, str):
                event_masks = [event_masks]

            if self.geo_id in event_masks:
                event.geos.mask_id = [self.geo_id]
            else:
                raise LocalisationError(
                    f"Mask with id '{self.geo_id}' not available "
                    f"(among geocomposite {event_masks})."
                )
        else:
            if self.geo_id in event.geos.id:
                event.geos = event.geos.sel(id=self.geo_id)
            else:
                raise LocalisationError(
                    f"Mask with id '{self.geo_id}' not available "
                    f"(among xarray {event.geos.id.values})."
                )

    def compute(self) -> SpatialLocalisation:
        """
        Localizes a risk to a specific geographical area.

        Returns:
            The computed object.

        Raises:
            LocalisationWarning: Raised when null risk level
        """
        if self.risk_level == 0:
            raise LocalisationWarning(
                "RiskLocalisation is only possible for risk level > 0."
            )
        hourly_maxi_risk = self.parent.final_risk_da.sel(id=self.geo_id)
        periods = set(
            hourly_maxi_risk.sel(
                valid_time=(hourly_maxi_risk == self.risk_level)
            ).valid_time.data.astype("datetime64[ns]")
        )

        # Find the best configuration for the given risk level and period.
        level, periods = self._find_configuration(periods)

        # Check if the risk is downstream. We can only localize downstream risks.
        if level.aggregation_type != "downStream":
            raise LocalisationWarning(
                "RiskLocalisation is only possible for downstream risk."
            )

        # Filter the events to only include those in the given geographical area.
        for event in level.events:
            self._compute_event(event)

        # Compute the domain and areas
        self._compute_domain_and_areas(level, periods)

        return self

    def _compute_domain_and_areas(self, level: LevelComposite, periods: list):
        """
        Finds the possible localisation areas.

        Args:
            level: Level element.
            periods: List of periods.

        Raises:
            LocalisationWarning: If there are no areas for localisation.
        """
        # Get the spatial information for the best level.
        geos = level.events[0].geos

        # If the spatial information is a `GeoComposite` object, convert it to a
        # `DataArray` object with the specified grid name and `mask_id` set to `None`.
        if isinstance(geos, GeoComposite):
            geos = geos.make_copy()
            geos.mask_id = None
            geos = geos.compute()

        # Select the domain from the full list.
        self.domain = geos.sel(id=self.geo_id)

        # Get the list of IDs of the localisation areas.
        id_list = [
            id
            for id in geos.id.data
            if id.startswith(self.geo_id) and id != self.geo_id
        ]

        # Select the localisation areas from the full list.
        # We also drop the areas that are not compatible with the `compass_split`
        # and `altitude_split` parameters.
        selected_area, drop_ids = geos.sel(id=id_list), []
        if not level.localisation.compass_split:
            compass_idx = selected_area["areaType"] == "compass"
            drop_ids.extend(selected_area.sel(id=compass_idx).id.values)
        if not level.localisation.altitude_split:
            alt_idx = selected_area["areaType"] == "Altitude"
            drop_ids.extend(selected_area.sel(id=alt_idx).id.values)

        # Add the descriptive geos to the list of IDs.
        id_list.extend(level.localisation.geos_descriptive)
        id_list = list(set(id_list).difference(set(drop_ids)))

        # Raise a warning if there are no areas for localisation.
        if not id_list:
            raise LocalisationWarning("There is no area for localisation process.")

        # Select the localisation areas from the full list.
        areas = geos.sel(id=id_list).dropna("id", how="all")

        # Update the period to the specified period. We do this for all risks
        # except for accumulation risks, which require the entire dataset to be
        # calculated.
        if not level.is_accumulation:
            level.update_selection(new_sel={"valid_time": periods})

        self.risk_ds = level.compute()
        full_risk = level.spatial_risk_da

        # If the risk is an accumulation risk, select the specified period.
        if level.is_accumulation:
            full_risk = full_risk.sel({"valid_time": periods})

        # Squeeze the `full_risk` DataArray to remove the `id` dimension.
        full_risk = (
            full_risk.squeeze("id").reset_coords("id", drop=True).sum("valid_time") > 0
        )
        # limit research to pertinent areas for the axis
        # to avoid selection of areas with too few relation with axis
        inclus = compute_iou_left(areas, self.domain)
        touching_areas = inclus.where(
            inclus > self.MIN_ZONE_INCLUSION, drop=True
        ).id.data
        areas = areas.sel(id=touching_areas)

        # Get the best areas by using IoL algorithm
        iol, self.default_localisation = compute_iol(areas, full_risk)

        # Raise a warning if there are no areas for localisation.
        if iol is None:
            raise LocalisationWarning("There is no area selected.")

        if self.default_localisation:
            self.areas = areas.sel(id=[iol.id[0].item()])

            # For special risk using DDI
            self.areas["areaName"] = (
                ["id"],
                [f"{self._('très localisé')} {self.areas['areaName'].item()}"],
            )
        else:
            self.areas = areas.sel(id=iol.id[:3])

        # If the selected areas are not enough to represent the axis we drop the
        # last one in order to be able the use multizone templates
        if len(self.areas.id) == N_CUTS and not self.covers_domain:
            self.areas = self.areas.isel(id=range(N_CUTS - 1))

    def _find_configuration(self, periods: set) -> Tuple[LevelComposite, list]:
        """
        Finds the best configuration for the given periods.

        The best configuration is the one with the most common periods with the
        input period. If there is a tie, the configuration with the earliest first
        period is chosen. If there is still a tie, the configuration with the most
        common periods is chosen.

        Args:
            periods: Period we are interested in.

        Returns:
            Tuple containing respectively:
                - The best level of the list for localisation.
                - The list of period to localise for this risk.

        Raises:
            ValueError: If no configuration with a common period is found.
        """
        best_level, best_periods = None, None

        # Iterate over the levels in the list and find the best match.
        for level in self.parent.levels_of_risk(level=self.risk_level):
            # Get the period covered by the current level.
            level_period = set(level.cover_period)

            # Find the intersection of the input period and the level period.
            common_periods = sorted(periods.intersection(level_period))

            # If there are no common periods, skip this level
            if len(common_periods) == 0:
                continue

            # Update best_periods and level
            if (
                best_periods is None
                or (
                    common_periods[0] < min(best_periods)
                    and len(common_periods) >= len(best_periods) / 4
                )
                or (
                    common_periods[0] > min(best_periods)
                    and len(common_periods) >= 4 * len(best_periods)
                )
            ):
                best_level = level.make_copy().reset()
                best_periods = set(common_periods)

        # If we haven't found any level with a common period, raise an error.
        if best_level is None:
            raise ValueError("Best conf not found")

        return best_level, list(best_periods)
