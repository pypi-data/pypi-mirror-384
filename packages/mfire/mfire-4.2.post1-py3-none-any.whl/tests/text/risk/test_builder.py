from unittest.mock import patch

import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.composite.event import Threshold
from mfire.composite.operator import ComparisonOperator
from mfire.text.risk.builder import (
    RiskBuilderStrategyME,
    RiskBuilderStrategyMonozone,
    RiskBuilderStrategyMultizone,
    RiskBuilderStrategyRain,
    RiskBuilderStrategySnow,
)
from mfire.utils.date import Datetime, Timedelta
from tests.composite.factories import (
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
    RiskBuilderFactory,
    RiskBuilderStrategyFactory,
    RiskBuilderStrategyMEFactory,
    RiskBuilderStrategyRainFactory,
    RiskBuilderStrategySnowFactory,
    RiskReducerFactory,
    RiskReducerStrategyMonozoneFactory,
)

# -----------------
# BUILDER TESTS
# -----------------


class TestRiskBuilder:
    def test_init_reducer(self):
        builder = RiskBuilderFactory()
        assert builder.reducer.geo_id == "geo_id"

    def test_hazard_name(self):
        assert (
            RiskBuilderFactory(
                parent=RiskComponentCompositeFactory(hazard_name="test")
            ).hazard_name
            == "test"
        )

    def test_strategy(self):
        assert isinstance(
            RiskBuilderFactory(hazard_name_factory="ME_XXX").strategy,
            RiskBuilderStrategyME,
        )
        assert isinstance(
            RiskBuilderFactory(hazard_name_factory="Neige").strategy,
            RiskBuilderStrategySnow,
        )
        assert isinstance(
            RiskBuilderFactory(hazard_name_factory="Pluies").strategy,
            RiskBuilderStrategyRain,
        )
        assert isinstance(
            RiskBuilderFactory(is_multizone_factory=True).strategy,
            RiskBuilderStrategyMultizone,
        )
        assert isinstance(
            RiskBuilderFactory(is_multizone_factory=False).strategy,
            RiskBuilderStrategyMonozone,
        )

    def test_template_key(self):
        assert (
            RiskBuilderFactory(
                strategy_factory=RiskBuilderStrategyFactory(template_key_factory="test")
            ).template_key
            == "test"
        )

    def test_template_name(self):
        assert (
            RiskBuilderFactory(
                strategy_factory=RiskBuilderStrategyFactory(
                    template_name_factory="test"
                )
            ).template_name
            == "test"
        )

    def test_is_multizone(self):
        builder = RiskBuilderFactory(
            reducer=RiskReducerFactory(is_multizone_factory=True)
        )
        assert builder.is_multizone is True

        builder = RiskBuilderFactory(
            reducer=RiskReducerFactory(is_multizone_factory=False)
        )
        assert builder.is_multizone is False

    def test_is_gusts_under_thunderstorm(self):
        # No good hazard_name
        builder = RiskBuilderFactory()
        assert builder.is_gusts_under_thunderstorm is False

        # No WWMF__SOL condition
        builder = RiskBuilderFactory(hazard_name_factory="Rafales")
        assert builder.is_gusts_under_thunderstorm is False

        builder = RiskBuilderFactory(
            parent=RiskComponentCompositeFactory(
                hazard_name="Rafales", levels=[LevelCompositeFactory(level=2)]
            )
        )
        assert builder.is_gusts_under_thunderstorm is False

        builder = RiskBuilderFactory(
            hazard_name_factory="Rafales",
            parent=RiskComponentCompositeFactory(
                levels=[
                    LevelCompositeFactory(
                        level=1,
                        events=[
                            EventCompositeFactory(
                                field=FieldCompositeFactory(name="FF__RAF")
                            )
                        ],
                    )
                ]
            ),
        )
        assert builder.is_gusts_under_thunderstorm is False

        # One no thunderstorm condition
        builder = RiskBuilderFactory(
            hazard_name_factory="Rafales",
            parent=RiskComponentCompositeFactory(
                levels=[
                    LevelCompositeFactory(
                        level=1,
                        events=[
                            EventCompositeFactory(
                                field=FieldCompositeFactory(name="WWMF__SOL"),
                                plain=Threshold(
                                    threshold=[90, 50],
                                    comparison_op=ComparisonOperator.ISIN,
                                ),
                            )
                        ],
                    )
                ]
            ),
        )
        assert builder.is_gusts_under_thunderstorm is False
        builder = RiskBuilderFactory(
            hazard_name_factory="Rafales",
            parent=RiskComponentCompositeFactory(
                levels=[
                    LevelCompositeFactory(
                        level=1,
                        events=[
                            EventCompositeFactory(
                                field=FieldCompositeFactory(name="WWMF__SOL"),
                                plain=Threshold(
                                    threshold=[90],
                                    comparison_op=ComparisonOperator.ISIN,
                                ),
                                mountain=Threshold(
                                    threshold=[50],
                                    comparison_op=ComparisonOperator.ISIN,
                                ),
                            )
                        ],
                    )
                ]
            ),
        )
        assert builder.is_gusts_under_thunderstorm is False

        # Gusts under thunderstorm
        for hazard_name in ["Rafales", "Vent"]:
            builder = RiskBuilderFactory(
                hazard_name_factory=hazard_name,
                parent=RiskComponentCompositeFactory(
                    levels=[
                        LevelCompositeFactory(
                            level=1,
                            events=[
                                EventCompositeFactory(
                                    field=FieldCompositeFactory(name="WWMF__SOL"),
                                    plain=Threshold(
                                        threshold=[92],
                                        comparison_op=ComparisonOperator.ISIN,
                                    ),
                                    mountain=Threshold(
                                        threshold=[90, 91],
                                        comparison_op=ComparisonOperator.ISIN,
                                    ),
                                )
                            ],
                        )
                    ]
                ),
            )
            assert builder.is_gusts_under_thunderstorm is True

    def test_post_process_gusts_under_thunderstorm(self):
        # Gust events with risk_level=0
        builder = RiskBuilderFactory(
            text="Risk text.",
            reducer=RiskReducerFactory(final_risk_max_level_factory=0),
        )
        builder.post_process_gusts_under_thunderstorm()
        assert builder.text == "Risk text."

        # No thunderstorm events
        builder = RiskBuilderFactory(
            text="Risk text.",
            _gusts_under_thunderstorm_event_factory=EventCompositeFactory(
                values_ds_factory=xr.Dataset({"occurrence_event": False})
            ),
            reducer=RiskReducerFactory(final_risk_max_level_factory=1),
        )
        builder.post_process_gusts_under_thunderstorm()
        assert builder.text == "Risk text."

        # Thunderstorm events
        builder = RiskBuilderFactory(
            text="Risk text.",
            _gusts_under_thunderstorm_event_factory=EventCompositeFactory(
                values_ds_factory=xr.Dataset({"occurrence_event": True})
            ),
            reducer=RiskReducerFactory(final_risk_max_level_factory=1),
        )
        builder.post_process_gusts_under_thunderstorm()
        assert builder.text == "Risk text.\nRafales plus fortes sous orage."


