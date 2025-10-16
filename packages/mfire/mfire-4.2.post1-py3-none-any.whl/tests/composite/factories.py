from __future__ import annotations

import random
from pathlib import Path
from typing import Annotated, Any, Dict, Generator, List, Optional

import numpy as np
from pydantic import Field

import mfire.utils.mfxarray as xr
from mfire.composite.aggregation import Aggregation, AggregationMethod, AggregationType
from mfire.composite.base import BaseComposite
from mfire.composite.component import (
    RiskComponentComposite,
    SynthesisComponentComposite,
    SynthesisCompositeInterface,
    SynthesisModule,
)
from mfire.composite.event import (
    Category,
    EventAccumulationComposite,
    EventComposite,
    Threshold,
)
from mfire.composite.field import FieldComposite, Selection
from mfire.composite.geo import AltitudeComposite, GeoComposite
from mfire.composite.level import LevelComposite, LocalisationConfig
from mfire.composite.operator import ComparisonOperator, LogicalOperator
from mfire.composite.period import PeriodComposite, PeriodsComposite
from mfire.composite.production import ProductionComposite
from mfire.composite.serialized_types import s_datetime, s_path, s_slice
from mfire.settings import SETTINGS_DIR
from mfire.settings.constants import LANGUAGES
from mfire.utils.date import Datetime
from tests.factories import Factory


class PeriodCompositeFactory(PeriodComposite):
    id: str = "period_id"
    name: Optional[str] = "period_name"
    start: s_datetime = Datetime(2023, 3, 1)
    stop: s_datetime = Datetime(2023, 3, 5)


class PeriodsCompositeFactory(PeriodsComposite):
    periods: List[PeriodComposite] = [PeriodCompositeFactory()]


class AggregationFactory(Aggregation):
    method: AggregationMethod = AggregationMethod.MEAN
    kwargs: dict = {}


class SelectionFactory(Selection):
    sel: dict = {"id": random.randint(0, 42)}
    islice: dict[str, s_slice | float] = {
        "valid_time": slice(random.randint(0, 42), random.randint(0, 42))
    }
    isel: dict = {"latitude": random.randint(0, 42)}
    slice: dict[str, s_slice] = {
        "longitude": slice(random.randint(0, 42), random.randint(0, 42))
    }


class BaseCompositeFactory(BaseComposite, Factory):
    _shared_config: dict = {"time_zone": "UTC", "language": "fr"}

    def iter_languages(self) -> Generator:
        for language in LANGUAGES:
            self.set_language(language)
            yield language


class ProductionCompositeFactory(ProductionComposite, BaseCompositeFactory):
    id: str = "production_id"
    name: str = "production_name"
    config_language: str = "fr"
    config_hash: str = "production_config_hash"
    config_time_zone: str = "UTC"
    mask_hash: str = "production_mask_hash"
    sort: float = 1.1
    components: List[
        RiskComponentCompositeFactory | SynthesisComponentCompositeFactory
    ] = []


class FieldCompositeFactory(FieldComposite, BaseCompositeFactory):
    """Field composite factory class."""

    file: Path | List[Path] = Path("field_composite_path")
    selection: Optional[Selection] = Selection()
    grid_name: str = "franxl1s100"
    name: str = "field_name"


class GeoCompositeFactory(GeoComposite, BaseCompositeFactory):
    """Geo composite factory class."""

    file: s_path = Path("geo_composite_file")
    mask_id: Optional[List[str] | str] = "mask_id"
    grid_name: Optional[str] = "franxl1s100"


class AltitudeCompositeFactory(AltitudeComposite, BaseCompositeFactory):
    """Altitude composite factory class."""

    filename: s_path = Path(SETTINGS_DIR / "geos/altitudes/franxl1s100.nc")
    grid_name: str = "franxl1s100"
    name: str = "name"


class EventCompositeFactory(EventComposite, BaseCompositeFactory):
    """Factory class for creating EventComposite objects."""

    field: FieldCompositeFactory = FieldCompositeFactory()
    category: Category = Category.BOOLEAN
    altitude: AltitudeCompositeFactory = AltitudeCompositeFactory()
    geos: GeoCompositeFactory | xr.DataArray = GeoCompositeFactory()
    plain: Optional[Threshold] = Threshold(
        threshold=20, comparison_op=ComparisonOperator.SUPEGAL, units="mm"
    )
    aggregation: Optional[Aggregation] = AggregationFactory()


class EventAccumulationCompositeFactory(
    EventAccumulationComposite, BaseCompositeFactory
):
    """Factory class for creating EventAccumulationComposite objects."""

    field: FieldCompositeFactory = FieldCompositeFactory()
    category: Category = Category.BOOLEAN
    altitude: AltitudeCompositeFactory = AltitudeCompositeFactory()
    geos: GeoCompositeFactory | xr.DataArray = GeoCompositeFactory()
    plain: Optional[Threshold] = Threshold(
        threshold=20, comparison_op=ComparisonOperator.SUPEGAL, units="mm"
    )
    aggregation: Optional[Aggregation] = AggregationFactory()

    field_1: FieldCompositeFactory = FieldCompositeFactory()
    cum_period: int = 6


