import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.composite.aggregation import AggregationMethod
from mfire.composite.event import Category, Threshold
from mfire.composite.operator import ComparisonOperator
from mfire.text.risk.reducer import (
    RiskReducerStrategyME,
    RiskReducerStrategyMonozone,
    RiskReducerStrategyMultizone,
    RiskReducerStrategyRain,
    RiskReducerStrategySnow,
)
from mfire.utils.date import Datetime
from tests.composite.factories import (
    BaseCompositeFactory,
    EventCompositeFactory,
    FieldCompositeFactory,
    LevelCompositeFactory,
    RiskComponentCompositeFactory,
)
from tests.functions_test import assert_identically_close
from tests.localisation.factories import (
    RiskLocalisationFactory,
    SpatialLocalisationFactory,
    TableLocalisationFactory,
)
from tests.text.risk.factories import (
    RiskReducerFactory,
    RiskReducerStrategyFactory,
    RiskReducerStrategyMEFactory,
    RiskReducerStrategyRainFactory,
    RiskReducerStrategySnowFactory,
)


class TestRiskReducer:
    def test_alt_area_name(self):
        assert (
            RiskReducerFactory(
                geo_id="XXX",
                parent=RiskComponentCompositeFactory(
                    alt_area_name_factory=lambda x: f"Nom zone {x}"
                ),
            ).alt_area_name
            == "Nom zone XXX"
        )

    def test_strategy(self):
        assert isinstance(
            RiskReducerFactory(
                parent=RiskComponentCompositeFactory(hazard_name="Neige")
            ).strategy,
            RiskReducerStrategySnow,
        )
        assert isinstance(
            RiskReducerFactory(
                parent=RiskComponentCompositeFactory(hazard_name="ME_XXX")
            ).strategy,
            RiskReducerStrategyME,
        )
        assert isinstance(
            RiskReducerFactory(
                parent=RiskComponentCompositeFactory(hazard_name="Neige")
            ).strategy,
            RiskReducerStrategySnow,
        )
        assert isinstance(
            RiskReducerFactory(
                parent=RiskComponentCompositeFactory(hazard_name="Pluies")
            ).strategy,
            RiskReducerStrategyRain,
        )
        assert isinstance(
            RiskReducerFactory(is_multizone_factory=True).strategy,
            RiskReducerStrategyMultizone,
        )
        assert isinstance(
            RiskReducerFactory(is_multizone_factory=False).strategy,
            RiskReducerStrategyMonozone,
        )

    def test_is_multizone(self):
        reducer = RiskReducerFactory(localisation=None)
        assert reducer.is_multizone is False

        reducer = RiskReducerFactory(
            localisation=RiskLocalisationFactory(is_multizone_factory=False)
        )
        assert reducer.is_multizone is False

        reducer = RiskReducerFactory(
            localisation=RiskLocalisationFactory(is_multizone_factory=True)
        )
        assert reducer.is_multizone is True

    def test_final_risk_da(self):
        for geo_idx in [1, 2, 3]:
            assert_identically_close(
                RiskReducerFactory(
                    parent=RiskComponentCompositeFactory(
                        final_risk_da_factory=xr.DataArray(
                            [1, 2, 3], coords={"id": ["geo_1", "geo_2", "geo_3"]}
                        )
                    ),
                    geo_id=f"geo_{geo_idx}",
                ).final_risk_da,
                xr.DataArray(geo_idx, coords={"id": f"geo_{geo_idx}"}),
            )

    def test_final_risk_max_level(self):
        assert RiskReducerFactory().final_risk_max_level == 0

        for geo_idx in [1, 2, 3]:
            assert (
                RiskReducerFactory(
                    parent=RiskComponentCompositeFactory(
                        final_risk_da_factory=xr.DataArray(
                            [[1], [2], [3]],
                            coords={
                                "id": ["geo_1", "geo_2", "geo_3"],
                                "valid_time": [Datetime(2023, 3, 1)],
                            },
                        ),
                        is_risks_empty_factory=False,
                    ),
                    geo_id=f"geo_{geo_idx}",
                ).final_risk_max_level
                == geo_idx
            )

    def test_comparison(self):
        assert RiskReducerFactory(final_risk_max_level_factory=0).comparison == {}

        lvls = [
            LevelCompositeFactory(
                level=2,
                events=[
                    EventCompositeFactory(
                        plain=Threshold(
                            threshold=3.1,
                            comparison_op=ComparisonOperator.SUPEGAL,
                            units="cm",
                        ),
                        mountain=Threshold(
                            threshold=2.4,
                            comparison_op=ComparisonOperator.SUP,
                            units="cm",
                        ),
                    )
                ],
            ),
            LevelCompositeFactory(
                level=3,
                events=[
                    EventCompositeFactory(
                        plain=Threshold(
                            threshold=4,
                            comparison_op=ComparisonOperator.SUPEGAL,
                            units="cm",
                        ),
                        mountain=Threshold(
                            threshold=3,
                            comparison_op=ComparisonOperator.SUP,
                            units="cm",
                        ),
                    )
                ],
            ),
        ]

        assert RiskReducerFactory(
            final_risk_max_level_factory=2,
            parent=RiskComponentCompositeFactory(levels=lvls),
        ).comparison == {
            "field_name": {
                "category": Category.BOOLEAN,
                "plain": Threshold(
                    threshold=3.1,
                    comparison_op=ComparisonOperator.SUPEGAL,
                    units="cm",
                    next_critical=4,
                ),
                "mountain": Threshold(
                    threshold=2.4,
                    comparison_op=ComparisonOperator.SUP,
                    units="cm",
                    next_critical=3,
                ),
                "aggregation": {"method": AggregationMethod.MEAN, "kwargs": {}},
            }
        }

    def test_risk_ds(self):
        # Multizone test
        ds = xr.Dataset({"a": "b"})
        reducer = RiskReducerFactory(
            is_multizone_factory=True,
            localisation=RiskLocalisationFactory(
                spatial_localisation=SpatialLocalisationFactory(
                    localised_risk_ds_factory=ds
                )
            ),
        )
        assert_identically_close(reducer.risk_ds, ds)

        # Monozone test
        ds = xr.Dataset({"A": (["id"], ["B", "C"])}, coords={"id": ["id1", "id2"]})
        reducer = RiskReducerFactory(
            is_multizone_factory=False,
            geo_id="id2",
            parent=RiskComponentCompositeFactory(risk_ds_factory=ds),
        )
        assert_identically_close(
            reducer.risk_ds, xr.Dataset({"A": (["id"], ["C"])}, coords={"id": ["id2"]})
        )

    def test_get_critical_values(self):
        assert not RiskReducerFactory(comparison_factory={}).get_critical_values()

        reducer = RiskReducerFactory(
            final_risk_max_level_factory=2,
            risk_ds_factory=xr.Dataset(
                {
                    "rep_value_plain": (
                        ["id", "valid_time", "risk_level", "evt"],
                        [[[[2.0, 3.0, np.nan, np.nan]]]],
                    ),
                    "rep_value_mountain": (
                        ["id", "valid_time", "risk_level", "evt"],
                        [[[[5.0, np.nan, 8.0, np.nan]]]],
                    ),
                    "occurrence_plain": (
                        ["id", "valid_time", "risk_level", "evt"],
                        [[[[True, True, False, False]]]],
                    ),
                    "occurrence_mountain": (
                        ["id", "valid_time", "risk_level", "evt"],
                        [[[[True, False, True, False]]]],
                    ),
                    "weatherVarName": (
                        ["risk_level", "evt"],
                        [["var1", "var2", "var3", None]],
                    ),
                },
                coords={
                    "evt": [0, 1, 2, 3],
                    "risk_level": [2],
                    "valid_time": [Datetime(2023, 3, 1)],
                    "id": ["id1"],
                },
            ),
            comparison_factory={
                "var1": {
                    "plain": Threshold(
                        threshold=3.1,
                        comparison_op=ComparisonOperator.SUPEGAL,
                        units="cm",
                        next_critical=4,
                    ),
                    "mountain": Threshold(
                        threshold=2.4,
                        comparison_op=ComparisonOperator.SUP,
                        units="cm",
                        next_critical=3,
                    ),
                },
                "var2": {
                    "plain": Threshold(
                        threshold=4,
                        comparison_op=ComparisonOperator.SUPEGAL,
                        units="cm",
                        next_critical=6,
                    )
                },
                "var3": {
                    "mountain": Threshold(
                        threshold=3,
                        comparison_op=ComparisonOperator.SUP,
                        units="cm",
                        next_critical=4,
                    )
                },
            },
        )

        assert reducer.get_critical_values() == {
            "var1": {
                "plain": {
                    "id": "id1",
                    "operator": ComparisonOperator.SUPEGAL,
                    "threshold": 3.1,
                    "units": "cm",
                    "next_critical": 4.0,
                    "value": 2.0,
                    "occurrence": True,
                },
                "mountain": {
                    "id": "id1",
                    "operator": ComparisonOperator.SUP,
                    "threshold": 2.4,
                    "units": "cm",
                    "next_critical": 3.0,
                    "value": 5.0,
                    "occurrence": True,
                },
            },
            "var2": {
                "plain": {
                    "id": "id1",
                    "operator": ComparisonOperator.SUPEGAL,
                    "threshold": 4,
                    "units": "cm",
                    "next_critical": 6.0,
                    "value": 3.0,
                    "occurrence": True,
                }
            },
            "var3": {
                "mountain": {
                    "id": "id1",
                    "operator": ComparisonOperator.SUP,
                    "threshold": 3,
                    "units": "cm",
                    "next_critical": 4.0,
                    "value": 8.0,
                    "occurrence": True,
                }
            },
        }

    def test_compute(self):
        reducer = RiskReducerFactory(
            strategy_factory=BaseCompositeFactory(compute_factory=lambda: {"a": "b"}),
            post_process_factory=lambda: None,
            parent=RiskComponentCompositeFactory(alt_area_name_factory=lambda _: "c"),
        )
        assert reducer.compute() == {"a": "b", "alt_area_name": "c"}

    def _test_compute_risk_component(
        self, evt1_name, evt2_name, evt1_unit, evt2_unit, hazard_name
    ):
        valid_time = [Datetime(2023, 3, 1, 3 * i).as_np_dt64 for i in range(4)]

        lvl1 = LevelCompositeFactory(
            level=1,
            events=[
                EventCompositeFactory(
                    field=FieldCompositeFactory(name=evt1_name),
                    plain=Threshold(
                        threshold=2.0, comparison_op=ComparisonOperator.SUP, units="mm"
                    ),
                )
            ],
        )
        lvl2 = LevelCompositeFactory(
            level=2,
            events=[
                # only plain event
                EventCompositeFactory(field=FieldCompositeFactory(name=evt1_name)),
                # plain and mountain event
                EventCompositeFactory(
                    field=FieldCompositeFactory(name=evt2_name),
                    plain=Threshold(
                        threshold=20, comparison_op=ComparisonOperator.SUP, units="mm"
                    ),
                    mountain=Threshold(
                        threshold=30,
                        comparison_op=ComparisonOperator.SUPEGAL,
                        units="mm",
                    ),
                ),
            ],
        )

        return RiskComponentCompositeFactory(
            hazard_name=hazard_name,
            risk_ds_factory=xr.Dataset(
                {
                    "occurrence": (
                        ["id", "risk_level", "valid_time"],
                        [[[True, True, False, False]] * 2],
                    ),
                    "occurrence_event": (
                        ["risk_level", "evt"],
                        [[True, True], [True, True]],
                    ),
                    "occurrence_plain": (
                        ["risk_level", "evt"],
                        [[True, True], [True, True]],
                    ),
                    "occurrence_mountain": (
                        ["risk_level", "evt"],
                        [[True, True], [True, True]],
                    ),
                    "threshold_plain": (["risk_level", "evt"], [[5, 10], [15, 20]]),
                    "threshold_mountain": (["risk_level", "evt"], [[15, 20], [25, 30]]),
                    "weatherVarName": (
                        ["risk_level", "evt"],
                        [[evt1_name, np.nan], [evt1_name, evt2_name]],
                    ),
                    "min_plain": (
                        ["id", "risk_level", "evt", "valid_time"],
                        [
                            [
                                [[10.0, 20.0, 30.0, 40.0], 4 * [np.nan]],
                                [[1.0, 2.0, 3.0, 4.0], [50.0, 60.0, 70.0, 80.0]],
                            ]
                        ],
                    ),
                    "max_plain": (
                        ["id", "risk_level", "evt", "valid_time"],
                        [
                            [
                                [[12.0, 22.0, 32.0, 42.0], 4 * [np.nan]],
                                [[1.2, 2.2, 3.2, 4.2], [52.0, 62.0, 72.0, 82.0]],
                            ]
                        ],
                    ),
                    "rep_value_plain": (
                        ["id", "risk_level", "evt", "valid_time"],
                        [
                            [
                                [[11.0, 21.0, 31.0, 41.0], 4 * [np.nan]],
                                [[1.1, 2.1, 3.1, 4.1], [51.0, 61.0, 71.0, 81.0]],
                            ]
                        ],
                    ),
                    "min_mountain": (
                        ["id", "risk_level", "evt", "valid_time"],
                        [
                            [
                                2 * [4 * [np.nan]],
                                [4 * [np.nan], [53.0, 63.0, 73.0, 83.0]],
                            ]
                        ],
                    ),
                    "max_mountain": (
                        ["id", "risk_level", "evt", "valid_time"],
                        [
                            [
                                2 * [4 * [np.nan]],
                                [4 * [np.nan], [55.0, 65.0, 75.0, 85.0]],
                            ]
                        ],
                    ),
                    "rep_value_mountain": (
                        ["id", "risk_level", "evt", "valid_time"],
                        [
                            [
                                2 * [4 * [np.nan]],
                                [4 * [np.nan], [54.0, 64.0, 74.0, 84.0]],
                            ]
                        ],
                    ),
                },
                coords={
                    "id": ["geo_id"],
                    "evt": [0, 1],
                    "risk_level": [1, 2],
                    "valid_time": valid_time,
                    "units": (
                        ["risk_level", "evt"],
                        [[evt1_unit, np.nan], [evt1_unit, evt2_unit]],
                    ),
                    "altAreaName": (["id"], ["domain"]),
                },
            ),
            final_risk_da_factory=xr.DataArray(
                [[2, 1, 1, 2]], coords={"id": ["geo_id"], "valid_time": valid_time}
            ),
            levels=[lvl1, lvl2],
            alt_area_name_factory=lambda _: "domain",
        )

    @pytest.mark.parametrize(
        "hazard_name,evt1_name,evt2_name,evt1_unit,evt2_unit",
        [
            # Normal hazard_name
            ("XXX", "NEIPOT1__SOL", "NEIPOT24__SOL", "mm", "mm"),  # type SNOW
            ("XXX", "NEIPOT1__SOL", "EAU12__SOL", "mm", "mm"),  # Type PRECIP_SNOW
            ("XXX", "EAU24__SOL", "EAU12__SOL", "mm", "mm"),  # Type PRECIP
            ("XXX", "NEIPOT1__SOL", "FF__HAUTEUR", "mm", "km/h"),  # Type general
            ("XXX", "NEIPOT1__SOL", "RAF__HAUTEUR", "mm", "km/h"),  # Type general
            # ME hazard_name
            ("ME_XXX", "NEIPOT1__SOL", "NEIPOT24__SOL", "mm", "mm"),
            ("ME_XXX", "FF__RAF", "FF__RAF", "km/h", "km/h"),
        ],
    )
    def test_compute_multizone(
        self,
        hazard_name,
        evt1_name,
        evt2_name,
        evt1_unit,
        evt2_unit,
        assert_equals_result,
    ):
        np.random.seed(1)
        result = {}
        risk_component = self._test_compute_risk_component(
            evt1_name, evt2_name, evt1_unit, evt2_unit, hazard_name
        )
        for language in risk_component.iter_languages():
            result[language] = RiskReducerFactory(
                parent=risk_component,
                is_multizone_factory=True,
                risk_ds_factory=risk_component.risk_ds,
                localisation=RiskLocalisationFactory(
                    all_name_factory="XXX",
                    table_localisation=TableLocalisationFactory(
                        table={"zone1": "Zone 1", "zone2": "Zone 2"}
                    ),
                    periods_name_factory=[
                        "20230301060000_to_20230301080000",
                        "20230301120000_to_20230301160000",
                        "20230302180000_to_20230302230000",
                    ],
                ),
                final_risk_max_level_factory=2,
            ).compute()
        assert_equals_result(result)

    @pytest.mark.parametrize(
        "hazard_name,evt1_name,evt2_name,evt1_unit,evt2_unit",
        [
            # Normal hazard_name
            ("XXX", "NEIPOT1__SOL", "NEIPOT24__SOL", "mm", "mm"),
            ("XXX", "NEIPOT1__SOL", "EAU12__SOL", "mm", "mm"),
            ("XXX", "EAU24__SOL", "EAU12__SOL", "mm", "mm"),
            ("XXX", "NEIPOT1__SOL", "FF__HAUTEUR", "mm", "km/h"),
            ("XXX", "NEIPOT1__SOL", "RAF__HAUTEUR", "mm", "km/h"),
            # ME hazard_name
            ("ME_XXX", "NEIPOT1__SOL", "NEIPOT24__SOL", "mm", "mm"),
            ("ME_XXX", "FF__RAF", "FF__RAF", "km/h", "km/h"),
        ],
    )
    def test_compute_monozone(
        self,
        hazard_name,
        evt1_name,
        evt2_name,
        evt1_unit,
        evt2_unit,
        assert_equals_result,
    ):
        np.random.seed(1)

        result = {}
        risk_component = self._test_compute_risk_component(
            evt1_name, evt2_name, evt1_unit, evt2_unit, hazard_name
        )
        for language in risk_component.iter_languages():
            result[language] = RiskReducerFactory(
                parent=risk_component,
                is_multizone_factory=False,
                risk_ds_factory=risk_component.risk_ds,
            ).compute()
        assert_equals_result(result)


