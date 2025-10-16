from pathlib import Path
from unittest.mock import patch

import pytest

from mfire.configuration.geo import FeatureCollection
from mfire.settings.constants import ROOT_DIR
from mfire.utils.dict import recursive_replace
from mfire.utils.exception import ConfigurationError
from mfire.utils.json import JsonFile
from tests.configuration.factories import (
    FeatureConfigFactory,
    PeriodMultipleFactory,
    ProductionFactory,
)


@patch("os.environ", {"MFIRE_DISABLE_PRECACHING": True})
class TestProduction:
    inputs_dir: Path = Path(__file__).parent / "inputs"
    components: dict = JsonFile(inputs_dir / "small_config.json").load()[0][
        "components"
    ]

    def test_id(self):
        assert ProductionFactory().id == "Production.production_id"
        assert ProductionFactory(configuration={}).id == "UnknownProductionID"

    def test_name(self):
        assert ProductionFactory().name == "Production.production_name"
        assert (
            ProductionFactory(configuration={"production_id": "ProdId"}).name
            == "UnknownProductionName_ProdId"
        )
        assert (
            ProductionFactory(configuration={}).name
            == "UnknownProductionName_UnknownProductionID"
        )

    def test_language(self):
        assert ProductionFactory().language == "Production.language"
        assert ProductionFactory(configuration={}).language == "fr"

    def test_time_zone(self):
        assert ProductionFactory(configuration={"time_zone": "XXX"}).time_zone == "XXX"
        with patch(
            "timezonefinder.TimezoneFinder.timezone_at", lambda *args, **_kwargs: None
        ):
            assert ProductionFactory().time_zone == "Europe/Paris"
        assert ProductionFactory().time_zone == "Europe/Berlin"

    def test_geos(self):
        geos = ProductionFactory().geos
        assert isinstance(geos, FeatureCollection)
        assert len(geos.features) == 1

        with pytest.raises(
            ConfigurationError, match="Failed to create GeoJSON FeatureCollection"
        ):
            _ = ProductionFactory(configuration={"geos": ...}).geos

    def test_mask_config(self, assert_equals_result):
        assert_equals_result(ProductionFactory().mask_config)

    def test_processed_hazards(self):
        production = ProductionFactory(
            configuration={
                "hazards": [{"id": "id1", "a": "b"}, {"id": "id2", "c": "d"}]
            }
        )
        processed_hazards = production.processed_hazards
        assert processed_hazards == {
            "id1": {"id": "id1", "a": "b"},
            "id2": {"id": "id2", "c": "d"},
        }

        # Test the deepcopy
        production.configuration["hazards"][0]["a"] = "e"
        assert processed_hazards == {
            "id1": {"id": "id1", "a": "b"},
            "id2": {"id": "id2", "c": "d"},
        }

    def test_all_configurations(self, assert_equals_result):
        assert_equals_result(
            ProductionFactory(
                configuration={
                    "components": self.components,
                    "geos": [
                        {
                            "id": "eur",
                            "geometry": {
                                "coordinates": [
                                    [
                                        [1.0, 45.0],
                                        [1.0, 44.9],
                                        [2.0, 44.9],
                                        [2.0, 45.0],
                                        [1.0, 45.0],
                                    ]
                                ],
                                "type": "Polygon",
                            },
                        },
                        {
                            "id": "global",
                            "geometry": {
                                "coordinates": [
                                    [
                                        [1.0, 45.0],
                                        [1.0, 44.9],
                                        [2.0, 44.9],
                                        [2.0, 45.0],
                                        [1.0, 45.0],
                                    ]
                                ],
                                "type": "Polygon",
                            },
                        },
                    ],
                }
            ).all_configurations
        )

        # Error in configuration
        assert not ProductionFactory(
            configuration={
                "components": [{"data": {"type": "risk", "hazards": [{"levels": ...}]}}]
            }
        ).all_configurations

    @patch("os.environ", {"MFIRE_DISABLE_PRECACHING": True})
    def test_process(self, assert_equals_result):
        production = ProductionFactory(
            configuration={
                "date_config": "20230301T063000",
                "periods": [
                    PeriodMultipleFactory(id="751410a0-a404-45de-8548-1944af4c6e60")
                ],
                "geos": [
                    FeatureConfigFactory(id="eur"),
                    FeatureConfigFactory(id="global"),
                ],
                "components": self.components,
            },
            processed_hazards_factory={},
        )

        result = list(production.process())
        result[0] = recursive_replace(result[0], f"{ROOT_DIR}/", "")
        assert_equals_result(result)

    def test_process_fails(self):
        production = ProductionFactory()
        with pytest.raises(
            ConfigurationError, match="No valid components found for 0 configurations"
        ):
            production.process()