# -----------------
# STRATEGY TESTS
# -----------------


class TestRiskBuilderStrategy:

    def test_reducer(self):
        strategy = RiskBuilderStrategyFactory(
            parent=RiskBuilderFactory(reducer=RiskReducerFactory(geo_id="test"))
        )
        assert strategy.reducer.geo_id == "test"

    def test_reduction(self):
        strategy = RiskBuilderStrategyFactory(
            parent=RiskBuilderFactory(reduction_factory={"a": "b"})
        )
        assert strategy.reduction == {"a": "b"}

    def test_text(self):
        # Test getter method
        strategy = RiskBuilderStrategyFactory(parent=RiskBuilderFactory(text="test1"))
        assert strategy.text == "test1"

        # Test setter method
        strategy.text = "test2"
        assert strategy.text == "test2"


class TestRiskBuilderStrategyMonozone:
    def test_template_name(self):
        assert (
            RiskBuilderStrategyMonozone(parent=RiskBuilderFactory()).template_name
            == "monozone"
        )

    def test_template_key(self):
        assert (
            RiskBuilderStrategyMonozone(
                parent=RiskBuilderFactory(
                    reducer=RiskReducerFactory(
                        strategy_factory=RiskReducerStrategyMonozoneFactory(
                            norm_risk_factory=[1, 2]
                        )
                    )
                )
            )
        ).template_key == [1, 2]

    @pytest.mark.parametrize(
        "reduction",
        [
            {
                "B0": {
                    "level": ...,
                    "T__HAUTEUR2": {
                        "plain": {
                            "units": "celsius",
                            "operator": ComparisonOperator.SUPEGAL,
                            "value": 2,
                        },
                        "mountain_altitude": 1200,
                    },
                    "RAF__HAUTEUR10": {
                        "mountain": {
                            "units": "km/h",
                            "operator": ComparisonOperator.SUPEGAL,
                            "value": 10,
                        },
                        "mountain_altitude": 1200,
                    },
                }
            },
            {
                "B0": {
                    "level": ...,
                    "FF__HAUTEUR10": {
                        "plain": {
                            "units": "km/h",
                            "operator": ComparisonOperator.SUPEGAL,
                            "value": 2,
                        },
                        "mountain": {
                            "units": "km/h",
                            "operator": ComparisonOperator.SUPEGAL,
                            "value": 5,
                        },
                        "mountain_altitude": 1200,
                    },
                    "NEIPOT24__SOL": {
                        "plain": {
                            "units": "cm",
                            "operator": ComparisonOperator.SUPEGAL,
                            "value": 5,
                        },
                        "mountain": {
                            "units": "cm",
                            "operator": ComparisonOperator.SUPEGAL,
                            "value": 10,
                        },
                        "mountain_altitude": 1200,
                    },
                }
            },
            {
                "B0": {
                    "level": ...,
                    "PRECIP1__SOL": {
                        "plain": {
                            "units": "cm",
                            "operator": ComparisonOperator.SUPEGAL,
                            "value": 2,
                        },
                        "mountain_altitude": 1200,
                    },
                    "EAU24__SOL": {
                        "mountain": {
                            "units": "cm",
                            "operator": ComparisonOperator.SUPEGAL,
                            "value": 10,
                        },
                        "mountain_altitude": 1200,
                    },
                }
            },
            {
                "B0": {
                    "level": ...,
                    "PRECIP12__SOL": {
                        "plain": {
                            "units": "cm",
                            "operator": ComparisonOperator.SUPEGAL,
                            "value": 2,
                        },
                        "mountain_altitude": 1200,
                    },
                    "EAU24__SOL": {
                        "mountain": {
                            "units": "cm",
                            "operator": ComparisonOperator.SUPEGAL,
                            "value": 10,
                        },
                        "mountain_altitude": 1200,
                    },
                }
            },
            {
                "B0": {
                    "level": ...,
                    "NEIPOT1__SOL": {
                        "plain": {
                            "units": "cm",
                            "operator": ComparisonOperator.SUPEGAL,
                            "value": 2,
                        }
                    },
                }
            },
            {
                "B0": {
                    "level": ...,
                    "NEIPOT1__SOL": {
                        "plain": {
                            "units": "cm",
                            "operator": ComparisonOperator.SUPEGAL,
                            "value": 2,
                        }
                    },
                    "NEIPOT24__SOL": {
                        "plain": {
                            "units": "cm",
                            "operator": ComparisonOperator.SUPEGAL,
                            "value": 2,
                        }
                    },
                }
            },
            {"B0": {"level": ..., "NEIPOT1__SOL": {}, "RAF__HAUTEUR10": {}}},
        ],
    )
    def test_post_process(self, reduction, assert_equals_result):
        np.random.seed(0)
        strategy = RiskBuilderStrategyMonozone(
            parent=RiskBuilderFactory(
                text="Template du monozone. {B0_val}",
                reducer=RiskReducerFactory(reduction=reduction | {"type": "OTHER"}),
            )
        )
        strategy.post_process()
        assert_equals_result(strategy.text)


