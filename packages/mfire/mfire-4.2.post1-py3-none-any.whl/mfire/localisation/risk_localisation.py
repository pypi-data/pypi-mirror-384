from __future__ import annotations

from typing import Annotated, Optional

from pydantic import SkipValidation, model_validator

from mfire.composite.base import BaseComposite
from mfire.composite.component import RiskComponentComposite
from mfire.localisation.spatial_localisation import SpatialLocalisation
from mfire.localisation.table_localisation import TableLocalisation
from mfire.localisation.temporal_localisation import TemporalLocalisation
from mfire.settings import get_logger
from mfire.utils.exception import LocalisationWarning

# Logging
LOGGER = get_logger(name="localisation", bind="localisation")


class RiskLocalisation(BaseComposite):
    parent: Annotated[Optional[RiskComponentComposite], SkipValidation] = None
    geo_id: str

    alt_min: Optional[int] = None
    alt_max: Optional[int] = None

    spatial_localisation: Optional[SpatialLocalisation] = None
    temporal_localisation: Optional[TemporalLocalisation] = None
    table_localisation: Optional[TableLocalisation] = None

    def compute(self) -> RiskLocalisation:
        """
        Compute the localized risk. This method performs the spatial and temporal
        localisation of the risk.

        Returns:
            The computed object.

        Raises:
            LocalisationWarning: Raised when it's monozone case.
        """

        # Perform the spatial localisation.
        self.spatial_localisation = SpatialLocalisation(
            parent=self.parent, geo_id=self.geo_id
        ).compute()
        self.temporal_localisation = TemporalLocalisation(
            data=self.spatial_localisation.risk_areas
        )
        table_3p = self.temporal_localisation.compute()

        # If all the temporal periods are on the same areas and those areas cover almost
        # the entire axis, we can set the risk to be monozone.
        identical_period = True
        for zones_idx in range(1, table_3p.sizes["period"]):
            if (table_3p[0, :] != table_3p[zones_idx, :]).any() and (
                table_3p[zones_idx, :] != 0
            ).any():
                identical_period = False
                break

        if identical_period and self.spatial_localisation.covers_domain:
            raise LocalisationWarning("Localised zones merely cover axe.")

        # Finally, aggregate the risk temporally.
        self.table_localisation = TableLocalisation(
            parent=self.parent,
            spatial_localisation=self.spatial_localisation,
            infos=table_3p,
            alt_min=self.alt_min,
            alt_max=self.alt_max,
        ).compute()
        return self

    @model_validator(mode="after")
    def init_alt_min_and_alt_max(self) -> RiskLocalisation:
        """
        Initializes the `alt_min` and `alt_max` attributes of the `RiskLocalisation`
        instance.

        Returns:
            Dictionary containing the updated values of the `RiskLocalisation` instance.
        """
        max_level = self.parent.final_risk_max_level(self.geo_id)
        levels = self.parent.levels
        if max_level > 0:
            levels = self.parent.levels_of_risk(level=max_level)

        self.alt_min = min((lvl.alt_min for lvl in levels), default=None)
        self.alt_max = max((lvl.alt_max for lvl in levels), default=None)
        return self

    @property
    def periods_name(self) -> list:
        return list(self.table_localisation.infos.period.values.tolist())

    @property
    def unique_name(self) -> str:
        return self.table_localisation.name

    @property
    def is_multizone(self) -> bool:
        """
        Checks whether the localized risk is multizone.

        A localized risk is multizone if it covers multiple areas.

        Returns:
            bool: True if the localized risk is multizone, False otherwise.
        """
        return self.table_localisation is not None and (
            len(self.table_localisation.table) > 1
            or self.spatial_localisation.default_localisation
        )

    @property
    def all_name(self) -> str:
        data = self.table_localisation.infos
        if data.raw[0] == "0":
            areas_idx = [str(i + 2) for i in range(len(data) - 1)]
        else:
            areas_idx = [str(i + 1) for i in range(len(data))]

        return self.table_localisation.table["zone" + "_".join(areas_idx)]
