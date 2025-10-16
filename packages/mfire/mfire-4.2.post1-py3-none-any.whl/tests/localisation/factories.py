from typing import Annotated

from pydantic import SkipValidation

from mfire.localisation.risk_localisation import RiskLocalisation
from mfire.localisation.spatial_localisation import SpatialLocalisation
from mfire.localisation.table_localisation import TableLocalisation
from mfire.utils import mfxarray as xr
from mfire.utils.date import Datetime
from tests.composite.factories import (
    BaseCompositeFactory,
    RiskComponentCompositeFactory,
)
from tests.utils.factories import PeriodDescriberFactory


class SpatialLocalisationFactory(SpatialLocalisation, BaseCompositeFactory):
    parent: Annotated[RiskComponentCompositeFactory, SkipValidation] = (
        RiskComponentCompositeFactory(period_describer_factory=PeriodDescriberFactory())
    )
    geo_id: str = "geo_id"


class TableLocalisationFactory(TableLocalisation, BaseCompositeFactory):
    parent: Annotated[RiskComponentCompositeFactory, SkipValidation] = (
        RiskComponentCompositeFactory(period_describer_factory=PeriodDescriberFactory())
    )
    infos: xr.DataArray = xr.DataArray(coords={"id": []}, dims=["id"])
    spatial_localisation: SpatialLocalisationFactory = SpatialLocalisationFactory()

    alt_min: int = 100
    alt_max: int = 1000


class RiskLocalisationFactory(RiskLocalisation, BaseCompositeFactory):
    parent: Annotated[RiskComponentCompositeFactory, SkipValidation] = (
        RiskComponentCompositeFactory()
    )
    risk_level: int = 2
    geo_id: str = "geo_id"
    period: set = {Datetime(2023, 3, 1, 6)}
