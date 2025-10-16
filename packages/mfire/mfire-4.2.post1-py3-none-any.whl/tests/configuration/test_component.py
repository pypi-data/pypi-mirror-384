from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from shapely import Point

from mfire.settings.constants import ROOT_DIR
from mfire.utils.date import Datetime
from mfire.utils.dict import recursive_replace
from tests.composite.factories import PeriodCompositeFactory, PeriodsCompositeFactory
from tests.configuration.factories import (
    AbstractComponentFactory,
    FeatureCollectionFactory,
    FeatureConfigFactory,
    RiskComponentFactory,
    RulesFactory,
    SynthesisComponentFactory,
)
from tests.functions_test import assert_identically_close


@patch("os.environ", {"MFIRE_DISABLE_PRECACHING": True})
class TestAbstractComponent:
    def test_processed_periods(self):
        periods = [
            PeriodCompositeFactory(id="id_0", start=Datetime(2023, 3, 1)),
            PeriodCompositeFactory(id="id_1", start=Datetime(2023, 3, 2)),
        ]
        processed_periods = PeriodsCompositeFactory(periods=periods)
        assert (
            AbstractComponentFactory(
                processed_periods=processed_periods, configuration={"period": "id_0"}
            ).processed_period
            == periods[0]
        )
        assert (
            AbstractComponentFactory(
                processed_periods=processed_periods, configuration={"period": "id_1"}
            ).processed_period
            == periods[1]
        )

    def test_processed_config(self, assert_equals_result):
        component = AbstractComponentFactory(
            configuration={"A": "B"}, processed_period_factory=PeriodCompositeFactory()
        )
        assert_equals_result(component.processed_config)
        assert component.configuration == {"A": "B"}

    def test_usable_geometries(self):
        component = AbstractComponentFactory()
        assert component.usable_geometries("not_good_geo_id") == []
        assert component.usable_geometries("FeatureConfigFactory.id") == [
            "eurw1s100",
            "eurw1s40",
            "glob01",
            "glob025",
            "globd01",
            "globd025",
        ]

    def test_box(self):
        component = AbstractComponentFactory(
            geos=FeatureCollectionFactory(
                features=[
                    FeatureConfigFactory(id="useless"),
                    FeatureConfigFactory(id="id1", geometry=Point((0, 0))),
                    FeatureConfigFactory(id="id2", geometry=Point((1, 1))),
                    FeatureConfigFactory(id="id3", geometry=Point((2, 2))),
                ]
            ),
            configuration={"geos": ["id1", "id2"], "geos_descriptive": ["id2", "id3"]},
        )
        assert_identically_close(component.box, ((2.26, -0.26), (-0.26, 2.26)))

    def test_selection(self, assert_equals_result):
        start_stop = (Datetime(2023, 3, 1), Datetime(2023, 3, 2))
        assert_equals_result(
            AbstractComponentFactory(box_factory=((0.0, 0.0), (1.0, 1.0))).selection(
                start_stop
            )
        )