class TestRiskReducerStrategy:

    def test_period_describer(self):
        assert (
            RiskReducerStrategyFactory(
                parent=RiskReducerFactory(
                    parent=RiskComponentCompositeFactory(
                        period_describer_factory="test"
                    )
                )
            ).period_describer
            == "test"
        )

    def test_geo_id(self):
        assert (
            RiskReducerStrategyFactory(parent=RiskReducerFactory(geo_id="XXX")).geo_id
            == "XXX"
        )

    def test_risk_component(self):
        assert (
            RiskReducerStrategyFactory(
                parent=RiskReducerFactory(
                    parent=RiskComponentCompositeFactory(hazard_name="XXX")
                )
            ).risk_component.hazard_name
            == "XXX"
        )

    def test_is_multizone(self):
        assert (
            RiskReducerStrategyFactory(
                parent=RiskReducerFactory(is_multizone_factory=True)
            ).is_multizone
            is True
        )
        assert (
            RiskReducerStrategyFactory(
                parent=RiskReducerFactory(is_multizone_factory=False)
            ).is_multizone
            is False
        )

    def test_reduction(self):
        reducer = RiskReducerFactory(reduction={"a": "b"})
        assert RiskReducerStrategyFactory(parent=reducer).reduction == {"a": "b"}

    def test_localisation(self):
        # Multizone case
        reducer = RiskReducerFactory(
            is_multizone_factory=True,
            localisation=RiskLocalisationFactory(all_name_factory="XXX"),
        )
        assert RiskReducerStrategyFactory(parent=reducer).localisation == "XXX"

        # Monozone case
        reducer = RiskReducerFactory(
            geo_id="XXX",
            is_multizone_factory=False,
            parent=RiskComponentCompositeFactory(alt_area_name_factory=lambda x: x),
        )
        assert RiskReducerStrategyFactory(parent=reducer).localisation == "XXX"