class TestRiskBuilderStrategyMultizone:
    def test_template_name(self):
        assert (
            RiskBuilderStrategyMultizone(parent=RiskBuilderFactory()).template_name
            == "multizone"
        )

    def test_template_key(self):
        assert (
            RiskBuilderStrategyMonozone(
                parent=RiskBuilderFactory(
                    reducer=RiskReducerFactory(
                        strategy_factory=RiskReducerStrategyMonozoneFactory(
                            norm_risk_factory=[1, 2]
                        )
                    )
                )
            )
        ).template_key == [1, 2]

    @pytest.mark.parametrize(
        "data",
        [
            # Empty data
            {},
            # Altitude builder
            {
                "NEIPOT1__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    },
                    "mountain_altitude": 1200,
                },
                "NEIPOT24__SOL": {
                    "mountain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 10,
                    },
                    "mountain_altitude": 1200,
                },
            },
            {
                "NEIPOT1__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    },
                    "mountain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 5,
                    },
                    "mountain_altitude": 1200,
                },
                "NEIPOT24__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 5,
                    },
                    "mountain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 10,
                    },
                    "mountain_altitude": 1200,
                },
            },
            {
                "NEIPOT1__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    },
                    "mountain_altitude": 1200,
                },
                "EAU24__SOL": {
                    "mountain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 10,
                    },
                    "mountain_altitude": 1200,
                },
            },
            {
                "PRECIP12__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    },
                    "mountain_altitude": 1200,
                },
                "EAU24__SOL": {
                    "mountain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 10,
                    },
                    "mountain_altitude": 1200,
                },
            },
            # No mountain_altitude
            {
                "NEIPOT1__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    }
                }
            },
            # Homogeneous var_name
            {
                "NEIPOT1__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    }
                },
                "NEIPOT24__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    }
                },
            },
            # Not homogeneous var_name
            {"NEIPOT1__SOL": {}, "RAF__HAUTEUR10": {}},
        ],
    )
    def test_post_process(self, data, assert_equals_result):
        np.random.seed(0)
        strategy = RiskBuilderStrategyMultizone(
            parent=RiskBuilderFactory(
                text="Template du multizone.",
                reducer=RiskReducerFactory(get_critical_values_factory=lambda: data),
            )
        )
        strategy.post_process()
        assert_equals_result(strategy.text)


class TestRiskBuilderStrategyME:

    def test_template_name(self):
        assert RiskBuilderStrategyMEFactory().template_name == "ME"

    def test_template_key(self):
        assert RiskBuilderStrategyMEFactory(reduction_factory={}).template_key == "RAS"
        assert (
            RiskBuilderStrategyMEFactory(
                reduction_factory={
                    "temporality": ...,
                    "value": ...,
                    "localisation": ...,
                }
            ).template_key
            == "temp+val+loc"
        )
        assert (
            RiskBuilderStrategyMEFactory(
                reduction_factory={
                    "temporality": ...,
                    "value": ...,
                    "localisation": ...,
                },
                parent=RiskBuilderFactory(hazard_name_factory="test_bis"),
            ).template_key
            == "val+loc"
        )


class TestRiskBuilderStrategyRain:

    def test_template_name(self):
        assert RiskBuilderStrategyRainFactory().template_name == "rain"

    def test_template_key(self):
        assert (
            RiskBuilderStrategyRainFactory(
                reduction_factory={"key": "test"}
            ).template_key
            == "test"
        )

    def test_post_process(self):
        strategy = RiskBuilderStrategyRainFactory()

        with patch(
            "mfire.text.risk.builder.RiskBuilderStrategyMultizone.post_process"
        ) as mock:
            strategy.post_process()
            assert mock.call_count == 1