@patch("os.environ", {"MFIRE_DISABLE_PRECACHING": True})
class TestRiskComponent:
    @pytest.mark.parametrize(
        "hazard_name,levels,expected",
        [
            # One level with one event
            (
                "Hazard",
                [{"elementsEvent": [{"field": "NEIPOT1__SOL"}]}],
                {"NEIPOT1__SOL"},
            ),
            # One level with two events
            (
                "Hazard",
                [
                    {
                        "elementsEvent": [
                            {"field": "EAU24__SOL"},
                            {"field": "PRECIPITATION3__SOL"},
                        ]
                    }
                ],
                {"EAU24__SOL", "PRECIPITATION3__SOL"},
            ),
            # Two levels with events
            (
                "Hazard",
                [
                    {
                        "elementsEvent": [
                            {"field": "FF__SOL"},
                            {"field": "RAF__HAUTEUR2"},
                        ]
                    },
                    {
                        "elementsEvent": [
                            {"field": "NEIPOT12__SOL"},
                            {"field": "PRECIPITATION3__SOL"},
                        ]
                    },
                ],
                {"FF__SOL", "RAF__HAUTEUR2", "NEIPOT12__SOL", "PRECIPITATION3__SOL"},
            ),
            # Hazard name = "Neige"
            (
                "Neige",
                [{"elementsEvent": [{"field": "NEIPOT1__SOL"}]}],
                {"NEIPOT1__SOL", "WWMF__SOL", "NEIPOT3__SOL"},
            ),
            # Hazard name = "Pluies"
            (
                "Pluies",
                [{"elementsEvent": [{"field": "EAU12__SOL"}]}],
                {"EAU12__SOL", "WWMF__SOL", "EAU1__SOL"},
            ),
        ],
    )
    def test_all_parameters(self, hazard_name, levels, expected):
        component = RiskComponentFactory(
            configuration={"levels": levels, "hazard_name": hazard_name}
        )
        assert component.all_parameters == expected

    @pytest.mark.parametrize(
        "level,configuration",
        [
            # Basic upstream level with 1 event
            (
                {
                    "level": 1,
                    "logicalOpList": [],
                    "aggregationType": "upStream",
                    "elementsEvent": [
                        {
                            "field": "FF__HAUTEUR10",
                            "category": "quantitative",
                            "plain": {
                                "threshold": 30,
                                "comparisonOp": "supegal",
                                "units": "km/k",
                            },
                        }
                    ],
                },
                {},
            ),
            # Downstream level with 1 event
            (
                {
                    "level": 2,
                    "logicalOpList": [],
                    "aggregation": {"method": "mean"},
                    "aggregationType": "downStream",
                    "elementsEvent": [
                        {
                            "field": "FF__HAUTEUR10",
                            "category": "quantitative",
                            "plain": {
                                "threshold": 30,
                                "comparisonOp": "supegal",
                                "units": "km/k",
                            },
                        }
                    ],
                },
                {},
            ),
            # Upstream level with 2 events
            (
                {
                    "level": 3,
                    "logicalOpList": ["or"],
                    "aggregationType": "upStream",
                    "elementsEvent": [
                        {
                            "field": "FF__HAUTEUR10",
                            "category": "quantitative",
                            "plain": {
                                "threshold": 30,
                                "comparisonOp": "supegal",
                                "units": "km/k",
                            },
                            "mountain": {
                                "threshold": 40,
                                "comparisonOp": "supegal",
                                "units": "km/k",
                            },
                        },
                        {
                            "field": "RAF__HAUTEUR10",
                            "category": "quantitative",
                            "plain": None,
                            "mountain": {
                                "threshold": 50,
                                "comparisonOp": "supegal",
                                "units": "km/k",
                            },
                        },
                    ],
                },
                {},
            ),
        ],
    )
    def test_process_level(self, level, configuration, assert_equals_result):
        component = RiskComponentFactory(
            data_config={
                ("file_id", "FF__HAUTEUR10"): [
                    {"local": Path("path_field_FF"), "geometry": "franxl1s100"}
                ],
                ("file_id", "RAF__HAUTEUR10"): [
                    {"local": Path("path_field_RAF"), "geometry": "franxl1s100"}
                ],
            },
            rules=RulesFactory(
                file_info_factory=pd.Series({"step": 12}),
                resource_handler_factory=lambda x, y, z: [{"local": x}],
            ),
            configuration=configuration,
            box_factory=((0.0, 0.0), (1.0, 1.0)),
        )

        assert_equals_result(
            recursive_replace(
                component.process_level(
                    level,
                    file_id="file_id",
                    start_stop=(Datetime(2023, 3, 1), Datetime(2023, 3, 2)),
                    mask_id="mask_id",
                ).model_dump(),
                f"{ROOT_DIR}/",
                "",
            )
        )

    @pytest.mark.parametrize(
        "event,configuration",
        [
            # Basic field
            (
                {
                    "field": "FF__HAUTEUR10",
                    "category": "quantitative",
                    "plain": {
                        "threshold": 30,
                        "comparisonOp": "supegal",
                        "units": "km/k",
                    },
                },
                {},
            ),
            # Basic field with alt_min and alt_max
            (
                {
                    "field": "FF__HAUTEUR10",
                    "category": "quantitative",
                    "plain": {
                        "threshold": 30,
                        "comparisonOp": "supegal",
                        "units": "km/h",
                    },
                },
                {"alt_min": 100, "alt_max": 600},
            ),
            # Mountain only case
            (
                {
                    "field": "FF__HAUTEUR10",
                    "category": "quantitative",
                    "plain": {
                        "threshold": 30,
                        "comparisonOp": "supegal",
                        "units": "km/k",
                    },
                    "alt_min": 200,
                },
                {},
            ),
            # Plain and only case
            (
                {
                    "field": "FF__HAUTEUR10",
                    "category": "quantitative",
                    "plain": {
                        "threshold": 30,
                        "comparisonOp": "supegal",
                        "units": "km/k",
                    },
                    "mountain": {
                        "threshold": 60,
                        "comparisonOp": "supegal",
                        "units": "km/k",
                    },
                    "altitude": [{"mountainThreshold": 600}],
                },
                {},
            ),
            # Aggregation test
            (
                {
                    "field": "FF__HAUTEUR10",
                    "category": "quantitative",
                    "plain": {
                        "threshold": 30,
                        "comparisonOp": "supegal",
                        "units": "km/k",
                    },
                    "aggregation": {"method": "requiredDensity", "kwargs": {"dr": 10}},
                },
                {},
            ),
            # Field with accumulation
            (
                {
                    "field": "EAU24__SOL",
                    "category": "quantitative",
                    "plain": {
                        "threshold": 30,
                        "comparisonOp": "supegal",
                        "units": "mm",
                    },
                },
                {},
            ),
            (
                {
                    "field": "NEIPOT12__SOL",
                    "category": "quantitative",
                    "plain": {
                        "threshold": 30,
                        "comparisonOp": "supegal",
                        "units": "mm",
                    },
                },
                {},
            ),
        ],
    )
    def test_process_event(self, event, configuration, assert_equals_result):
        component = RiskComponentFactory(
            rules=RulesFactory(
                file_info_factory=lambda _: pd.Series({"step": 12}),
                resource_handler_factory=lambda x, y, z: [{"local": x}],
            ),
            configuration=configuration,
            box_factory=((0.0, 0.0), (1.0, 1.0)),
            data_config={
                ("file_id", "FF__HAUTEUR10"): [
                    {"local": Path("path_field_FF"), "geometry": "franxl1s100"}
                ],
                ("file_id", "EAU24__SOL"): [
                    {"local": Path("path_field_EAU"), "geometry": "franxl1s100"}
                ],
                ("file_id", "NEIPOT12__SOL"): [
                    {"local": Path("path_field_NEIPOT"), "geometry": "franxl1s100"}
                ],
            },
        )
        assert_equals_result(
            recursive_replace(
                component.process_event(
                    event,
                    file_id="file_id",
                    start_stop=(Datetime(2023, 3, 1), Datetime(2023, 3, 2)),
                    mask_id="mask_id",
                    aggregation_aval={"method": "requiredDensity", "dr": 0.5},
                ).model_dump(),
                f"{ROOT_DIR}/",
                "",
            )
        )

    @pytest.mark.parametrize(
        "files_groups",
        [
            {(("file_id", Datetime(2023, 3, 1), Datetime(2023, 3, 2)),): "mask_id"},
            {
                (("file_id1", Datetime(2023, 3, 1), Datetime(2023, 3, 2)),): "mask_id1",
                (("file_id2", Datetime(2023, 3, 2), Datetime(2023, 3, 3)),): "mask_id2",
            },
            {
                (
                    ("file_id1", Datetime(2023, 3, 1), Datetime(2023, 3, 2)),
                    ("file_id2", Datetime(2023, 3, 2), Datetime(2023, 3, 3)),
                ): "mask_id1"
            },
        ],
    )
    def test_process_files_groups(self, files_groups, assert_equals_result):
        component = RiskComponentFactory(
            rules=RulesFactory(
                file_info_factory=lambda _: pd.Series({"step": 12}),
                resource_handler_factory=lambda x, y, z: [
                    {"local": x, "geometry": "franxl1s100"}
                ],
            ),
            configuration={
                "id": "component_id",
                "name": "component_name",
                "production_id": "production_id",
                "production_name": "production_name",
                "product_comment": True,
                "levels": [
                    {
                        "level": 1,
                        "logicalOpList": [],
                        "aggregationType": "upStream",
                        "elementsEvent": [
                            {
                                "field": "FF__HAUTEUR10",
                                "category": "quantitative",
                                "plain": {
                                    "threshold": 30,
                                    "comparisonOp": "supegal",
                                    "units": "km/k",
                                },
                            }
                        ],
                    },
                    {
                        "level": 2,
                        "logicalOpList": [],
                        "aggregation": {"method": "mean"},
                        "aggregationType": "downStream",
                        "elementsEvent": [
                            {
                                "field": "FF__HAUTEUR10",
                                "category": "quantitative",
                                "plain": {
                                    "threshold": 30,
                                    "comparisonOp": "supegal",
                                    "units": "km/k",
                                },
                            }
                        ],
                    },
                    {
                        "level": 3,
                        "logicalOpList": ["or"],
                        "aggregationType": "upStream",
                        "elementsEvent": [
                            {
                                "field": "FF__HAUTEUR10",
                                "category": "quantitative",
                                "plain": {
                                    "threshold": 30,
                                    "comparisonOp": "supegal",
                                    "units": "km/k",
                                },
                                "mountain": {
                                    "threshold": 40,
                                    "comparisonOp": "supegal",
                                    "units": "km/k",
                                },
                            },
                            {
                                "field": "RAF__HAUTEUR10",
                                "category": "quantitative",
                                "plain": None,
                                "mountain": {
                                    "threshold": 50,
                                    "comparisonOp": "supegal",
                                    "units": "km/k",
                                },
                            },
                        ],
                    },
                ],
                "hazard_id": "hazard_id",
                "hazard_name": "hazard_name",
            },
            box_factory=((0.0, 0.0), (1.0, 1.0)),
            processed_period_factory=PeriodCompositeFactory(),
        )

        assert_equals_result(
            [
                recursive_replace(compo.model_dump(), f"{ROOT_DIR}/", "")
                for compo in component.process_files_groups(files_groups)
            ]
        )