class TestRiskReducerStrategySnow:
    @pytest.mark.parametrize(
        "intensity,expected",
        [(1, "low"), (2, "low"), (3, "moderate"), (4, "moderate"), (5, "high")],
    )
    def test_intensity_key(self, intensity, expected):
        assert (
            RiskReducerStrategySnowFactory(intensity_factory=intensity).intensity_key
            == expected
        )

    def test_compute(self):
        # Test with final risk max level = 0
        strategy = RiskReducerStrategySnow(
            parent=RiskReducerFactory(final_risk_max_level_factory=0)
        )
        assert strategy.compute() == {"key": "RAS"}

        # Test with low intensity and monozone
        strategy = RiskReducerStrategySnow(
            parent=RiskReducerFactory(
                is_multizone_factory=False,
                final_risk_max_level_factory=1,
                parent=RiskComponentCompositeFactory(
                    levels=[
                        LevelCompositeFactory(
                            level=1,
                            spatial_risk_da_factory=xr.DataArray(
                                [[[[True, True, True, True]]]],
                                coords={
                                    "id": ["geo_id"],
                                    "longitude": [30],
                                    "latitude": [40],
                                    "valid_time": [
                                        Datetime(2023, 3, 1, i) for i in range(4)
                                    ],
                                },
                            ),
                        )
                    ],
                    params={
                        "NEIPOT3__SOL": FieldCompositeFactory(
                            compute_factory=lambda: xr.DataArray(
                                [[[0, 10, 0, 0]]],
                                coords={
                                    "longitude": [30],
                                    "latitude": [40],
                                    "valid_time": [
                                        Datetime(2023, 3, 1, i) for i in range(4)
                                    ],
                                },
                                dims=["longitude", "latitude", "valid_time"],
                                attrs={"units": "mm"},
                            )
                        )
                    },
                ),
            )
        )
        assert strategy.compute() == {"key": "low", "localisation": "N.A"}

        # Test with high intensity and multizone
        strategy = RiskReducerStrategySnow(
            parent=RiskReducerFactory(
                is_multizone_factory=True,
                final_risk_max_level_factory=1,
                parent=RiskComponentCompositeFactory(
                    levels=[
                        LevelCompositeFactory(
                            level=1,
                            spatial_risk_da_factory=xr.DataArray(
                                [[[[True, True, True, True]]]],
                                coords={
                                    "id": ["geo_id"],
                                    "longitude": [30],
                                    "latitude": [40],
                                    "valid_time": [
                                        Datetime(2023, 3, 1, i) for i in range(4)
                                    ],
                                },
                            ),
                        )
                    ],
                    params={
                        "NEIPOT3__SOL": FieldCompositeFactory(
                            compute_factory=lambda: xr.DataArray(
                                [[[0, 10, 0, 0]]],
                                coords={
                                    "longitude": [30],
                                    "latitude": [40],
                                    "valid_time": [
                                        Datetime(2023, 3, 1, i) for i in range(4)
                                    ],
                                },
                                dims=["longitude", "latitude", "valid_time"],
                                attrs={"units": "cm"},
                            )
                        )
                    },
                ),
                localisation=RiskLocalisationFactory(all_name_factory="Lieu Multizone"),
            )
        )
        assert strategy.compute() == {"key": "high", "localisation": "Lieu Multizone"}

    @pytest.mark.parametrize(
        "valid_time_len,wwmf,expected",
        [
            (2, 0, {"periods": "par moments"}),
            (2, 60, {"periods": "de la nuit de lundi à mardi jusqu'à cette nuit"}),
            # Test with only one valid_time
            (1, 0, {"periods": "par moments"}),
            (1, 60, {"periods": "par moments"}),
        ],
    )
    def test_process_period(self, valid_time_len, wwmf, expected):
        strategy = RiskReducerStrategySnow(
            parent=RiskReducerFactory(
                reduction={},
                final_risk_max_level_factory=1,
                parent=RiskComponentCompositeFactory(
                    params={
                        "WWMF__SOL": FieldCompositeFactory(
                            compute_factory=lambda: xr.DataArray(
                                [[[wwmf] * valid_time_len]],
                                coords={
                                    "longitude": [30],
                                    "latitude": [40],
                                    "valid_time": [
                                        Datetime(2023, 3, i + 1)
                                        for i in range(valid_time_len)
                                    ],
                                },
                                dims=["longitude", "latitude", "valid_time"],
                            )
                        )
                    }
                ),
            )
        )
        strategy.process_period()
        assert strategy.reduction == expected


