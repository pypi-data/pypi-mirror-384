from pathlib import Path
from typing import List, Optional

from shapely.geometry.base import BaseGeometry

from mfire.composite.serialized_types import s_datetime
from mfire.configuration.component import (
    AbstractComponent,
    RiskComponent,
    SynthesisComponent,
)
from mfire.configuration.geo import FeatureCollection, FeatureConfig
from mfire.configuration.period import PeriodMultiple, PeriodSingle
from mfire.configuration.processor import Processor
from mfire.configuration.production import Production
from mfire.configuration.rules import Rules
from mfire.utils.date import Datetime
from tests.composite.factories import PeriodsCompositeFactory
from tests.factories import Factory


class PeriodSingleFactory(PeriodSingle):
    id: str = "PeriodSingle.id"
    name: Optional[str] = "PeriodSingle.name"


class PeriodMultipleFactory(PeriodMultiple):
    id: str = "PeriodMultiple.id"
    name: Optional[str] = "PeriodMultiple.name"

    period_elements: List[PeriodSingleFactory] = [PeriodSingleFactory(start=6, stop=20)]


class FeatureConfigFactory(FeatureConfig):
    id: str = "FeatureConfigFactory.id"
    geometry: Optional[dict | BaseGeometry] = {
        "type": "Polygon",
        "coordinates": [
            [
                [13.38272, 52.46385],
                [13.42786, 52.46385],
                [13.42786, 52.48445],
                [13.38272, 52.48445],
                [13.38272, 52.46385],
            ]
        ],
    }


class FeatureCollectionFactory(FeatureCollection):
    features: List[FeatureConfigFactory] = [FeatureConfigFactory()]


class RulesFactory(Factory, Rules):
    name: str = "alpha"
    drafting_datetime: Optional[s_datetime] = Datetime(2023, 3, 1)


class ProductionFactory(Factory, Production):
    global_hash: str = "Production.global_hash"
    rules: RulesFactory = RulesFactory()
    configuration: dict = {
        "date_config": "20230301T063000",
        "production_id": "Production.production_id",
        "production_name": "Production.production_name",
        "production_language": "Production.language",
        "geos": [FeatureConfigFactory()],
        "periods": [PeriodSingleFactory(start=6, stop=8)],
        "components": [],
    }


class AbstractComponentFactory(Factory, AbstractComponent):
    rules: RulesFactory = RulesFactory()
    configuration: dict = {}
    configuration_datetime: Datetime = Datetime(2023, 3, 1)
    processed_periods: PeriodsCompositeFactory = PeriodsCompositeFactory()

    mask_config: dict = {
        "file": Path("MaskConfig.file"),
        "id": "MaskConfig.id",
        "name": "MaskConfig.name",
        "config_hash": "MaskConfig.config_hash",
        "geos": FeatureCollectionFactory(),
    }

    geos: FeatureCollectionFactory = FeatureCollectionFactory()

    def process_files_groups(self, files_groups: dict):
        return

    @property
    def all_parameters(self):
        return


class RiskComponentFactory(Factory, RiskComponent):
    rules: RulesFactory = RulesFactory()
    configuration: dict = {}
    configuration_datetime: Datetime = Datetime(2023, 3, 1)
    processed_periods: PeriodsCompositeFactory = PeriodsCompositeFactory()

    mask_config: dict = {
        "file": Path("MaskConfig.file"),
        "id": "MaskConfig.id",
        "name": "MaskConfig.name",
        "config_hash": "MaskConfig.config_hash",
        "geos": FeatureCollectionFactory(),
    }

    geos: FeatureCollectionFactory = FeatureCollectionFactory()


class SynthesisComponentFactory(Factory, SynthesisComponent):
    rules: RulesFactory = RulesFactory()
    configuration: dict = {}
    configuration_datetime: Datetime = Datetime(2023, 3, 1)
    processed_periods: PeriodsCompositeFactory = PeriodsCompositeFactory()

    mask_config: dict = {
        "file": Path("MaskConfig.file"),
        "id": "MaskConfig.id",
        "name": "MaskConfig.name",
        "config_hash": "MaskConfig.config_hash",
        "geos": FeatureCollectionFactory(),
    }

    geos: FeatureCollectionFactory = FeatureCollectionFactory()


class ProcessorFactory(Factory, Processor):
    configuration_path: Path = Path("Processor.configuration_path")
    rules: str | Rules = RulesFactory()
    drafting_datetime: Datetime | str = Datetime(2023, 3, 1)