@patch("os.environ", {"MFIRE_DISABLE_PRECACHING": True})
class TestSynthesisComponent:
    def test_all_parameters(self):
        # Several synthesis components without condition
        component = SynthesisComponentFactory(
            configuration={
                "weather": [
                    {"id": "weather", "condition": None},
                    {"id": "tempe", "condition": {}},
                ]
            }
        )
        assert component.all_parameters == {
            "WWMF__SOL",
            "LPN__SOL",
            "T__HAUTEUR2",
            "PRECIP__SOL",
            "NEIPOT__SOL",
            "EAU__SOL",
        }

        # One synthesis component with a condition
        component = SynthesisComponentFactory(
            configuration={
                "weather": [{"id": "wind", "condition": {"field": "test_field"}}]
            }
        )
        assert component.all_parameters == {
            "test_field",
            "DD__HAUTEUR10",
            "RAF__HAUTEUR10",
            "FF__HAUTEUR10",
            "WWMF__SOL",
        }

    def test_grid_name(self):
        component = SynthesisComponentFactory(
            data_config={("file_id", "param_field"): [{"geometry": "grid_name"}]}
        )
        assert component.grid_name("file_id", {"field": "param_field"}) == "grid_name"

    def test_name(self):
        component = SynthesisComponentFactory(
            data_config={("file_id", "param_field"): [{"param": "name"}]}
        )
        assert component.name("file_id", {"field": "param_field"}) == "name"

    @pytest.mark.parametrize(
        "files_groups",
        [
            {(("file_id", Datetime(2023, 3, 1), Datetime(2023, 3, 2)),): "mask_id"},
            {
                (("file_id1", Datetime(2023, 3, 1), Datetime(2023, 3, 2)),): "mask_id1",
                (("file_id2", Datetime(2023, 3, 2), Datetime(2023, 3, 3)),): "mask_id2",
            },
        ],
    )
    @pytest.mark.parametrize(
        "weather",
        [
            # Basic components
            {"id": "weather"},
            {"id": "wind", "condition": None},
            {"id": "weather", "nebulosity": None},
            {"id": "weather", "nebulosity": False},
            {"id": "weather", "nebulosity": True},
            # Components with condition only on plain
            {
                "id": "weather",
                "condition": {
                    "field": "WWMF__SOL",
                    "plain": {
                        "threshold": [60, 61, 62, 63, 80],
                        "comparisonOp": "egal",
                        "units": "wwmf",
                    },
                    "category": "categorical",
                    "aggregation": None,
                },
            },
            {
                "id": "wind",
                "condition": {
                    "field": "T__HAUTEUR2",
                    "plain": {
                        "threshold": 20,
                        "comparisonOp": "supegal",
                        "units": "celsius",
                    },
                    "category": "quantitative",
                    "aggregation": {"method": "mean"},
                },
            },
            # Condition on mountain
            {
                "id": "tempe",
                "condition": {
                    "field": "RAF__HAUTEUR10",
                    "plain": None,
                    "mountain": {
                        "threshold": 40,
                        "comparisonOp": "supegal",
                        "units": "km/h",
                    },
                    "category": "quantitative",
                    "aggregation": {"method": "requiredDensity", "kwargs": {"dr": 5}},
                },
                "altitude": [{"mountainThreshold": 600}],
            },
            {
                "id": "weather",
                "condition": {
                    "field": "T__HAUTEUR2",
                    "plain": {
                        "threshold": 0,
                        "comparisonOp": "infegal",
                        "units": "celsius",
                    },
                    "mountain": {
                        "threshold": -5,
                        "comparisonOp": "infegal",
                        "units": "celsius",
                    },
                    "category": "quantitative",
                    "aggregation": None,
                },
                "altitude": [{"mountainThreshold": 600}],
            },
            # Test with different operator
            {
                "id": "weather",
                "condition": {
                    "field": "WWMF__SOL",
                    "plain": {
                        "threshold": [60, 61, 62, 63, 80],
                        "comparisonOp": "dif",
                        "units": "wwmf",
                    },
                    "category": "categorical",
                    "aggregation": None,
                },
            },
        ],
    )
    def test_process_weather(self, files_groups, weather, assert_equals_result):
        component = SynthesisComponentFactory(
            rules=RulesFactory(resource_handler_factory=lambda x, y, z: [{"local": x}]),
            configuration={
                "weather": [weather],
                "compass_split": True,
                "altitude_split": True,
                "geos_descriptive": ["config_geos_descriptive"],
            },
            box_factory=((0.0, 0.0), (1.0, 1.0)),
            processed_period_factory=PeriodCompositeFactory(),
            grid_name_factory=lambda _x, _y: "eurw1s40",
            name_factory=lambda _x, _y: "name_of_fields",
        )
        assert_equals_result(
            recursive_replace(
                component.process_weather(files_groups, weather).model_dump(),
                f"{ROOT_DIR}/",
                "",
            )
        )

    @pytest.mark.parametrize(
        "files_groups",
        [
            {(("file_id", Datetime(2023, 3, 1), Datetime(2023, 3, 2)),): "mask_id"},
            {
                (("file_id1", Datetime(2023, 3, 1), Datetime(2023, 3, 2)),): "mask_id1",
                (("file_id2", Datetime(2023, 3, 2), Datetime(2023, 3, 3)),): "mask_id2",
            },
        ],
    )
    def test_process_files_groups(
        self, files_groups, assert_equals_result, tmp_path_cwd
    ):
        component = SynthesisComponentFactory(
            rules=RulesFactory(resource_handler_factory=lambda x, y, z: [{"local": x}]),
            configuration={
                "id": "component_id",
                "name": "component_name",
                "production_id": "production_id",
                "production_name": "production_name",
                "product_comment": True,
                "weather": [
                    {
                        "id": "weather",
                        "condition": {
                            "field": "WWMF__SOL",
                            "plain": {
                                "threshold": [60, 61, 62, 63, 80],
                                "comparisonOp": "egal",
                                "units": "wwmf",
                            },
                            "category": "categorical",
                            "aggregation": None,
                        },
                    },
                    {"id": "tempe"},
                    {"id": "weather"},
                ],
                "compass_split": True,
                "altitude_split": True,
                "geos_descriptive": ["config_geos_descriptive"],
            },
            box_factory=((0.0, 0.0), (1.0, 1.0)),
            processed_period_factory=PeriodCompositeFactory(),
            grid_name_factory=lambda _x, _y: "eurw1s40",
            name_factory=lambda _x, _y: "name_of_fields",
        )
        assert_equals_result(
            [
                recursive_replace(compo.model_dump(), f"{ROOT_DIR}/", "")
                for compo in component.process_files_groups(files_groups)
            ]
        )