class TestRiskReducerStrategyRain:
    @pytest.mark.parametrize(
        "intensity,wwmf,expected",
        [
            (0.1, 0, "low"),
            (0.2, 0, "low"),
            (0.1, 98, "low_thunder"),
            (0.2, 99, "low_thunder"),
            (0.55, 0, "moderate"),
            (0.75, 0, "moderate"),
            (0.75, 98, "moderate_thunder"),
            (0.55, 99, "moderate_thunder"),
            (0.76, 0, "high"),
            (2.0, 98, "high"),
            (0.76, 99, "high"),
        ],
    )
    def test_intensity_key(self, intensity, wwmf, expected):
        assert (
            RiskReducerStrategyRainFactory(
                intensity_factory=intensity,
                parent=RiskReducerFactory(
                    final_risk_max_level_factory=1,
                    geo_id="geo_id_test",
                    parent=RiskComponentCompositeFactory(
                        params={
                            "WWMF__SOL": FieldCompositeFactory(
                                compute_factory=lambda: xr.DataArray(
                                    [[wwmf]],
                                    coords={"longitude": [30], "latitude": [40]},
                                )
                            )
                        },
                        levels=[
                            LevelCompositeFactory(
                                level=1,
                                spatial_risk_da_factory=xr.DataArray(
                                    [[[True]]],
                                    coords={
                                        "id": ["geo_id_test"],
                                        "longitude": [30],
                                        "latitude": [40],
                                    },
                                ),
                            )
                        ],
                    ),
                ),
            ).intensity_key
            == expected
        )

    def test_compute(self):
        # Test with final risk max level = 0
        strategy = RiskReducerStrategyRain(
            parent=RiskReducerFactory(final_risk_max_level_factory=0)
        )
        assert strategy.compute() == {"key": "RAS"}

        # Test with low intensity and monozone
        strategy = RiskReducerStrategyRain(
            parent=RiskReducerFactory(
                is_multizone_factory=False,
                final_risk_max_level_factory=1,
                parent=RiskComponentCompositeFactory(
                    levels=[
                        LevelCompositeFactory(
                            level=1,
                            spatial_risk_da_factory=xr.DataArray(
                                [[[[True, True, True, True]]]],
                                coords={
                                    "id": ["geo_id"],
                                    "longitude": [30],
                                    "latitude": [40],
                                    "valid_time": [
                                        Datetime(2023, 3, 1, i) for i in range(4)
                                    ],
                                },
                            ),
                        )
                    ],
                    params={
                        "EAU1__SOL": FieldCompositeFactory(
                            compute_factory=lambda: xr.DataArray(
                                [[[0, 1.0, 0, 0]]],
                                coords={
                                    "longitude": [30],
                                    "latitude": [40],
                                    "valid_time": [
                                        Datetime(2023, 3, 1, i) for i in range(4)
                                    ],
                                },
                                dims=["longitude", "latitude", "valid_time"],
                                attrs={"units": "mm"},
                            )
                        ),
                        "WWMF__SOL": FieldCompositeFactory(
                            compute_factory=lambda: xr.DataArray(
                                [[[0, 0, 0, 0]]],
                                coords={
                                    "longitude": [30],
                                    "latitude": [40],
                                    "valid_time": [
                                        Datetime(2023, 3, 1, i) for i in range(4)
                                    ],
                                },
                                dims=["longitude", "latitude", "valid_time"],
                                attrs={"units": "cm"},
                            )
                        ),
                    },
                ),
            )
        )
        assert strategy.compute() == {"key": "low", "localisation": "N.A"}

        # Test with moderate intensity and multizone
        strategy = RiskReducerStrategyRain(
            parent=RiskReducerFactory(
                is_multizone_factory=True,
                final_risk_max_level_factory=1,
                parent=RiskComponentCompositeFactory(
                    levels=[
                        LevelCompositeFactory(
                            level=1,
                            spatial_risk_da_factory=xr.DataArray(
                                [[[[True, True, True, True]]]],
                                coords={
                                    "id": ["geo_id"],
                                    "longitude": [30],
                                    "latitude": [40],
                                    "valid_time": [
                                        Datetime(2023, 3, 1, i) for i in range(4)
                                    ],
                                },
                            ),
                        )
                    ],
                    params={
                        "EAU1__SOL": FieldCompositeFactory(
                            compute_factory=lambda: xr.DataArray(
                                [[[0, 1.0, 0, 0]]],
                                coords={
                                    "longitude": [30],
                                    "latitude": [40],
                                    "valid_time": [
                                        Datetime(2023, 3, 1, i) for i in range(4)
                                    ],
                                },
                                dims=["longitude", "latitude", "valid_time"],
                                attrs={"units": "cm"},
                            )
                        ),
                        "WWMF__SOL": FieldCompositeFactory(
                            compute_factory=lambda: xr.DataArray(
                                [[[0, 0, 0, 0]]],
                                coords={
                                    "longitude": [30],
                                    "latitude": [40],
                                    "valid_time": [
                                        Datetime(2023, 3, 1, i) for i in range(4)
                                    ],
                                },
                                dims=["longitude", "latitude", "valid_time"],
                                attrs={"units": "cm"},
                            )
                        ),
                    },
                ),
                localisation=RiskLocalisationFactory(all_name_factory="Lieu Multizone"),
            )
        )
        assert strategy.compute() == {"key": "high", "localisation": "Lieu Multizone"}

    @pytest.mark.parametrize(
        "final_risk_da,expected",
        [
            ([0, 0, 0], {}),
            ([2], {"periods": "en début de période"}),
            (
                [2, 2, 0, 0, 0],
                {"periods": "de la nuit de lundi à mardi jusqu'à cette nuit"},
            ),
            (
                [0, 0, 0, 0, 3, 3, 3],
                {
                    "periods": "de la nuit de vendredi à samedi jusqu'à la nuit de "
                    "lundi à mardi"
                },
            ),
        ],
    )
    def test_process_period(self, final_risk_da, expected):
        strategy = RiskReducerStrategyRain(
            parent=RiskReducerFactory(
                reduction={},
                final_risk_da_factory=xr.DataArray(
                    final_risk_da,
                    coords={
                        "valid_time": [
                            Datetime(2023, 3, i + 1) for i in range(len(final_risk_da))
                        ]
                    },
                ),
                final_risk_max_level_factory=max(final_risk_da),
            )
        )
        strategy.process_period()
        assert strategy.reduction == expected