class LevelCompositeFactory(LevelComposite, BaseCompositeFactory):
    level: int = 2
    aggregation: Optional[AggregationFactory] = None
    aggregation_type: AggregationType = AggregationType.UP_STREAM
    events: Annotated[
        List[EventAccumulationCompositeFactory | EventCompositeFactory],
        Field(discriminator="type"),
    ] = [EventCompositeFactory()]
    localisation: LocalisationConfig = LocalisationConfig()

    def __init__(self, **data: Any):
        events = data.get("events")
        if events is not None and data.get("logical_op_list") is None:
            logical_ops = [op.value for op in LogicalOperator]
            data["logical_op_list"] = list(
                np.random.choice(logical_ops, size=len(events) - 1)
            )
        super().__init__(**data)


class SynthesisComponentCompositeFactory(
    SynthesisComponentComposite, BaseCompositeFactory
):
    period: PeriodCompositeFactory = PeriodCompositeFactory()
    id: str = "text_component_id"
    name: str = "text_component_name"
    production_id: str = "production_id"
    production_name: str = "production_name"
    production_datetime: s_datetime = Datetime(2023, 3, 1, 6)

    weathers: List[SynthesisModuleFactory] = []
    product_comment: bool = True

    customer_id: Optional[str] = "customer_id"
    customer_name: Optional[str] = "customer_name"


class RiskComponentCompositeFactory(RiskComponentComposite, BaseCompositeFactory):
    period: PeriodCompositeFactory = PeriodCompositeFactory()
    id: str = "risk_component_id"
    name: str = "risk_component_name"
    production_id: str = "production_id"
    production_name: str = "production_name"
    production_datetime: s_datetime = Datetime(2023, 3, 1, 6)

    levels: List[LevelCompositeFactory] = []
    hazard_id: str = "hazard_id"
    hazard_name: str = "hazard_name"
    product_comment: bool = True
    params: Dict[str, FieldCompositeFactory] = {}

    customer_id: Optional[str] = "customer_id"
    customer_name: Optional[str] = "customer_name"


class SynthesisCompositeInterfaceFactory(
    SynthesisCompositeInterface, BaseCompositeFactory
):
    has_risk: Any = lambda x, y, z: None
    has_field: Any = lambda x, y, z: None
    get_risk_infos: Any = lambda v, w, x, y, z: {}


class SynthesisModuleFactory(SynthesisModule, BaseCompositeFactory):
    id: str = "id_weather"
    params: Dict[str, FieldCompositeFactory] = {}
    units: Dict[str, Optional[str]] = {}
    localisation: LocalisationConfig = LocalisationConfig()

    interface: SynthesisCompositeInterfaceFactory = SynthesisCompositeInterfaceFactory()

    @classmethod
    def create_factory(
        cls,
        geos_descriptive: list,
        valid_time: list,
        lon: list,
        lat: list,
        data_vars: dict,
        altitude: Optional[list],
        **kwargs,
    ) -> SynthesisModuleFactory:
        data_ds = xr.Dataset(
            data_vars=data_vars,
            coords={
                "id": "geo_id",
                "valid_time": valid_time,
                "latitude": lat,
                "longitude": lon,
            },
        )

        ids = [str(x) for x in range(len(geos_descriptive))]
        geos_descriptive = xr.DataArray(
            data=geos_descriptive,
            dims=["id", "latitude", "longitude"],
            coords={
                "id": ids,
                "latitude": lat,
                "longitude": lon,
                "areaType": (["id"], ["Axis"] + (len(ids) - 1) * [""]),
                "areaName": (
                    ["id"],
                    [f"à localisation N°{i + 1}" for i in range(len(ids))],
                ),
            },
        )
        compo = cls(
            parent=SynthesisComponentCompositeFactory(),
            weather_data_factory=lambda *_1, **_2: data_ds,
            production_datetime=data_ds.valid_time[0],
            geos_descriptive_factory=lambda _: geos_descriptive,
            altitude_factory=lambda _: xr.DataArray(
                data=altitude,
                dims=["latitude", "longitude"],
                coords={"latitude": lat, "longitude": lon},
            ),
            **kwargs,
        )

        geos_data = geos_descriptive.sum(dim="id").expand_dims({"id": ["geo_id"]}) > 0
        geos_data["areaType"] = (["id"], ["Axis"])
        geos_data["areaName"] = (["id"], ["domain"])
        geos_data["altAreaName"] = (["id"], ["domain"])
        compo.geos = GeoCompositeFactory(
            compute_factory=lambda: geos_data, mask_da_factory=geos_data, mask_id=None
        )
        return compo