class TestRiskBuilderStrategySnow:

    def test_template_name(self):
        assert RiskBuilderStrategySnowFactory().template_name == "snow"

    def test_template_key(self):
        assert (
            RiskBuilderStrategySnowFactory(
                reduction_factory={"key": "test"}
            ).template_key
            == "test"
        )

    @pytest.mark.parametrize(
        "data",
        [
            # Altitude builder
            {
                "NEIPOT1__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    },
                    "mountain_altitude": 1200,
                },
                "NEIPOT24__SOL": {
                    "mountain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 10,
                    },
                    "mountain_altitude": 1200,
                },
            },
            {
                "NEIPOT1__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    },
                    "mountain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 5,
                    },
                    "mountain_altitude": 1200,
                },
                "NEIPOT24__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 5,
                    },
                    "mountain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 10,
                    },
                    "mountain_altitude": 1200,
                },
            },
            # No mountain_altitude
            {
                "NEIPOT1__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    }
                }
            },
            # Homogeneous var_name
            {
                "NEIPOT1__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    }
                },
                "NEIPOT24__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    }
                },
            },
        ],
    )
    @pytest.mark.parametrize("has_lpn", [True, False])
    def test_post_process(self, data, has_lpn, assert_equals_result):
        np.random.seed(0)

        if has_lpn:
            data = data.copy() | {"LPN__SOL": {}}

        lpn = [100, 500, 200, 1000]
        valid_time = [Datetime(2023, 3, 1, 3 * i).as_np_dt64 for i in range(len(lpn))]
        lpn = xr.DataArray(
            [[lpn, [v + 5 for v in lpn]]],  # test minimal value taken over space
            coords={"latitude": [30], "longitude": [40, 41], "valid_time": valid_time},
        )
        wwmf = xr.DataArray(
            [[[60] * 4] * 2],
            coords={"latitude": [30], "longitude": [40, 41], "valid_time": valid_time},
        )

        levels = [
            LevelCompositeFactory(
                level=2,
                spatial_risk_da_factory=xr.DataArray(
                    [[[[True] * len(valid_time)] * 2]],
                    coords={
                        "id": ["geo_id"],
                        "latitude": [30],
                        "longitude": [40, 41],
                        "valid_time": valid_time,
                    },
                ),
            )
        ]
        component = RiskComponentCompositeFactory(
            params={
                "LPN__SOL": FieldCompositeFactory(compute_factory=lambda: lpn),
                "WWMF__SOL": FieldCompositeFactory(compute_factory=lambda: wwmf),
            },
            geo_factory=lambda _: xr.DataArray(
                [[True, True]], coords={"latitude": [30], "longitude": [40, 41]}
            ),
            levels=levels,
        )
        strategy = RiskBuilderStrategySnowFactory(
            reducer_factory=RiskReducerFactory(
                get_critical_values_factory=lambda: data
            ),
            parent=RiskBuilderFactory(parent=component, text="L1\nL2\nL3"),
        )
        strategy.post_process()
        assert_equals_result(strategy.text)


# -----------------
# INTEGRATION TESTS
# -----------------