class TestRiskReducerStrategyMonozone:
    @pytest.mark.parametrize(
        "risks,expected",
        [
            ([1, 1, 0, 0], [1, 1, 0, 0]),
            ([0, 0, 1, 1], [0, 0, 1, 1]),
            ([0, 0, 1, 1, 0, 0], [0, 0, 1, 1, 0, 0]),
            ([0, 0, 1, 0, 1, 0, 0], [0, 0, 1, 1, 1, 0, 0]),
            ([0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0], [0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0]),
            ([0, 0, 1, 0, 0, 0, 1, 0, 0], [0, 0, 1, 1, 1, 1, 1, 0, 0]),
        ],
    )
    def test_mask_start_end(self, risks, expected) -> xr.DataArray:
        valid_time = [Datetime(2023, 3, 1, i).as_np_dt64 for i in range(len(risks))]
        risk = xr.DataArray(
            risks,
            coords={"id": "geo_id", "valid_time": valid_time},
            dims=["valid_time"],
        )
        output = RiskReducerStrategyMonozone.mask_start_end(risk)
        expect = xr.DataArray(
            expected,
            coords={"id": "geo_id", "valid_time": valid_time},
            dims=["valid_time"],
        )
        assert_identically_close(output, expect)

    @pytest.mark.parametrize(
        "time_zone,offset,expected",
        [
            # Test with correction for bloc of 3h with offset
            ("UTC", 0, [3, 3, 3, 2, 2, 2, 1, 1, 1]),
            ("UTC", 1, [3, 3, 3, 2, 2, 1, 1, 1, 1]),
            ("UTC", 2, [3, 3, 3, 2, 2, 2, 2, 2, 2]),
            # Test with different UTC
            ("Etc/GMT-1", 1, [3, 3, 3, 2, 2, 2, 2, 2, 2]),
            ("Etc/GMT-2", 2, [3, 3, 3, 2, 2, 1, 1, 1, 1]),
        ],
    )
    def test_final_risk_da(self, time_zone, offset, expected):
        valid_time = [Datetime(2023, 3, 1, i + offset).as_np_dt64 for i in range(9)]

        composite = RiskComponentCompositeFactory(
            data=xr.Dataset({"risk_level": range(4)}, coords={"id": ["geo_id"]}),
            final_risk_da_factory=xr.DataArray(
                [[3, 2, 1, 1, 2, 1, 1, 1, 0]],
                coords={"id": ["geo_id"], "valid_time": valid_time},
            ),
        )
        strategy = RiskReducerStrategyMonozone(
            parent=RiskReducerFactory(parent=composite)
        )
        composite.shared_config["time_zone"] = time_zone
        assert_identically_close(
            strategy.final_risk_da,
            xr.DataArray(
                expected,
                coords={"id": "geo_id", "valid_time": valid_time},
                dims=["valid_time"],
            ),
        )

    @pytest.mark.parametrize(
        "time_zone,inputs,expected",
        [
            ("UTC", [3, 1, 2, 3, 2, 1, 3], [3, 3, 3, 3, 3, 3, 3]),
            ("UTC", [0, 1, 2, 3, 2, 1, 1], [2, 2, 2, 3, 3, 3, 3]),
            ("UTC", [0, 0, 2, 3, 0, 2, 1], [2, 2, 2, 3, 3, 3, 3]),
            ("UTC", [0, 0, 0, 1, 2, 3, 3], [0, 0, 0, 3, 3, 3, 3]),
            ("UTC", [0, 0, 0, 0, 2, 3, 3], [0, 0, 0, 0, 3, 3, 3]),
            # Test with different UTC start
            ("Etc/GMT+1", [3, 1, 2, 3, 2, 1, 3], [3, 3, 3, 3, 3, 3, 3]),
            ("Etc/GMT+1", [0, 1, 2, 3, 2, 1, 1], [3, 3, 3, 3, 2, 2, 2]),
            ("Etc/GMT+1", [0, 0, 2, 3, 0, 2, 1], [3, 3, 3, 3, 2, 2, 2]),
            ("Etc/GMT+1", [0, 0, 2, 2, 3, 2, 1], [2, 2, 2, 2, 3, 3, 3]),
            ("Etc/GMT+1", [0, 0, 0, 1, 2, 3, 3], [0, 0, 0, 1, 3, 3, 3]),
            ("Etc/GMT+1", [0, 0, 0, 0, 2, 3, 3], [0, 0, 0, 0, 3, 3, 3]),
            # Test with different end
            ("Etc/GMT+1", [3, 1, 2, 3, 2, 1, 3], [3, 3, 3, 3, 3, 3, 3]),
            ("Etc/GMT+1", [0, 1, 2, 3, 2, 1, 0], [3, 3, 3, 3, 2, 2, 2]),
            ("Etc/GMT+1", [3, 3, 2, 3, 0, 0, 0], [3, 3, 3, 3, 0, 0, 0]),
            ("Etc/GMT+1", [3, 3, 2, 0, 0, 0, 0], [3, 3, 3, 0, 0, 0, 0]),
        ],
    )
    def test_final_risk_da_start_end(self, time_zone, inputs, expected):
        valid_time = [Datetime(2023, 3, 1, i).as_np_dt64 for i in range(len(inputs))]

        composite = RiskComponentCompositeFactory(
            data=xr.Dataset({"risk_level": range(4)}, coords={"id": ["geo_id"]}),
            final_risk_da_factory=xr.DataArray(
                [inputs], coords={"id": ["geo_id"], "valid_time": valid_time}
            ),
        )
        strategy = RiskReducerStrategyMonozone(
            parent=RiskReducerFactory(parent=composite)
        )
        composite.shared_config["time_zone"] = time_zone
        assert_identically_close(
            strategy.final_risk_da,
            xr.DataArray(
                expected,
                coords={"id": "geo_id", "valid_time": valid_time},
                dims=["valid_time"],
            ),
        )

    @pytest.mark.parametrize(
        "final_risk,offset,expected",
        [
            # Test with max_level=2
            (
                [2, 2, 2, 1, 1, 1, 2, 2, 2],
                0,
                [1.0, 1.0, 1.0, 0.5, 0.5, 0.5, 1.0, 1.0, 1.0],
            ),
            # Test with max_level=1
            ([1] * 9, 0, [1] * 9),
            # Test with max_level=0
            ([0] * 9, 0, [0] * 9),
            # Test with correction for bloc of 3h and offset
            (
                [3, 2, 1, 1, 2, 1, 1, 1, 0],
                0,
                [1.0, 1.0, 1.0, 0.75, 0.75, 0.75, 0.5, 0.5, 0.5],
            ),
            (
                [3, 2, 1, 1, 2, 1, 1, 1, 0],
                1,
                [1.0, 1.0, 1.0, 0.75, 0.75, 0.5, 0.5, 0.5, 0.5],
            ),
            (
                [3, 2, 1, 1, 2, 1, 1, 1, 0],
                2,
                [1.0, 1.0, 1.0, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75],
            ),
        ],
    )
    def test_norm_risk(self, final_risk, offset, expected):
        valid_time = [
            Datetime(2023, 3, 1, i + offset).as_np_dt64 for i in range(len(final_risk))
        ]

        composite = RiskComponentCompositeFactory(
            data=xr.Dataset(
                {"risk_level": range(max(final_risk) + 1)}, coords={"id": ["geo_id"]}
            ),
            final_risk_da_factory=xr.DataArray(
                [final_risk], coords={"id": ["geo_id"], "valid_time": valid_time}
            ),
        )
        strategy = RiskReducerStrategyMonozone(
            parent=RiskReducerFactory(parent=composite)
        )
        assert_identically_close(strategy.norm_risk, np.array(expected))

    def test_operator_dict(self):
        lvl1 = LevelCompositeFactory(
            events=[
                EventCompositeFactory(
                    field=FieldCompositeFactory(name="evt1"),
                    plain=Threshold(threshold=15, comparison_op=ComparisonOperator.SUP),
                ),
                EventCompositeFactory(
                    field=FieldCompositeFactory(name="evt2"),
                    plain=Threshold(threshold=15, comparison_op=ComparisonOperator.SUP),
                    mountain=Threshold(
                        threshold=15, comparison_op=ComparisonOperator.INF
                    ),
                ),
            ]
        )
        lvl2 = LevelCompositeFactory(
            events=[
                EventCompositeFactory(
                    field=FieldCompositeFactory(name="evt3"),
                    plain=Threshold(
                        threshold=15, comparison_op=ComparisonOperator.EGAL
                    ),
                )
            ]
        )
        composite = RiskComponentCompositeFactory(levels=[lvl1, lvl2])
        strategy = RiskReducerStrategyMonozone(
            parent=RiskReducerFactory(parent=composite)
        )
        assert strategy.operator_dict == {
            "evt1": {"plain": ComparisonOperator.SUP},
            "evt2": {
                "plain": ComparisonOperator.SUP,
                "mountain": ComparisonOperator.INF,
            },
            "evt3": {"plain": ComparisonOperator.EGAL},
        }

    def test_process_value(self):
        lvl = LevelCompositeFactory(
            level=1,
            events=[
                EventCompositeFactory(
                    field=FieldCompositeFactory(name="evt"),
                    plain=Threshold(threshold=15, comparison_op=ComparisonOperator.SUP),
                    mountain=Threshold(
                        threshold=15, comparison_op=ComparisonOperator.INF
                    ),
                )
            ],
        )
        strategy = RiskReducerStrategyMonozone(
            parent=RiskReducerFactory(
                parent=RiskComponentCompositeFactory(levels=[lvl])
            )
        )

        # Test without data
        evts_ds = [
            xr.Dataset(
                {
                    "risk_level": 1,
                    "units": ...,
                    "threshold_plain": ...,
                    "threshold_mountain": ...,
                }
            )
        ]
        assert strategy.process_value("evt", evts_ds=evts_ds, kind="plain") is None
        assert strategy.process_value("evt", evts_ds=evts_ds, kind="mountain") is None

        evts_ds = [
            xr.Dataset(
                {
                    "risk_level": 1,
                    "threshold_plain": 10.0,
                    "min_plain": 10.0,
                    "max_plain": 20.0,
                    "rep_value_plain": 15.0,
                    "threshold_mountain": 30.0,
                    "min_mountain": 30.0,
                    "max_mountain": 40.0,
                    "rep_value_mountain": 35.0,
                    "occurrence_event": True,
                    "occurrence_plain": True,
                    "occurrence_mountain": False,
                },
                coords={"units": "cm"},
            ),
            xr.Dataset(
                {
                    "risk_level": 1,
                    "threshold_plain": 10.0,
                    "min_plain": 15.0,
                    "max_plain": 17.0,
                    "rep_value_plain": 16.0,
                    "threshold_mountain": 30.0,
                    "min_mountain": 35.0,
                    "max_mountain": 53.0,
                    "rep_value_mountain": 41.0,
                    "occurrence_event": False,
                    "occurrence_plain": False,
                    "occurrence_mountain": True,
                },
                coords={"units": "cm"},
            ),
        ]
        assert strategy.process_value("evt", evts_ds=evts_ds, kind="plain") == {
            "threshold": 10.0,
            "min": 10.0,
            "max": 20.0,
            "value": 16.0,
            "units": "cm",
            "operator": ComparisonOperator.SUP,
            "occurrence": True,
        }
        assert strategy.process_value("evt", evts_ds=evts_ds, kind="mountain") == {
            "threshold": 30.0,
            "min": 30.0,
            "max": 53.0,
            "value": 35.0,
            "units": "cm",
            "operator": ComparisonOperator.INF,
            "occurrence": True,
        }

        # Test with only plain event
        lvl = LevelCompositeFactory(
            level=1,
            events=[
                EventCompositeFactory(
                    field=FieldCompositeFactory(name="evt"),
                    plain=Threshold(threshold=15, comparison_op=ComparisonOperator.SUP),
                )
            ],
        )
        strategy = RiskReducerStrategyMonozone(
            parent=RiskReducerFactory(
                parent=RiskComponentCompositeFactory(levels=[lvl])
            )
        )
        assert strategy.process_value("evt", evts_ds=evts_ds, kind="plain") == {
            "threshold": 10.0,
            "min": 10.0,
            "max": 20.0,
            "value": 16.0,
            "units": "cm",
            "operator": ComparisonOperator.SUP,
            "occurrence": True,
        }
        assert strategy.process_value("evt", evts_ds=evts_ds, kind="mountain") is None

        # Test with only mountain event
        lvl = LevelCompositeFactory(
            level=1,
            events=[
                EventCompositeFactory(
                    field=FieldCompositeFactory(name="evt"),
                    plain=None,
                    mountain=Threshold(
                        threshold=15, comparison_op=ComparisonOperator.SUP
                    ),
                )
            ],
        )
        strategy = RiskReducerStrategyMonozone(
            parent=RiskReducerFactory(
                parent=RiskComponentCompositeFactory(levels=[lvl])
            )
        )

        assert strategy.process_value("evt", evts_ds=evts_ds, kind="plain") is None
        assert strategy.process_value("evt", evts_ds=evts_ds, kind="mountain") == {
            "threshold": 30.0,
            "min": 30.0,
            "max": 53.0,
            "value": 41.0,
            "units": "cm",
            "operator": ComparisonOperator.SUP,
            "occurrence": True,
        }

    def test_compute_infos(self, assert_equals_result):
        # Test with DataArray
        da1 = xr.DataArray(Datetime(2023, 3, 1, 6).as_np_dt64, coords={"centroid": 0.2})
        da2 = xr.DataArray(Datetime(2023, 3, 1, 7).as_np_dt64)
        da3 = xr.DataArray(Datetime(2023, 3, 1, 8).as_np_dt64)
        strategy = RiskReducerStrategyMonozone(parent=RiskReducerFactory())
        assert strategy.compute_infos([da1, da2, da3]) == {
            "level": 0,
            "start": Datetime(2023, 3, 1, 6),
            "stop": Datetime(2023, 3, 1, 8),
            "centroid": 0.2,
        }

        # Test with Dataset
        ds1 = xr.Dataset(
            {
                "centroid": 0.2,
                "threshold_plain": (["evt"], [5.0, 50.0]),
                "min_plain": (["evt"], [1.0, 20.0]),
                "max_plain": (["evt"], [11.0, 120.0]),
                "rep_value_plain": (["evt"], [6.0, 70.0]),
                "threshold_mountain": (["evt"], [np.nan, 100.0]),
                "min_mountain": (["evt"], [np.nan, 40.0]),
                "max_mountain": (["evt"], [np.nan, 240.0]),
                "rep_value_mountain": (["evt"], [np.nan, 140.0]),
                "occurrence_event": (["evt"], [True, True]),
                "occurrence_plain": (["evt"], [True, True]),
                "occurrence_mountain": (["evt"], [True, True]),
            },
            coords={
                "evt": [0, 1],
                "units": (["evt"], ["cm", "mm"]),
                "risk_level": 1,
                "valid_time": Datetime(2023, 3, 1, 6).as_np_dt64,
                "weatherVarName": (["evt"], ["NEIPOT1__SOL", "NEIPOT24__SOL"]),
            },
        )
        ds2 = xr.Dataset(
            {
                "threshold_plain": (["evt"], [10.0, 100.0]),
                "min_plain": (["evt"], [3.0, 40.0]),
                "max_plain": (["evt"], [13.0, 140.0]),
                "rep_value_plain": (["evt"], [8.0, 90.0]),
                "threshold_mountain": (["evt"], [np.nan, 600.0]),
                "min_mountain": (["evt"], [np.nan, 80.0]),
                "max_mountain": (["evt"], [np.nan, 280.0]),
                "rep_value_mountain": (["evt"], [np.nan, 180.0]),
                "occurrence_event": (["evt"], [True, True]),
                "occurrence_plain": (["evt"], [True, True]),
                "occurrence_mountain": (["evt"], [True, True]),
            },
            coords={
                "evt": [0, 1],
                "units": (["evt"], ["cm", "mm"]),
                "valid_time": Datetime(2023, 3, 1, 7).as_np_dt64,
                "weatherVarName": (["evt"], ["NEIPOT1__SOL", "NEIPOT24__SOL"]),
            },
        )
        ds3 = xr.Dataset(
            {
                "threshold_plain": (["evt"], [20.0, 200.0]),
                "min_plain": (["evt"], [5.0, 60.0]),
                "max_plain": (["evt"], [15.0, 160.0]),
                "rep_value_plain": (["evt"], [10.0, 110.0]),
                "threshold_mountain": (["evt"], [np.nan, 600.0]),
                "min_mountain": (["evt"], [np.nan, 120.0]),
                "max_mountain": (["evt"], [np.nan, 360.0]),
                "rep_value_mountain": (["evt"], [np.nan, 220.0]),
                "occurrence_event": (["evt"], [False, False]),
                "occurrence_plain": (["evt"], [False, False]),
                "occurrence_mountain": (["evt"], [False, False]),
            },
            coords={
                "evt": [0, 1],
                "units": (["evt"], ["cm", "mm"]),
                "valid_time": Datetime(2023, 3, 1, 8).as_np_dt64,
                "weatherVarName": (["evt"], ["NEIPOT1__SOL", "NEIPOT24__SOL"]),
            },
        )

        lvl = LevelCompositeFactory(
            level=1,
            events=[
                # only plain event
                EventCompositeFactory(
                    field=FieldCompositeFactory(name="NEIPOT1__SOL"),
                    mountain_altitude=600,
                ),
                # plain and mountain event
                EventCompositeFactory(
                    field=FieldCompositeFactory(name="NEIPOT24__SOL"),
                    mountain=Threshold(
                        threshold=30, comparison_op=ComparisonOperator.SUPEGAL
                    ),
                    mountain_altitude=600,
                ),
            ],
        )
        strategy = RiskReducerStrategyMonozone(
            parent=RiskReducerFactory(
                parent=RiskComponentCompositeFactory(levels=[lvl])
            )
        )
        assert_equals_result(strategy.compute_infos([ds1, ds2, ds3]))

    def test_find_levels(self):
        reduction = {
            "C": ...,
            "B1": {
                "level": ...,
                "start": ...,
                "stop": ...,
                "centroid": 1,  # => level_max
                "EAU24__SOL": {
                    "plain": {"operator": ComparisonOperator.SUP, "value": 10}
                },  # won't be kept
                "PRECIP1__SOL": {
                    "plain": {"operator": ComparisonOperator.INF, "value": 10}
                },  # will be kept
            },
            "B2": {
                "level": ...,
                "start": ...,
                "stop": ...,
                "centroid": 1,  # => level_max
                "EAU24__SOL": {
                    "plain": {"operator": ComparisonOperator.SUP, "value": 20}
                },  # will be kept
                "PRECIP1__SOL": {
                    "plain": {"operator": ComparisonOperator.INF, "value": 20}
                },  # won't be kept
            },
            "B3": {
                "level": 3,  # => level_int
                "start": ...,
                "stop": ...,
                "centroid": ...,
                "NEIPOT12__SOL": {
                    "plain": {"operator": ComparisonOperator.SUP, "value": 10},
                    "mountain": {"operator": ComparisonOperator.INF, "value": 10},
                },  # won't be kept
            },
            "B4": {
                "level": 2,  # => level_int
                "start": ...,
                "stop": ...,
                "centroid": ...,
                "NEIPOT12__SOL": {
                    "plain": {"operator": ComparisonOperator.SUP, "value": 10},
                    "mountain": {"operator": ComparisonOperator.INF, "value": 5},
                },  # will be kept
            },
        }
        strategy = RiskReducerStrategyMonozone(
            parent=RiskReducerFactory(reduction=reduction)
        )
        strategy.find_levels()
        assert strategy.reduction == reduction | {
            "level_max": {
                "EAU24__SOL": {
                    "plain": {"operator": ComparisonOperator.SUP, "value": 20}
                },
                "PRECIP1__SOL": {
                    "plain": {"operator": ComparisonOperator.INF, "value": 10}
                },
            },
            "level_int": {
                "NEIPOT12__SOL": {
                    "plain": {"operator": ComparisonOperator.SUP, "value": 10},
                    "mountain": {"operator": ComparisonOperator.INF, "value": 5},
                }
            },
        }

    def test_process_period(self, assert_equals_result):
        # Test for "Neige" hazard_name
        strategy = RiskReducerStrategyMonozone(
            parent=RiskReducerFactory(
                is_multizone_factory=False,
                parent=RiskComponentCompositeFactory(hazard_name="Neige"),
            )
        )
        strategy.process_period()
        assert strategy.reduction is None

        # Test for other hazard_name
        reduction = {
            "not_dict_value": 3,
            "no_start": {"stop": Datetime(2023, 3, 1, 8)},
            "no_stop": {"start": Datetime(2023, 3, 1, 6)},
            "B0": {"start": Datetime(2023, 3, 1, 0), "stop": Datetime(2023, 3, 1, 12)},
            "B1": {"start": Datetime(2023, 3, 2, 12), "stop": Datetime(2023, 3, 2, 18)},
        }
        strategy = RiskReducerStrategyMonozone(
            parent=RiskReducerFactory(reduction=reduction, is_multizone_factory=False)
        )
        strategy.process_period()
        assert_equals_result(strategy.reduction)

    def test_compute(self):
        # To complete...
        # reducer=RiskReducerFactory(final_risk_da_factory=xr.DataArray(),
        #                            norm_risk_factory=[1,0.5,1],
        #                            reduction_factory={})
        pass


