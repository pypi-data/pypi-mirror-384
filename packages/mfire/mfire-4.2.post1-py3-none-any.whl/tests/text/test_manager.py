from functools import partial
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from mfire.composite.production import ProductionComposite
from mfire.settings.constants import LANGUAGES
from mfire.text.manager import Manager
from mfire.utils import recursive_format
from mfire.utils.date import Datetime
from mfire.utils.json import JsonFile
from tests.composite.factories import (
    PeriodCompositeFactory,
    RiskComponentCompositeFactory,
    SynthesisComponentCompositeFactory,
    SynthesisCompositeInterfaceFactory,
    SynthesisModuleFactory,
)
from tests.text.base.factories import BaseBuilderFactory
from tests.text.factories import ManagerFactory


class TestManager:
    @pytest.mark.parametrize(
        "period_start,production_datetime",
        [
            (Datetime("20230301T07"), Datetime("20230102")),
            (Datetime("20230102"), Datetime("20230301T06")),
        ],
    )
    def test_compute_empty(
        self, period_start, production_datetime, assert_equals_result
    ):
        manager = ManagerFactory(
            parent=SynthesisComponentCompositeFactory(
                period=PeriodCompositeFactory(
                    start=period_start, stop=Datetime("20230302T06")
                ),
                production_datetime=production_datetime,
            )
        )

        assert_equals_result(
            {language: manager.compute() for language in manager.iter_languages()}
        )

    def test_compute_risk(self):
        manager = ManagerFactory(
            parent=RiskComponentCompositeFactory(),
            builders={
                "risk": partial(
                    BaseBuilderFactory, compute_factory=lambda: "RiskBuilder Text"
                )
            },
        )
        assert manager.compute() == "RiskBuilder Text"

    def test_compute_synthesis(self, assert_equals_result):
        manager = ManagerFactory(
            parent=SynthesisComponentCompositeFactory(
                weathers=[
                    SynthesisModuleFactory(id="tempe"),
                    SynthesisModuleFactory(id="weather"),
                    SynthesisModuleFactory(id="wind"),
                ]
            ),
            builders={
                "tempe": partial(
                    BaseBuilderFactory, compute_factory=lambda: "Temperature Text"
                ),
                "weather": partial(
                    BaseBuilderFactory, compute_factory=lambda: "Weather Text"
                ),
                "wind": partial(
                    BaseBuilderFactory, compute_factory=lambda: "Wind Text"
                ),
            },
        )
        assert_equals_result(
            {language: manager.compute() for language in manager.iter_languages()}
        )


class TestManagerValidation:
    inputs_dir: Path = Path(__file__).parent / "inputs" / "text_manager"

    @pytest.mark.validation
    @pytest.mark.parametrize("language", LANGUAGES)
    @pytest.mark.parametrize("period", ["20230309", "20230319", "20230401", "20230402"])
    @patch(
        "mfire.composite.component.TEXT_ALGO",
        {
            "weather": {
                "generic": {
                    "params": {"wwmf": {"field": "WWMF__SOL", "default_units": "wwmf"}}
                }
            },
            "tempe": {
                "generic": {
                    "params": {"tempe": {"field": "T__HAUTEUR2", "default_units": "°C"}}
                }
            },
            "wind": {
                "generic": {
                    "params": {
                        "wind": {"field": "FF__HAUTEUR10", "default_units": "km/h"},
                        "gust": {"field": "RAF__HAUTEUR10", "default_units": "km/h"},
                        "direction": {"field": "DD__HAUTEUR10", "default_units": "°"},
                        "wwmf": {"field": "WWMF__SOL", "default_units": "wwmf"},
                    }
                }
            },
        },
    )  # this patch avoids to have to use all (useless) data files for weather
    def test_compute_synthesis(self, language, period, assert_equals_result):
        inputs_dir = self.inputs_dir / "synthesis"
        config = JsonFile(inputs_dir / f"prod_task_config_{period}.json").load()

        # Replace "test_data_dir" by appropriate values
        data: dict = recursive_format(
            config,
            values={
                "language": language,
                "data_dir": str(inputs_dir / period),
                "masks_dir": str(inputs_dir / "masks"),
            },
        )

        result = {}
        for production_data in data.values():
            production = ProductionComposite(**production_data)

            for component in production.components:
                # Handling the interface between risk and synthesis
                for weather in component.weathers:
                    weather.interface = SynthesisCompositeInterfaceFactory()

                # Computation
                for geo_id in component.geos:
                    text_manager = Manager(parent=component, geo_id=geo_id)
                    result[f"{component.name} > {geo_id}"] = text_manager.compute()

        assert_equals_result(result)

    @pytest.mark.validation
    @pytest.mark.parametrize("language", LANGUAGES)
    @pytest.mark.parametrize("period", ["20220401T070000", "20210115T130000"])
    def test_compute_risk(self, language, period, root_path_cwd, assert_equals_result):
        np.random.seed(0)
        inputs_dir = self.inputs_dir / "risk"
        config = JsonFile(inputs_dir / period / "prod_task_config.json").load()

        result = {}

        # Replace "test_data_dir" by appropriate values
        data: dict = recursive_format(
            config,
            values={
                "language": language,
                "inputs_dir": str(inputs_dir),
                "altitudes_dir": (
                    root_path_cwd / "mfire" / "settings" / "geos" / "altitudes"
                ),
            },
        )

        for production_data in data.values():
            production = ProductionComposite(**production_data)
            for component in production.components:
                component.compute()
                for geo_id in component.geos:
                    result[
                        f"{component.name} > {component.hazard_name} > "
                        f"{component.area_name(geo_id)}"
                    ] = Manager(parent=component, geo_id=geo_id).compute()

        assert_equals_result(result)