class TestRiskBuilderMonozone:

    def test_template_key(self):
        valid_time = [Datetime(2023, 3, 1, i).as_np_dt64 for i in range(3)]
        composite = RiskComponentCompositeFactory(
            data=xr.Dataset(
                None, coords={"id": ["geo_id"], "risk_level": (["id"], [2])}
            ),
            final_risk_da_factory=xr.DataArray(
                [[2, 1, 2]], coords={"id": ["geo_id"], "valid_time": valid_time}
            ),
            final_risk_max_level_factory={"geo_id": 2},
        )
        reducer = RiskReducerFactory(
            reduction={"type": "general"}, is_multizone_factory=False, parent=composite
        )
        builder = RiskBuilderFactory(reducer=reducer)
        assert_identically_close(builder.template_key, np.array([1.0, 1.0, 1.0]))

    def test_template_name(self):
        builder = RiskBuilderFactory(is_multizone_factory=False)
        assert builder.template_name == "monozone"

    def test_compute_simple_generic(self, assert_equals_result):
        np.random.seed(0)
        assert_equals_result(
            RiskBuilderFactory(
                reducer=RiskReducerFactory(
                    reduction={
                        "type": "OTHER",
                        "B0": {
                            "start": "en début de nuit de mardi à mercredi",
                            "centroid": 1.0,
                            "level": 2,
                            "T__HAUTEUR": {
                                "plain": {
                                    "min": 1.0,
                                    "max": 1.2,
                                    "value": 1.1,
                                    "units": "celsius",
                                    "operator": "supegal",
                                }
                            },
                            "FF__HAUTEUR10": {
                                "plain": {
                                    "min": 50.0,
                                    "max": 52.0,
                                    "value": 51.0,
                                    "units": "km/h",
                                    "operator": "sup",
                                },
                                "mountain": {
                                    "min": 53.0,
                                    "max": 55.0,
                                    "value": 54.0,
                                    "units": "km/h",
                                    "operator": "inf",
                                },
                            },
                            "stop": "ce milieu de nuit de mardi à mercredi",
                            "period": "la nuit de mardi à mercredi",
                        },
                        "level_max": {
                            "RAF__HAUTEUR10": {
                                "plain": {
                                    "min": 4.0,
                                    "max": 4.2,
                                    "value": 4.1,
                                    "units": "km/h",
                                    "operator": "supegal",
                                }
                            },
                            "EAU12__SOL": {
                                "plain": {
                                    "min": 80.0,
                                    "max": 82.0,
                                    "value": 81.0,
                                    "units": "mm",
                                    "operator": "sup",
                                },
                                "mountain": {
                                    "min": 83.0,
                                    "max": 85.0,
                                    "value": 84.0,
                                    "units": "mm",
                                    "operator": "inf",
                                },
                            },
                        },
                        "level_int": {
                            "PRECIP1__SOL": {
                                "plain": {
                                    "min": 20.0,
                                    "max": 32.0,
                                    "value": 31.0,
                                    "units": "mm",
                                    "operator": "supegal",
                                }
                            }
                        },
                    }
                ),
                is_multizone_factory=False,
                template_factory="Risque à partir de {B0_start} jusqu'à {B0_stop}. "
                "{B0_val}. Level max : {level_max_val}. Level int : "
                "{level_int_val}.",
            ).compute()
        )

    @pytest.mark.parametrize(
        "hazard_name,evt1_name,evt2_name,evt1_unit,evt2_unit",
        [
            # Normal hazard_name
            ("XXX", "EAU24__SOL", "EAU12__SOL", "mm", "mm"),
            ("XXX", "EAU24__SOL", "FF__HAUTEUR", "mm", "km/h"),
            ("XXX", "FF__HAUTEUR", "RAF__HAUTEUR", "km/h", "km/h"),
            # ME hazard_name
            ("ME_XXX", "EAU24__SOL", "EAU12__SOL", "mm", "mm"),
            ("ME_XXX_bis", "NEIPOT12__SOL", "NEIPOT3__SOL", "mm", "mm"),
            ("ME_XXX", "FF__RAF", "FF__RAF", "km/h", "km/h"),
            ("ME_XXX_bis", "FF__RAF", "FF__RAF", "km/h", "km/h"),
        ],
    )
    def test_compute(
        self,
        hazard_name,
        evt1_name,
        evt2_name,
        evt1_unit,
        evt2_unit,
        assert_equals_result,
    ):
        np.random.seed(0)
        valid_time = [Datetime(2023, 3, 1, 3 * i).as_np_dt64 for i in range(4)]

        lvl1 = LevelCompositeFactory(
            level=1,
            events=[
                EventCompositeFactory(
                    field=FieldCompositeFactory(name=evt1_name),
                    plain=Threshold(
                        threshold=2.0,
                        comparison_op=ComparisonOperator.SUP,
                        units=evt1_unit,
                    ),
                )
            ],
        )
        lvl2 = LevelCompositeFactory(
            level=2,
            events=[
                # only plain event
                EventCompositeFactory(
                    field=FieldCompositeFactory(name=evt1_name),
                    plain=Threshold(
                        threshold=1.5,
                        comparison_op=ComparisonOperator.SUP,
                        units=evt1_unit,
                    ),
                ),
                # plain and mountain event
                EventCompositeFactory(
                    field=FieldCompositeFactory(name=evt2_name),
                    plain=Threshold(
                        threshold=20,
                        comparison_op=ComparisonOperator.SUP,
                        units=evt2_unit,
                    ),
                    mountain=Threshold(
                        threshold=30,
                        comparison_op=ComparisonOperator.SUPEGAL,
                        units=evt2_unit,
                    ),
                ),
            ],
        )
        parent = RiskComponentCompositeFactory(
            hazard_name=hazard_name,
            final_risk_da_factory=xr.DataArray(
                [[2, 1, 1, 2]], coords={"id": ["geo_id"], "valid_time": valid_time}
            ),
            levels=[lvl1, lvl2],
            alt_area_name_factory=lambda _: "domain",
        )

        builder = RiskBuilderFactory(
            parent=parent,
            reducer=RiskReducerFactory(
                final_risk_max_level_factory=2,
                risk_ds_factory=xr.Dataset(
                    {
                        "occurrence": (
                            ["id", "risk_level", "valid_time"],
                            [[[False, False, True, True], [False, False, True, True]]],
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
                        "threshold_mountain": (
                            ["risk_level", "evt"],
                            [[15, 20], [25, 30]],
                        ),
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
                    },
                ),
                is_multizone_factory=False,
                parent=parent,
            ),
        )
        assert_equals_result(
            {language: builder.compute() for language in builder.iter_languages()}
        )

    @pytest.mark.parametrize(
        "offset,inputs,expected",
        [
            (0, [3, 0, 3], "Risque sur toute la période. {B0_val}."),
            (
                0,
                [3, 3, 3, 3, 0, 0, 0, 0, 0],
                "Risque jusqu'à cette fin de nuit de mardi à mercredi. {B0_val}.",
            ),
            (
                12,
                [0, 3, 3, 3, 3, 3, 0, 0, 0, 0],
                "Risque jusqu'à ce mercredi après-midi. {B0_val}.",
            ),
            (
                13,
                [0, 3, 3, 3, 3, 3, 0, 0, 0, 0],
                "Risque jusqu'à ce mercredi soir. {B0_val}.",
            ),
            (
                14,
                [0, 3, 3, 3, 3, 3, 0, 0, 0, 0],
                "Risque jusqu'à ce mercredi soir. {B0_val}.",
            ),
            (
                12,
                [0, 0, 0, 3, 3, 3, 0, 0, 0, 0],
                "Risque ce mercredi après-midi. {B1_val}.",
            ),
            (
                13,
                [0, 0, 0, 3, 3, 3, 0, 0, 0, 0],
                "Risque ce mercredi après-midi et soirée. {B1_val}.",
            ),
            (
                14,
                [0, 0, 0, 3, 3, 3, 0, 0, 0, 0],
                "Risque ce mercredi après-midi et soirée. {B1_val}.",
            ),
            (
                10,
                [0, 0, 0, 3, 3, 3, 3, 3, 0, 0],
                "Risque à partir de ce mercredi en milieu de journée. {B1_val}.",
            ),
            (
                11,
                [0, 0, 0, 3, 3, 3, 0, 3, 0, 0],
                "Risque à partir de ce mercredi en milieu de journée. {B1_val}.",
            ),
            (
                12,
                [0, 0, 0, 3, 3, 3, 0, 3, 0, 0],
                "Risque à partir de ce mercredi après-midi. {B1_val}.",
            ),
            (
                12,
                [0, 0, 0, 3, 0, 0, 0, 0, 0, 0],
                "Risque ce mercredi après-midi. {B1_val}.",
            ),
            (
                12,
                [0, 3, 3, 0, 0, 0, 0, 0, 0, 0],
                "Risque jusqu'à ce mercredi en milieu de journée. {B0_val}.",
            ),
            (
                13,
                [0, 0, 0, 3, 0, 0, 0, 0, 0, 0],
                "Risque ce mercredi après-midi. {B1_val}.",
            ),
            (
                13,
                [0, 3, 3, 0, 0, 0, 0, 0, 0, 0],
                "Risque jusqu'à ce mercredi après-midi. {B0_val}.",
            ),
            (
                7,
                [0, 0, 0, 3, 0, 3, 3, 0, 0, 0],
                "Risque ce mercredi mi-journée. {B1_val}.",
            ),
            (
                7,
                [0, 0, 3, 0, 0, 0, 0, 3, 0, 0],
                "Risque sur toute la période. {B0_val}.",
            ),
            (
                8,
                [0, 0, 3, 0, 0, 0, 0, 3, 0, 0],
                "Risque jusqu'à ce mercredi en fin de matinée. "
                "Nouveau risque à partir de ce mercredi après-midi. {level_max_val}.",
            ),
            (
                7,
                [0, 0, 3, 0, 0, 0, 0, 0, 3, 0, 0],
                "Risque jusqu'à ce mercredi en fin de matinée. Nouveau risque à partir "
                "de ce mercredi après-midi. {level_max_val}.",
            ),
            (3, [0, 0, 0, 3, 0, 3, 3, 0, 0, 0], "Risque ce mercredi matin. {B1_val}."),
            (
                3,
                [0, 0, 3, 0, 0, 0, 0, 0, 3, 0, 0],
                "Risque jusqu'à cette fin de nuit de mardi à mercredi. Nouveau risque "
                "à partir de ce mercredi en fin de matinée. {level_max_val}.",
            ),
        ],
    )
    def test_compute_with_flashing_levels(self, offset, inputs, expected):
        # This test ensures that repetition of date blocks are avoided - cf #34947
        valid_time = [
            (Datetime(2023, 3, 1) + Timedelta(hours=i + offset)).as_np_dt64
            for i in range(len(inputs))
        ]

        lvl = LevelCompositeFactory(
            level=3,
            events=[
                EventCompositeFactory(field=FieldCompositeFactory(name="FF__HAUTEUR10"))
            ],
        )

        reducer = RiskReducerFactory(
            is_multizone_factory=False,
            parent=RiskComponentCompositeFactory(levels=[lvl]),
            risk_ds_factory=xr.Dataset(
                {"weatherVarName": (["evt", "risk_level"], [["FF__HAUTEUR10"]])},
                coords={
                    "id": ["geo_id"],
                    "valid_time": valid_time,
                    "risk_level": [3],
                    "evt": [0],
                    "units": (["risk_level", "evt"], [["km/h"]]),
                },
            ),
            final_risk_da_factory=xr.DataArray(
                inputs, coords={"valid_time": valid_time}
            ),
        )
        builder = RiskBuilderFactory(reducer=reducer, post_process_factory=lambda: None)
        assert builder.compute() == expected


class TestRiskBuilderMultizone:
    def test_template(self, assert_equals_result):
        np.random.seed(0)

        keys = [
            "P1_0_1",
            "P2_1_2",
            "P2_1_3",
            "P2_2_3",
            "P2_0_1_2",
            "P2_0_1_3",
            "P2_0_2_3",
            "P2_1_2_3",
            "P3_2_5",
            "P3_2_7",
            "P3_3_5",
            "P3_3_6",
            "P3_5_6",
            "P3_5_7",
            "P3_0_2_5",
            "P3_0_2_7",
            "P3_0_3_5",
            "P3_0_3_6",
            "P3_0_5_6",
            "P3_0_5_7",
            "P3_1_2_4",
            "P3_1_2_5",
            "P3_1_2_6",
            "P3_1_2_7",
            "P3_1_3_4",
            "P3_1_3_5",
            "P3_1_3_6",
            "P3_1_3_7",
            "P3_1_4_6",
            "P3_1_4_7",
            "P3_1_5_6",
            "P3_1_5_7",
            "P3_2_3_4",
            "P3_2_3_5",
            "P3_2_3_6",
            "P3_2_3_7",
            "P3_2_4_5",
            "P3_2_4_7",
            "P3_2_5_6",
            "P3_2_5_7",
            "P3_2_6_7",
            "P3_3_4_5",
            "P3_3_4_6",
            "P3_3_5_6",
            "P3_3_5_7",
            "P3_3_6_7",
            "P3_4_5_6",
            "P3_4_5_7",
            "P3_4_6_7",
            "P3_5_6_7",
        ]

        builder = RiskBuilderFactory(
            reducer=RiskReducerFactory(is_multizone_factory=True)
        )
        result = {}
        for language in builder.iter_languages():
            result[language] = {}
            for key in keys:
                builder.template_key_factory = key
                result[language][key] = builder.template.format(
                    alt_area_name="domain",
                    zone1="Zone 1",
                    zone2="Zone 2",
                    zone3="Zone 3",
                    zone1_2="Zone 1 et 2",
                    zone1_3="Zone 1 et 3",
                    zone2_3="Zone 2 et 3",
                    zone1_2_3="Zone 1, 2 et 3",
                    periode1="Periode 1",
                    periode2="Periode 2",
                    periode3="Periode 3",
                    periode1_2="Periodes 1 et 2",
                    periode1_3="Periodes 1 et 3",
                    periode2_3="Periodes 2 et 3",
                    periode1_2_3="Periodes 1, 2 et 3",
                )

        assert_equals_result(result)

    def test_template_key(self):
        reducer = RiskReducerFactory(
            is_multizone_factory=True,
            localisation=RiskLocalisationFactory(unique_name_factory="test"),
        )
        assert RiskBuilderFactory(reducer=reducer).template_key == "test"

    def test_template_name(self):
        assert (
            RiskBuilderFactory(
                reducer=RiskReducerFactory(is_multizone_factory=True)
            ).template_name
            == "multizone"
        )

    @pytest.mark.parametrize(
        "hazard_name,evt1_name,evt2_name,evt1_unit,evt2_unit",
        [
            ("XXX", "EAU24__SOL", "EAU12__SOL", "mm", "mm"),  # Type PRECIP
            ("XXX", "EAU24__SOL", "FF__HAUTEUR", "mm", "km/h"),  # Type general
            ("XXX", "FF__HAUTEUR", "RAF__HAUTEUR", "km/h", "km/h"),  # Type general
            # ME hazard_name
            ("ME_XXX", "EAU24__SOL", "EAU12__SOL", "mm", "mm"),
            ("ME_XXX_bis", "NEIPOT12__SOL", "NEIPOT3__SOL", "mm", "mm"),
            ("ME_XXX", "FF__RAF", "FF__RAF", "km/h", "km/h"),
            ("ME_XXX_bis", "FF__RAF", "FF__RAF", "km/h", "km/h"),
        ],
    )
    def test_compute(
        self,
        hazard_name,
        evt1_name,
        evt2_name,
        evt1_unit,
        evt2_unit,
        assert_equals_result,
    ):
        np.random.seed(0)

        valid_time = [Datetime(2023, 3, 1, 3 * i).as_np_dt64 for i in range(4)]
        lvl1 = LevelCompositeFactory(
            level=1,
            events=[
                EventCompositeFactory(
                    field=FieldCompositeFactory(name=evt1_name),
                    plain=Threshold(
                        threshold=2.0,
                        comparison_op=ComparisonOperator.SUP,
                        units=evt1_unit,
                    ),
                )
            ],
        )
        lvl2 = LevelCompositeFactory(
            level=2,
            events=[
                # only plain event
                EventCompositeFactory(
                    field=FieldCompositeFactory(name=evt1_name),
                    plain=Threshold(
                        threshold=1.5,
                        comparison_op=ComparisonOperator.SUP,
                        units=evt1_unit,
                    ),
                ),
                # plain and mountain event
                EventCompositeFactory(
                    field=FieldCompositeFactory(name=evt2_name),
                    plain=Threshold(
                        threshold=20,
                        comparison_op=ComparisonOperator.SUP,
                        units=evt2_unit,
                    ),
                    mountain=Threshold(
                        threshold=30,
                        comparison_op=ComparisonOperator.SUPEGAL,
                        units=evt2_unit,
                    ),
                ),
            ],
        )

        ids = ["id1"]

        risk_ds = xr.Dataset(
            {
                "occurrence": (
                    ["id", "risk_level", "valid_time"],
                    [[[True, True, False, False], [True, True, False, False]]],
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
                "rep_value_plain": (
                    ["id", "risk_level", "evt", "valid_time"],
                    [
                        [
                            [[11.0, 21.0, 31.0, 41.0], 4 * [np.nan]],
                            [[1.1, 2.1, 3.1, 4.1], [51.0, 61.0, 71.0, 81.0]],
                        ]
                    ],
                ),
                "rep_value_mountain": (
                    ["id", "risk_level", "evt", "valid_time"],
                    [[2 * [4 * [np.nan]], [4 * [np.nan], [54.0, 64.0, 74.0, 84.0]]]],
                ),
            },
            coords={
                "id": ids,
                "evt": [0, 1],
                "risk_level": [1, 2],
                "valid_time": valid_time,
                "units": (
                    ["risk_level", "evt"],
                    [[evt1_unit, np.nan], [evt1_unit, evt2_unit]],
                ),
                "altAreaName": (["id"], ["domain"]),
            },
        )
        risk_component = RiskComponentCompositeFactory(
            hazard_name=hazard_name,
            risk_ds_factory=risk_ds,
            levels=[lvl1, lvl2],
            final_risk_max_level_factory=lambda _: 2,
        )

        localisation = RiskLocalisationFactory(
            parent=risk_component,
            geo_id="id1",
            all_name_factory="Area",
            periods_name_factory=[
                "20230301060000_to_20230301080000",
                "20230301120000_to_20230301160000",
                "20230302180000_to_20230302230000",
            ],
            table_localisation=TableLocalisationFactory(
                table={"zone1": "Z1", "zone2": "Z2"}
            ),
            spatial_localisation=SpatialLocalisationFactory(
                parent=risk_component, localised_risk_ds_factory=risk_ds
            ),
            unique_name_factory="P3_2_5",
        )
        builder = RiskBuilderFactory(
            parent=risk_component,
            is_multizone_factory=True,
            reducer=RiskReducerFactory(
                geo_id=ids[0], parent=risk_component, localisation=localisation
            ),
        )
        assert_equals_result(
            {language: builder.compute() for language in builder.iter_languages()}
        )


class TestRiskBuilderME:

    def test_template_key(self):
        assert (
            RiskBuilderFactory(
                hazard_name_factory="ME_XXX", reduction_factory={}
            ).template_key
            == "RAS"
        )

        reduction = {"temporality": ..., "value": ..., "localisation": ...}
        assert (
            RiskBuilderFactory(
                hazard_name_factory="ME_XXX", reduction_factory=reduction
            ).template_key
            == "temp+val+loc"
        )
        assert (
            RiskBuilderFactory(
                hazard_name_factory="ME_XXX_bis", reduction_factory=reduction
            ).template_key
            == "val+loc"
        )

    @pytest.mark.parametrize(
        "reduction,expected",
        [
            ({}, ""),
            ({"temporality": "TTT"}, "TTT."),
            ({"value": "VVV"}, "VVV."),
            ({"localisation": "LLL"}, "LLL."),
            ({"temporality": "TTT", "value": "VVV"}, "TTT, VVV."),
            ({"temporality": "TTT", "localisation": "LLL"}, "TTT, LLL."),
            ({"value": "VVV", "localisation": "LLL"}, "VVV, LLL."),
            (
                {"temporality": "TTT", "value": "VVV", "localisation": "LLL"},
                "TTT, VVV, LLL.",
            ),
        ],
    )
    def test_compute(self, reduction, expected):
        assert (
            RiskBuilderFactory(
                hazard_name_factory="ME_XXX", reduction_factory=reduction
            ).compute()
            == expected
        )


class TestRiskBuilderSnow:

    def test_template_key(self):
        assert (
            RiskBuilderFactory(
                hazard_name_factory="Neige", reduction_factory={"key": "template_key"}
            ).template_key
            == "template_key"
        )

    def test_template_name(self):
        assert RiskBuilderFactory(hazard_name_factory="Neige").template_name == "snow"

    @pytest.mark.parametrize("template_key", ["RAS", "low", "moderate", "high"])
    def test_compute(self, template_key, assert_equals_result):
        builder = RiskBuilderFactory(
            template_name_factory="snow",
            template_key_factory=template_key,
            reduction_factory={"periods": "Période", "localisation": "Localisation"},
        )
        assert_equals_result(
            {language: builder.compute() for language in builder.iter_languages()}
        )

    @pytest.mark.parametrize(
        "data",
        [
            # Altitude builder
            {
                "NEIPOT1__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    },
                    "mountain_altitude": 1200,
                },
                "NEIPOT24__SOL": {
                    "mountain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 10,
                    },
                    "mountain_altitude": 1200,
                },
            },
            {
                "NEIPOT1__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    },
                    "mountain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 5,
                    },
                    "mountain_altitude": 1200,
                },
                "NEIPOT24__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 5,
                    },
                    "mountain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 10,
                    },
                    "mountain_altitude": 1200,
                },
            },
            # No mountain_altitude
            {
                "NEIPOT1__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    }
                }
            },
            # Homogeneous var_name
            {
                "NEIPOT1__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    }
                },
                "NEIPOT24__SOL": {
                    "plain": {
                        "units": "cm",
                        "operator": ComparisonOperator.SUPEGAL,
                        "value": 2,
                    }
                },
            },
        ],
    )
    @pytest.mark.parametrize("has_lpn", [True, False])
    def test_post_process(self, data, has_lpn, assert_equals_result):
        np.random.seed(0)

        lpn = [100, 500, 200, 1000]
        valid_time = [Datetime(2023, 3, 1, 3 * i).as_np_dt64 for i in range(len(lpn))]
        lpn = xr.DataArray(
            [[lpn, [v + 5 for v in lpn]]],  # test minimal value taken over space
            coords={"latitude": [30], "longitude": [40, 41], "valid_time": valid_time},
        )
        wwmf = xr.DataArray(
            [[[60] * 4] * 2],
            coords={"latitude": [30], "longitude": [40, 41], "valid_time": valid_time},
        )
        params = {
            "LPN__SOL": FieldCompositeFactory(compute_factory=lambda: lpn),
            "WWMF__SOL": FieldCompositeFactory(compute_factory=lambda: wwmf),
        }
        levels = [
            LevelCompositeFactory(
                level=2,
                spatial_risk_da_factory=xr.DataArray(
                    [[[[True] * len(valid_time)] * 2]],
                    coords={
                        "id": ["geo_id"],
                        "latitude": [30],
                        "longitude": [40, 41],
                        "valid_time": valid_time,
                    },
                ),
            )
        ]

        composite = RiskComponentCompositeFactory(
            params=params,
            hazard_name_factory="Neige",
            geo_factory=lambda _: xr.DataArray(
                [[True, True]], coords={"latitude": [30], "longitude": [40, 41]}
            ),
            levels=levels,
        )

        if has_lpn:
            data = data.copy() | {"LPN__SOL": {}}

        assert_equals_result(
            RiskBuilderFactory(
                parent=composite,
                template_factory="L1\nL2\nL3",
                reducer=RiskReducerFactory(get_critical_values_factory=lambda: data),
            ).compute()
        )


class TestRiskBuilderRain:
    @pytest.mark.parametrize(
        "template_key",
        ["RAS", "low", "low_thunder", "moderate", "moderate_thunder", "high"],
    )
    def test_compute(self, template_key, assert_equals_result):
        builder = RiskBuilderFactory(
            template_name_factory="rain",
            template_key_factory=template_key,
            reduction_factory={"periods": "Période", "localisation": "Localisation"},
        )
        assert_equals_result(
            {language: builder.compute() for language in builder.iter_languages()}
        )