class TestRiskReducerStrategyMultizone:
    def test_process_period(self, assert_equals_result):
        strategy = RiskReducerStrategyMultizone(
            parent=RiskReducerFactory(
                reduction={},
                is_multizone_factory=True,
                localisation=RiskLocalisationFactory(
                    periods_name_factory=[
                        "20230301060000_to_20230301080000",
                        "20230301120000_to_20230301160000",
                        "20230302180000_to_20230302230000",
                    ]
                ),
            )
        )
        strategy.process_period()
        assert_equals_result(strategy.reduction)

    def test_compute(self):
        strategy = RiskReducerStrategyMultizone(
            parent=RiskReducerFactory(
                localisation=RiskLocalisationFactory(
                    table_localisation=TableLocalisationFactory(table={"a": "b"})
                )
            )
        )
        assert strategy.compute() == {"a": "b"}


class TestRiskReducerStrategyME:
    def test_process_period(self):
        # Occurrence < 80%
        reducer = RiskReducerFactory(
            reduction={"a": "b"},
            final_risk_max_level_factory=2,
            risk_ds_factory=xr.Dataset(
                {
                    "occurrence": (
                        ["id", "risk_level", "valid_time"],
                        [[[i < 7 for i in range(10)]]],
                    )
                },
                coords={
                    "valid_time": [
                        Datetime(2023, 3, 1, i).as_np_dt64 for i in range(10)
                    ],
                    "risk_level": [2],
                    "id": ["geo_id"],
                },
            ),
        )
        strategy = RiskReducerStrategyMEFactory(parent=reducer)
        strategy.process_period()
        assert reducer.reduction == {
            "a": "b",
            "temporality": "la nuit de mardi à mercredi et mercredi en début de "
            "matinée",
        }

        # Occurrence > 80%
        reducer = RiskReducerFactory(
            reduction={"a": "b"},
            final_risk_max_level_factory=2,
            risk_ds_factory=xr.Dataset(
                {
                    "occurrence": (
                        ["id", "risk_level", "valid_time"],
                        [[[i < 8 for i in range(10)]]],
                    )
                },
                coords={
                    "valid_time": [
                        Datetime(2023, 3, 1, i).as_np_dt64 for i in range(10)
                    ],
                    "risk_level": [2],
                    "id": ["geo_id"],
                },
            ),
        )
        strategy = RiskReducerStrategyMEFactory(parent=reducer)
        strategy.process_period()
        assert reducer.reduction == {"a": "b"}

    def test_compute(self):
        # Monozone case
        reducer = RiskReducerFactory(
            is_multizone_factory=False,
            get_critical_values_factory=lambda: {
                "FF__RAF": {
                    "mountain": {
                        "operator": ComparisonOperator.SUPEGAL,
                        "threshold": 40,
                        "units": "km/h",
                        "next_critical": 80,
                        "value": 50,
                        "occurrence": True,
                    }
                }
            },
        )
        assert RiskReducerStrategyMEFactory(parent=reducer).compute() == {
            "value": "50 à 55\xa0km/h sur les hauteurs"
        }

        # Multizone case
        reducer = RiskReducerFactory(
            is_multizone_factory=True,
            get_critical_values_factory=lambda: {
                "EAU1__SOL": {
                    "plain": {
                        "operator": ComparisonOperator.SUPEGAL,
                        "threshold": 3.1,
                        "units": "cm",
                        "next_critical": 4.0,
                        "value": 2.0,
                        "occurrence": True,
                    },
                    "mountain": {
                        "operator": ComparisonOperator.SUP,
                        "threshold": 2.4,
                        "units": "cm",
                        "next_critical": 3.0,
                        "value": 5.0,
                        "occurrence": True,
                    },
                }
            },
        )
        assert RiskReducerStrategyMEFactory(
            parent=reducer, localisation_factory="XXX"
        ).compute() == {
            "value": "au maximum 3\xa0cm en 1h (localement 3 à 7\xa0cm)",
            "localisation": "XXX",
        }

        # Test when the fusion of names is the domain - see #45337
        reducer = RiskReducerFactory(
            is_multizone_factory=True,
            get_critical_values_factory=lambda: {
                "NEIPOT3__SOL": {
                    "plain": {
                        "operator": ComparisonOperator.SUPEGAL,
                        "threshold": 5.0,
                        "units": "cm",
                        "next_critical": 6.0,
                        "value": 5.5,
                        "occurrence": True,
                    }
                }
            },
            alt_area_name_factory="Domain",
        )
        assert RiskReducerStrategyMEFactory(
            parent=reducer, localisation_factory="Domain"
        ).compute() == {"value": "5 à 7\xa0cm en 3h"}
