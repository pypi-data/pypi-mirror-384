from pathlib import Path

import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.composite.aggregation import AggregationMethod, AggregationType
from mfire.composite.component import (
    RiskComponentComposite,
    SynthesisComponentComposite,
)
from mfire.composite.event import Category, Threshold
from mfire.composite.level import LocalisationConfig
from mfire.composite.operator import ComparisonOperator, LogicalOperator
from mfire.composite.period import PeriodComposite
from mfire.utils.date import Datetime
from mfire.utils.json import JsonFile
from mfire.utils.period import Period, PeriodDescriber
from tests.composite.factories import (
    AggregationFactory,
    AltitudeCompositeFactory,
    EventCompositeFactory,
    FieldCompositeFactory,
    GeoCompositeFactory,
    LevelCompositeFactory,
    PeriodCompositeFactory,
    RiskComponentCompositeFactory,
    SynthesisComponentCompositeFactory,
    SynthesisModuleFactory,
)
from tests.functions_test import assert_identically_close

# COMPONENTS


class TestAbstractComponentComposite:
    @pytest.mark.parametrize(
        "component_class",
        [SynthesisComponentCompositeFactory, RiskComponentCompositeFactory],
    )
    def test_reset(self, component_class):
        component = component_class(data=2)
        component.reset()
        assert component.data is None

    @pytest.mark.parametrize(
        "component_class",
        [SynthesisComponentCompositeFactory, RiskComponentCompositeFactory],
    )
    def test_init_dates(self, component_class):
        component = component_class(
            production_datetime="2023-03-01", configuration_datetime="2023-03-02"
        )
        assert component.production_datetime == Datetime(2023, 3, 1)
        assert component.configuration_datetime == Datetime(2023, 3, 2)

    @pytest.mark.parametrize(
        "component_class",
        [SynthesisComponentCompositeFactory, RiskComponentCompositeFactory],
    )
    def test_period_describer(self, component_class):
        component = component_class(
            period=PeriodCompositeFactory(
                start=Datetime(2023, 3, 1, 1), stop=Datetime(2023, 3, 1, 12)
            ),
            production_datetime=Datetime(2023, 3, 1),
        )
        assert component.period_describer == PeriodDescriber(
            cover_period=Period(
                begin_time=Datetime(2023, 3, 1, 1), end_time=Datetime(2023, 3, 1, 12)
            ),
            request_time=Datetime(2023, 3, 1),
            parent=component,
        )


class TestRiskComponentComposite:
    inputs_dir: Path = Path(__file__).parent / "inputs"

    def test_is_risks_empty(self):
        risk_compo = RiskComponentCompositeFactory()
        assert risk_compo.is_risks_empty is True

        risk_compo = RiskComponentCompositeFactory(
            data=xr.Dataset({"A": ("B", [1])}, coords={"B": [2]})
        )
        assert risk_compo.is_risks_empty is False

    def test_levels_of_risk(self):
        risk_compo = RiskComponentCompositeFactory(
            levels=[LevelCompositeFactory(level=1)] * 3
            + [LevelCompositeFactory(level=2)] * 5
        )
        assert len(risk_compo.levels_of_risk(1)) == 3
        assert len(risk_compo.levels_of_risk(2)) == 5
        assert len(risk_compo.levels_of_risk(3)) == 0

    def test_final_risk_max_level(self):
        # Empty risk
        risk_compo = RiskComponentCompositeFactory()
        assert risk_compo.final_risk_max_level(geo_id="id") == 0

        # Non-empty risk
        risk_compo = RiskComponentCompositeFactory(
            data=xr.Dataset({"A": ("B", [...])}, coords={"B": [...]}),
            final_risk_da_factory=xr.DataArray(
                [[1, 2], [4, 5]], coords={"id": ["id_1", "id_2"], "A": [..., ...]}
            ),
        )
        assert risk_compo.final_risk_max_level(geo_id="id_1") == 2
        assert risk_compo.final_risk_max_level(geo_id="id_2") == 5
        assert risk_compo.final_risk_max_level() == 5

    def test_alt_area_name(self):
        # Empty risk
        risk_compo = RiskComponentCompositeFactory()
        assert risk_compo.area_name(geo_id="id") == "N.A"

        # Non-empty risk
        risk_compo = RiskComponentCompositeFactory(
            data=xr.Dataset(
                {"altAreaName": (["id"], ["area1", "area2"])},
                coords={"id": ["id1", "id2"]},
            )
        )
        assert risk_compo.alt_area_name(geo_id="id1") == "area1"
        assert risk_compo.alt_area_name(geo_id="id2") == "area2"

    def test_area_name(self):
        # Empty risk
        risk_compo = RiskComponentCompositeFactory()
        assert risk_compo.area_name(geo_id="id") == "N.A"

        # Non-empty risk
        risk_compo = RiskComponentCompositeFactory(
            data=xr.Dataset(
                {"areaName": (["id"], ["area1", "area2"])},
                coords={"id": ["id1", "id2"]},
            )
        )
        assert risk_compo.area_name(geo_id="id1") == "area1"
        assert risk_compo.area_name(geo_id="id2") == "area2"

    def test_get_comparison(self):
        levels = [
            LevelCompositeFactory(
                level=1,
                events=[
                    EventCompositeFactory(
                        plain=Threshold(
                            threshold=13,
                            comparison_op=ComparisonOperator.SUP,
                            units="mm",
                        ),
                        mountain=Threshold(
                            threshold=13,
                            comparison_op=ComparisonOperator.INF,
                            units="mm",
                        ),
                    )
                ],
            ),
            LevelCompositeFactory(
                level=2,
                events=[
                    EventCompositeFactory(
                        plain=Threshold(
                            threshold=1.5,
                            comparison_op=ComparisonOperator.SUP,
                            units="cm",
                        ),
                        mountain=Threshold(
                            threshold=1.0,
                            comparison_op=ComparisonOperator.INF,
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
                            threshold=20,
                            comparison_op=ComparisonOperator.SUPEGAL,
                            units="mm",
                        ),
                        mountain=Threshold(
                            threshold=0.5,
                            comparison_op=ComparisonOperator.INFEGAL,
                            units="cm",
                        ),
                    )
                ],
            ),
        ]

        risk_compo = RiskComponentCompositeFactory(levels=levels)
        assert risk_compo.get_comparison(1) == {
            "field_name": {
                "plain": Threshold(
                    threshold=13,
                    comparison_op=ComparisonOperator.SUP,
                    units="mm",
                    next_critical=15.0,
                ),
                "category": Category.BOOLEAN,
                "mountain": Threshold(
                    threshold=13,
                    comparison_op=ComparisonOperator.INF,
                    units="mm",
                    next_critical=10.0,
                ),
                "aggregation": {"kwargs": {}, "method": AggregationMethod.MEAN},
            }
        }
        assert risk_compo.get_comparison(2) == {
            "field_name": {
                "plain": Threshold(
                    threshold=1.5,
                    comparison_op=ComparisonOperator.SUP,
                    units="cm",
                    next_critical=2.0,
                ),
                "category": Category.BOOLEAN,
                "mountain": Threshold(
                    threshold=1,
                    comparison_op=ComparisonOperator.INF,
                    units="cm",
                    next_critical=0.5,
                ),
                "aggregation": {"kwargs": {}, "method": AggregationMethod.MEAN},
            }
        }
        assert risk_compo.get_comparison(3) == {
            "field_name": {
                "plain": Threshold(
                    threshold=20, comparison_op=ComparisonOperator.SUPEGAL, units="mm"
                ),
                "category": Category.BOOLEAN,
                "mountain": Threshold(
                    threshold=0.5, comparison_op=ComparisonOperator.INFEGAL, units="cm"
                ),
                "aggregation": {"kwargs": {}, "method": AggregationMethod.MEAN},
            }
        }

    @pytest.mark.parametrize(
        "axis,expected",
        [
            (0, [5.0, 1.0, 4.0]),
            (1, [2.0, 4.0, 4.0]),
            ((0,), [5.0, 1.0, 4.0]),
            ((1,), [2.0, 4.0, 4.0]),
        ],
    )
    def test_replace_middle(self, axis, expected):
        x = np.array([[2.0, 1.0, 2.0], [5.0, 1.0, 4.0], [4.0, 4.0, 1.0]])
        result = RiskComponentComposite._replace_middle(x, axis=axis)
        assert_identically_close(result, np.array(expected))

    def test_special_merge(self):
        d1 = xr.Dataset(
            {
                "summarized_density": (["valid_time", "risk_level"], [[0.1, 0.2]]),
                "risk_summarized_density": (["valid_time", "risk_level"], [[0.1, 0.2]]),
                "occurrence": (["valid_time", "risk_level"], [[False, True]]),
                "occurrence_event": (["valid_time", "risk_level"], [[False, True]]),
                "occurrence_plain": (["valid_time", "risk_level"], [[False, True]]),
                "occurrence_mountain": (["valid_time", "risk_level"], [[False, True]]),
            },
            coords={
                "risk_level": [1, 2],
                "valid_time": [
                    np.datetime64("2024-02-01T00:00:00").astype("datetime64[ns]")
                ],
            },
        )
        d2 = xr.Dataset(
            {
                "summarized_density": (
                    ["valid_time", "risk_level"],
                    [[0.2, 0.1], [0.4, 0.3]],
                ),
                "risk_summarized_density": (
                    ["valid_time", "risk_level"],
                    [[0.2, 0.1], [0.4, 0.3]],
                ),
                "occurrence": (
                    ["valid_time", "risk_level"],
                    [[True, False], [True, False]],
                ),
                "occurrence_event": (
                    ["valid_time", "risk_level"],
                    [[True, False], [False, True]],
                ),
                "occurrence_plain": (
                    ["valid_time", "risk_level"],
                    [[True, False], [False, True]],
                ),
                "occurrence_mountain": (
                    ["valid_time", "risk_level"],
                    [[True, False], [False, True]],
                ),
            },
            coords={
                "risk_level": [1, 2],
                "valid_time": [
                    np.datetime64("2024-02-01T00:00:00").astype("datetime64[ns]"),
                    np.datetime64("2024-02-02T04:00:00").astype("datetime64[ns]"),
                ],
            },
        )

        result = RiskComponentComposite._special_merge(d1, d2)

        assert_identically_close(
            result,
            xr.Dataset(
                {
                    "summarized_density": (
                        ["valid_time", "risk_level"],
                        [[0.2, 0.2], [0.4, 0.3]],
                    ),
                    "risk_summarized_density": (
                        ["valid_time", "risk_level"],
                        [[0.2, 0.2], [0.4, 0.3]],
                    ),
                    "occurrence": (
                        ["valid_time", "risk_level"],
                        [[True, True], [True, False]],
                    ),
                    "occurrence_event": (
                        ["valid_time", "risk_level"],
                        [[True, True], [False, True]],
                    ),
                    "occurrence_plain": (
                        ["valid_time", "risk_level"],
                        [[True, True], [False, True]],
                    ),
                    "occurrence_mountain": (
                        ["valid_time", "risk_level"],
                        [[True, True], [False, True]],
                    ),
                },
                coords={
                    "risk_level": [1, 2],
                    "valid_time": [
                        np.datetime64("2024-02-01T00:00:00").astype("datetime64[ns]"),
                        np.datetime64("2024-02-02T04:00:00").astype("datetime64[ns]"),
                    ],
                },
            ),
        )

    def test_compute(self, assert_equals_result):
        lon, lat = [15], [30, 31, 32, 33]
        ids = ["id"]

        altitude = AltitudeCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[10, np.nan, 20, 30]], coords={"longitude": lon, "latitude": lat}
            )
        )
        geos1 = GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[[False, True, True, True]]],
                coords={"id": ids, "longitude": lon, "latitude": lat},
            ),
            mask_id=ids,
        )
        geos2 = GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[[False, True, False, True]]],
                coords={"id": ids, "longitude": lon, "latitude": lat},
            ),
            mask_id=ids,
        )

        field1 = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [
                    [
                        [1000, 2000],  # masked values by geos
                        [1500, 3000],  # masked values by altitude
                        [1.7, 1.9],  # isn't risked with threshold and geos
                        [1.8, 1.9],
                    ]
                ],
                coords={
                    "longitude": lon,
                    "latitude": lat,
                    "valid_time": [
                        Datetime(2023, 3, i).as_np_dt64 for i in range(1, 3)
                    ],
                },
                attrs={"units": "cm"},
                name="NEIPOT24__SOL",
            )
        )
        field2 = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [
                    [
                        [1500],  # masked values by geos
                        [2000],  # masked values by altitude
                        [1.6],  # isn't risked with threshold
                        [1.9],
                    ]
                ],
                coords={
                    "longitude": lon,
                    "latitude": lat,
                    "valid_time": [Datetime(2023, 3, 3).as_np_dt64],
                },
                attrs={"units": "cm"},
                name="NEIPOT1__SOL",
            )
        )
        evt1 = EventCompositeFactory(
            field=field1,
            geos=geos1,
            altitude=altitude,
            category=Category.QUANTITATIVE,
            plain=Threshold(
                threshold=2.0, comparison_op=ComparisonOperator.SUPEGAL, units="cm"
            ),
        )
        evt2 = EventCompositeFactory(
            field=field1,
            geos=geos2,
            altitude=altitude,
            category=Category.QUANTITATIVE,
            plain=Threshold(
                threshold=15, comparison_op=ComparisonOperator.SUPEGAL, units="mm"
            ),
        )
        evt3 = EventCompositeFactory(
            field=field2,
            geos=geos2,
            altitude=altitude,
            category=Category.QUANTITATIVE,
            plain=Threshold(
                threshold=2.0, comparison_op=ComparisonOperator.SUPEGAL, units="cm"
            ),
            mountain=Threshold(
                threshold=12, comparison_op=ComparisonOperator.SUPEGAL, units="mm"
            ),
            mountain_altitude=15,
        )

        risk_compo = RiskComponentCompositeFactory(
            levels=[
                LevelCompositeFactory(
                    level=1,
                    events=[evt1, evt2],
                    logical_op_list=[LogicalOperator.OR],
                    aggregation_type=AggregationType.DOWN_STREAM,
                    aggregation=AggregationFactory(),
                ),
                LevelCompositeFactory(
                    level=2,
                    events=[evt1, evt2],
                    logical_op_list=[LogicalOperator.AND],
                    aggregation_type=AggregationType.DOWN_STREAM,
                    aggregation=AggregationFactory(),
                ),
                LevelCompositeFactory(
                    level=3,
                    events=[evt3],
                    aggregation_type=AggregationType.DOWN_STREAM,
                    aggregation=AggregationFactory(),
                ),
            ]
        )

        risk_compo.compute()
        assert_equals_result(
            {
                "risk_ds": risk_compo.risk_ds.to_dict(),
                "final_risk_da": risk_compo.final_risk_da.to_dict(),
            }
        )

    def test_integration(self, assert_equals_result, root_path_cwd):
        data = JsonFile(self.inputs_dir / "small_conf_risk.json").load()
        data_prod = next(iter(data.values()))
        component = data_prod["components"][0]
        compo = RiskComponentComposite(**component)

        assert_equals_result(compo)

    @pytest.mark.parametrize(
        "final_risk_da,expected",
        [
            # No information about fog
            (None, None),
            (
                xr.DataArray(
                    [[1]], coords={"valid_time": [Datetime(2023, 3, 1)], "id": ["id3"]}
                ),
                None,
            ),
            (
                xr.DataArray(
                    [[1]], coords={"valid_time": [Datetime(2023, 2, 1)], "id": ["id1"]}
                ),
                None,
            ),
            # Mist without occurrence
            (
                xr.DataArray(
                    [[0]], coords={"valid_time": [Datetime(2023, 3, 1)], "id": ["id1"]}
                ),
                False,
            ),
            # Mist with occurrence
            (
                xr.DataArray(
                    [[1, 0]],
                    coords={"valid_time": [Datetime(2023, 3, 1)], "id": ["id1", "id2"]},
                ),
                True,
            ),
            (
                xr.DataArray(
                    [[0, 1]],
                    coords={"valid_time": [Datetime(2023, 3, 1)], "id": ["id1", "id2"]},
                ),
                True,
            ),
        ],
    )
    def test_has_risk(self, final_risk_da, expected):
        assert (
            RiskComponentCompositeFactory(final_risk_da_factory=final_risk_da).has_risk(
                ids=["id1", "id2"],
                valid_time=slice(Datetime(2023, 3, 1), Datetime(2023, 3, 1, 2)),
            )
            == expected
        )

    @pytest.mark.parametrize(
        "field,ids,expected",
        [
            ("F1", ["id1"], True),
            ("F2", ["id2"], True),
            ("F2", ["id1", "id2"], True),
            ("F1", ["id2"], False),
        ],
    )
    def test_has_field(self, field, ids, expected):
        level = LevelCompositeFactory(
            events=[
                EventCompositeFactory(
                    field=FieldCompositeFactory(name="F1"), geos_id_factory=["id1"]
                ),
                EventCompositeFactory(
                    field=FieldCompositeFactory(name="F2"), geos_id_factory=["id2"]
                ),
            ]
        )
        compo = RiskComponentCompositeFactory(levels=[level])
        assert compo.has_field(field, ids) == expected

    @pytest.mark.parametrize(
        "gd_1, gd_2, field_name, geo_id, data_types",
        [
            # geo_1 mask: [False, True, True, True]
            # geo_2 mask: [True, True, True, True]
            # altitude mask: [10, 30, 550, 600]
            # Field 1 on geo_1 with plain threshold 60 km/h
            # Field 2 on geo_2 with plain threshold 80 km/h, mountain threshold 100 km/h
            # and mountain_altitude as 500 m
            (
                [[np.nan], [59.3], [49.5], [42.1]],
                None,
                "RAF__HAUTEUR10",
                "id1",
                ["min", "max"],
            ),
            (
                [[np.nan], [65.3], [65.3], [65.3]],
                None,
                "RAF__HAUTEUR10",
                "id1",
                ["min", "max"],
            ),
            (
                [[np.nan], [65.3], [60.1], [63.6]],
                None,
                "RAF__HAUTEUR10",
                "id1",
                ["min", "max"],
            ),
            (None, [[40], [42], [62], [75]], "RAF__HAUTEUR10", "id2", ["min", "max"]),
            (None, [[81], [81], [62], [75]], "RAF__HAUTEUR10", "id2", ["min", "max"]),
            (None, [[81], [89], [62], [75]], "RAF__HAUTEUR10", "id2", ["min", "max"]),
            (None, [[40], [42], [110], [89]], "RAF__HAUTEUR10", "id2", ["min", "max"]),
            (None, [[40], [42], [110], [120]], "RAF__HAUTEUR10", "id2", ["min", "max"]),
            (None, [[81], [89], [110], [120]], "RAF__HAUTEUR10", "id2", ["min", "max"]),
            (
                [[np.nan], [120], [59], [59]],
                [[85], [85], [110], [110]],
                "RAF__HAUTEUR10",
                "id2",
                ["min", "max"],
            ),
            (
                [[np.nan], [120], [59], [59]],
                [[85], [85], [90], [90]],
                "RAF__HAUTEUR10",
                "id2",
                ["min", "max"],
            ),
            (
                [[np.nan], [74], [59], [59]],
                [[85], [75], [40], [110]],
                "RAF__HAUTEUR10",
                "id1",
                ["min", "max"],
            ),
            (
                [[np.nan], [np.nan], [np.nan], [np.nan]],
                None,
                "RAF__HAUTEUR10",
                "id1",
                ["min", "max"],
            ),
            (
                [[71], [74], [59], [59]],
                [[85], [75], [40], [110]],
                "NEIPOT1__SOL",
                "id1",
                ["min", "max"],
            ),
            (
                [[71], [74], [59], [59]],
                None,
                "RAF__HAUTEUR10",
                "not_found_id",
                ["min", "max"],
            ),
            (
                [[np.nan], [np.nan], [np.nan], [np.nan]],
                None,
                "RAF__HAUTEUR10",
                "id1",
                ["min", "max"],
            ),
        ],
    )
    def test_get_risk_infos(
        self, gd_1, gd_2, field_name, geo_id, data_types, assert_equals_result
    ):
        # gd_1 and gd_2 are gust data of FieldComposite field_1 and field_2.
        lon, lat = [15], [30, 31, 32, 33]
        ids = ["id1", "id2"]
        valid_time: np.datetime64 = Datetime(2023, 3, 3).as_np_dt64

        altitude = AltitudeCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[10, 30, 550, 600]], coords={"longitude": lon, "latitude": lat}
            )
        )
        geos_1 = GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[[False, True, True, True]]],
                coords={"id": ["id1"], "longitude": lon, "latitude": lat},
            ),
            mask_id=ids,
        )
        geos_2 = GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[[True, True, True, True]]],
                coords={"id": ["id2"], "longitude": lon, "latitude": lat},
            ),
            mask_id=ids,
        )

        levels = []

        if gd_1 is not None:
            field_1 = FieldCompositeFactory(
                compute_factory=lambda: xr.DataArray(
                    [gd_1],
                    coords={
                        "longitude": lon,
                        "latitude": lat,
                        "valid_time": [valid_time],
                    },
                    attrs={"units": "km/h"},
                    name="RAF__HAUTEUR10",
                ),
                name="RAF__HAUTEUR10",
            )
            evt_1 = EventCompositeFactory(
                field=field_1,
                geos=geos_1,
                altitude=altitude,
                category=Category.QUANTITATIVE,
                plain=Threshold(
                    threshold=60.0,
                    comparison_op=ComparisonOperator.SUPEGAL,
                    units="km/h",
                ),
            )
            lvl_1 = LevelCompositeFactory(
                level=1,
                events=[evt_1],
                aggregation_type=AggregationType.DOWN_STREAM,
                aggregation=AggregationFactory(),
            )
            levels.append(lvl_1)

        if gd_2 is not None:
            field_2 = FieldCompositeFactory(
                compute_factory=lambda: xr.DataArray(
                    [gd_2],
                    coords={
                        "longitude": lon,
                        "latitude": lat,
                        "valid_time": [valid_time],
                    },
                    attrs={"units": "km/h"},
                    name="RAF__HAUTEUR10",
                ),
                name="RAF__HAUTEUR10",
            )

            evt_2 = EventCompositeFactory(
                field=field_2,
                geos=geos_2,
                altitude=altitude,
                category=Category.QUANTITATIVE,
                plain=Threshold(
                    threshold=80.0,
                    comparison_op=ComparisonOperator.SUPEGAL,
                    units="km/h",
                ),
                mountain=Threshold(
                    threshold=100.0,
                    comparison_op=ComparisonOperator.SUPEGAL,
                    units="km/h",
                ),
                mountain_altitude=500,
            )

            lvl_2 = LevelCompositeFactory(
                level=2,
                events=[evt_2],
                aggregation_type=AggregationType.DOWN_STREAM,
                aggregation=AggregationFactory(),
            )
            levels.append(lvl_2)

        risk_compo = RiskComponentCompositeFactory(levels=levels)

        risk_compo.compute()

        res: dict = {
            "input": {
                "gd_1": gd_1,
                "gd_2": gd_2,
                "field_name": field_name,
                "geo_id": geo_id,
                "data_types": data_types,
            },
            "output": risk_compo.get_risk_infos(
                field_name, geo_id, slice(valid_time), data_types
            ),
        }

        assert_equals_result(res)

    def test_geo(self):
        risk = RiskComponentCompositeFactory(
            levels=[
                LevelCompositeFactory(
                    events=[
                        EventCompositeFactory(
                            geos=xr.DataArray(coords={"id": ["id1"]}, dims=["id"])
                        )
                    ]
                ),
                LevelCompositeFactory(
                    events=[
                        EventCompositeFactory(
                            geos=xr.DataArray(
                                coords={"id": ["id1", "id2"]}, dims=["id"]
                            )
                        )
                    ]
                ),
            ]
        )
        assert risk.geo("id1").id == "id1"
        assert risk.geo("id2").id == "id2"
        assert risk.geo("id3") is None

    @pytest.mark.parametrize(
        "final_risk_max_level,same_level,risk_ds,expected",
        [
            # Max level cases
            (
                2,
                True,
                xr.Dataset(
                    {
                        "threshold_dr": (["risk_level"], [0.4]),
                        "risk_density": (["id", "risk_level", "valid_time"], [[[0.5]]]),
                    },
                    coords={
                        "id": ["geo_id"],
                        "risk_level": [2],
                        "valid_time": [Datetime(2023, 3, 1)],
                    },
                ),
                25,
            ),  # downstream case
            (
                2,
                True,
                xr.Dataset(
                    {
                        "threshold_dr": (["risk_level"], [0.0]),
                        "risk_density": (["id", "risk_level", "valid_time"], [[[0.5]]]),
                    },
                    coords={
                        "id": ["geo_id"],
                        "risk_level": [2],
                        "valid_time": [Datetime(2023, 3, 1)],
                    },
                ),
                50,
            ),  # downstream case with DR0
            (
                2,
                True,
                xr.Dataset(
                    {
                        "threshold_dr": (["evt", "risk_level"], [[0.4]]),
                        "density": (
                            ["evt", "id", "risk_level", "valid_time"],
                            [[[[0.5]]]],
                        ),
                    },
                    coords={
                        "id": ["geo_id"],
                        "risk_level": [2],
                        "evt": [0],
                        "valid_time": [Datetime(2023, 3, 1)],
                    },
                ),
                25,
            ),  # upstream case
            # Level 0 cases
            (
                0,
                True,
                xr.Dataset(
                    {
                        "threshold_dr": (["risk_level"], [0.0]),
                        "risk_density": (["id", "risk_level", "valid_time"], [[[0.0]]]),
                    },
                    coords={
                        "id": ["geo_id"],
                        "risk_level": [2],
                        "valid_time": [Datetime(2023, 3, 1)],
                    },
                ),
                0,
            ),  # next threshold is null with downstream case
            (
                0,
                True,
                xr.Dataset(
                    {
                        "threshold_dr": (["risk_level", "evt"], [[0.0]]),
                        "density": (
                            ["id", "risk_level", "evt", "valid_time"],
                            [[[[0.0]]]],
                        ),
                    },
                    coords={
                        "id": ["geo_id"],
                        "risk_level": [2],
                        "evt": [0],
                        "valid_time": [Datetime(2023, 3, 1)],
                    },
                ),
                0,
            ),  # next threshold is null with upstream case
            (
                0,
                True,
                xr.Dataset(
                    {
                        "threshold_dr": (["risk_level"], [0.8]),
                        "risk_density": (["id", "risk_level", "valid_time"], [[[0.5]]]),
                    },
                    coords={
                        "id": ["geo_id"],
                        "risk_level": [2],
                        "valid_time": [Datetime(2023, 3, 1)],
                    },
                ),
                62,
            ),  # next threshold is not null
            # Required density is different those of the next level
            (
                1,
                True,
                xr.Dataset(
                    {
                        "threshold_dr": (["risk_level"], [0.0, 0.4]),
                        "risk_density": (
                            ["valid_time", "id", "risk_level"],
                            [[[0.15, 0.15]]],
                        ),
                    },
                    coords={
                        "id": ["geo_id"],
                        "risk_level": [1, 2],
                        "valid_time": [Datetime(2023, 3, 1)],
                    },
                ),
                37,
            ),  # same levels
            (
                1,
                False,
                xr.Dataset(
                    {
                        "threshold_dr": (["risk_level"], [0.0, 0.4]),
                        "rep_value_plain": (["id", "risk_level"], [[70.0, np.nan]]),
                        "threshold_plain": (["risk_level"], [30.0, 80.0]),
                        "density": (["id"], [0.0]),
                    },
                    coords={"id": ["geo_id"], "risk_level": [1, 2]},
                ),
                80,
            ),  # different levels
            # Representative value is compared to the threshold of the next level
            (
                1,
                True,
                xr.Dataset(
                    {
                        "threshold_dr": (["risk_level"], [0.0, 0.0]),
                        "rep_value_plain": (["id", "risk_level"], [[70.0, np.nan]]),
                        "threshold_plain": (["risk_level"], [30.0, 80.0]),
                        "density": (["id"], [0.0]),
                    },
                    coords={"id": ["geo_id"], "risk_level": [1, 2]},
                ),
                80,
            ),  # Normal case
            (
                1,
                True,
                xr.Dataset(
                    {
                        "threshold_dr": (["risk_level"], [0.0, 0.0]),
                        "rep_value_plain": (["id", "risk_level"], [[70.0, np.nan]]),
                        "threshold_plain": (["risk_level"], [30.0, 80.0]),
                        "rep_value_mountain": (["id", "risk_level"], [[90.0, np.nan]]),
                        "threshold_mountain": (["risk_level"], [60.0, 100.0]),
                        "density": (["id"], [0.0]),
                    },
                    coords={"id": ["geo_id"], "risk_level": [1, 2]},
                ),
                77,
            ),  # plain and mountain VR
            (
                1,
                True,
                xr.Dataset(
                    {
                        "threshold_dr": (["risk_level"], [0.0, 0.0]),
                        "rep_value_plain": (["id", "risk_level"], [[-4.0, np.nan]]),
                        "threshold_plain": (["risk_level"], [0.0, -5.0]),
                        "density": (["id"], [0.0]),
                    },
                    coords={"id": ["geo_id"], "risk_level": [1, 2]},
                ),
                80,
            ),  # Reversed case (like cold risk)
            # Representative values does not reach the threshold of the current level
            (
                1,
                True,
                xr.Dataset(
                    {
                        "threshold_dr": (["risk_level"], [0.0, 0.0]),
                        "rep_value_mountain": (["id", "risk_level"], [[9.0, np.nan]]),
                        "threshold_mountain": (["risk_level"], [10.0, 20.0]),
                        "density": (["id"], [0.0]),
                    },
                    coords={"id": ["geo_id"], "risk_level": [1, 2]},
                ),
                0,
            ),
        ],
    )
    def test_percent_uncertainty(
        self, final_risk_max_level, same_level, risk_ds, expected
    ):
        assert_identically_close(
            RiskComponentCompositeFactory(
                final_risk_max_level_factory=lambda _: final_risk_max_level,
                risk_ds_factory=risk_ds,
                levels=[
                    LevelCompositeFactory(
                        level=1,
                        events=[
                            EventCompositeFactory(
                                plain=Threshold(
                                    threshold=20, comparison_op=ComparisonOperator.SUP
                                )
                            )
                        ],
                    ),
                    LevelCompositeFactory(
                        level=2,
                        events=[
                            EventCompositeFactory(
                                plain=Threshold(
                                    threshold=20 if same_level else 30,
                                    comparison_op=ComparisonOperator.SUP,
                                )
                            )
                        ],
                    ),
                ],
            ).percent_uncertainty("geo_id"),
            expected,
        )

    @pytest.mark.parametrize(
        "level,risk_levels,percent,expected",
        [
            # All risk levels
            (0, [1, 2, 3], np.nan, 0),
            (0, [1, 2, 3], None, 0),
            (0, [1, 2, 3], 0, 11),
            (0, [1, 2, 3], 10, 11),
            (0, [1, 2, 3], 50, 12),
            (0, [1, 2, 3], 90, 13),
            (0, [1, 2, 3], 100, 13),
            (1, [1, 2, 3], np.nan, 0),
            (1, [1, 2, 3], None, 0),
            (1, [1, 2, 3], 0, 21),
            (1, [1, 2, 3], 25, 21),
            (1, [1, 2, 3], 34, 22),
            (1, [1, 2, 3], 67, 23),
            (1, [1, 2, 3], 100, 23),
            (2, [1, 2, 3], np.nan, 0),
            (2, [1, 2, 3], None, 0),
            (2, [1, 2, 3], 0, 21),
            (2, [1, 2, 3], 1, 21),
            (2, [1, 2, 3], 40, 22),
            (2, [1, 2, 3], 80, 23),
            (2, [1, 2, 3], 100, 23),
            (3, [1, 2, 3], np.nan, 0),
            (3, [1, 2, 3], None, 0),
            (3, [1, 2, 3], 0, 31),
            (3, [1, 2, 3], 15, 31),
            (3, [1, 2, 3], 65, 32),
            (3, [1, 2, 3], 88, 33),
            (3, [1, 2, 3], 100, 33),
            # Not all risk levels
            (1, [1], 25, 31),
            (2, [1, 2], 34, 32),
        ],
    )
    def test_code_uncertainty(self, level, risk_levels, percent, expected):
        component = RiskComponentCompositeFactory(
            final_risk_max_level_factory=lambda x: level if x == "geo_id" else None,
            percent_uncertainty_factory=lambda x: (
                percent if x == "geo_id" else "bad value"
            ),
            risk_ds_factory=xr.Dataset(None, coords={"risk_level": risk_levels}),
        )

        with pytest.raises(TypeError):
            component.code_uncertainty("bad_geo_id")

        assert component.code_uncertainty("geo_id") == expected


class TestSynthesisComponentComposite:
    inputs_dir: Path = Path(__file__).parent / "inputs"

    def test_init_weather_component(self):
        composite = SynthesisModuleFactory(parent=None)
        assert composite.parent is None

        component = SynthesisComponentCompositeFactory(weathers=[composite])
        assert component.weathers[0].parent is not None

    def test_weather_period(self):
        compo = SynthesisComponentCompositeFactory()
        assert compo.weather_period == PeriodComposite(
            id="period_id", start=Datetime(2023, 3, 1), stop=Datetime(2023, 3, 5)
        )

    def test_alt_area_name(self):
        ds = xr.Dataset(
            {"altAreaName": (["id"], ["area1", "area2"]), "id": ["id1", "id2"]}
        )
        text_compo = SynthesisComponentCompositeFactory(compute_factory=lambda: ds)

        assert text_compo.alt_area_name("id1") == "area1"
        assert text_compo.alt_area_name("id2") == "area2"

    def test_area_name(self):
        ds = xr.Dataset(
            {"areaName": (["id"], ["area1", "area2"]), "id": ["id1", "id2"]}
        )
        text_compo = SynthesisComponentCompositeFactory(compute_factory=lambda: ds)

        assert text_compo.area_name("id1") == "area1"
        assert text_compo.area_name("id2") == "area2"

    def test_compute(self, assert_equals_result):
        lon, lat = [35], [40, 41, 42]
        ids = ["id"]

        # First weather component
        field1 = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[1.0, 2.0, 3.0]], coords={"longitude": lon, "latitude": lat}
            ),
            name="T__HAUTEUR2",
        )
        geos1 = GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[[True, False, False]]],
                coords={"id": ids, "longitude": lon, "latitude": lat},
            ),
            mask_id=ids,
        )

        weather_compo1 = SynthesisModuleFactory(
            id="tempe", params={"tempe": field1}, geos=geos1
        )

        # Second weather component
        field2 = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[4.0, 5.0, 6.0]], coords={"longitude": lon, "latitude": lat}
            ),
            name="T__SOL",
        )
        geos2 = GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[[False, True, False]]],
                coords={"id": ids, "longitude": lon, "latitude": lat},
            ),
            mask_id=ids,
        )

        weather_compo2 = SynthesisModuleFactory(
            id="tempe", params={"tempe": field2}, geos=geos2
        )

        # Text Component
        component = SynthesisComponentCompositeFactory(
            geos=["id"], weathers=[weather_compo1, weather_compo2]
        )
        assert_equals_result(component.compute().to_dict())

    def test_integration(self, assert_equals_result, root_path_cwd):
        data = JsonFile(self.inputs_dir / "small_conf_text.json").load()
        data_prod = next(iter(data.values()))
        component = data_prod["components"][0]
        compo = SynthesisComponentComposite(**component)

        assert_equals_result(compo)


# COMPONENT MODULES


class TestSynthesisModule:
    def test_wrong_field(self):
        with pytest.raises(
            ValueError,
            match="Wrong field: [], expected ['wwmf', 'precip', 'rain', 'snow', "
            "'lpn']",
        ):
            SynthesisModuleFactory(id="weather", params={})

    def test_check_condition_without_condition(self):
        weather_compo = SynthesisModuleFactory()
        assert weather_compo.check_condition("geo_id") is True

    def test_check_condition(self):
        assert SynthesisModuleFactory().check_condition("...") is True

        synthesis_compo = SynthesisModuleFactory(
            condition=EventCompositeFactory(
                compute_factory=lambda: xr.DataArray([False, True]),
                geos=GeoCompositeFactory(mask_id=None),
            )
        )
        assert synthesis_compo.check_condition("geo_id") is True
        assert synthesis_compo.condition.geos.mask_id == "geo_id"

        assert (
            SynthesisModuleFactory(
                condition=EventCompositeFactory(
                    compute_factory=lambda: xr.DataArray([False, False])
                )
            ).check_condition("...")
            is False
        )

    def test_altitude(self):
        weather_compo = SynthesisModuleFactory(
            id="tempe", params={"tempe": FieldCompositeFactory(grid_name="franxl1s100")}
        )

        assert weather_compo.altitude("weather") is None

        alt = weather_compo.altitude("tempe")
        assert isinstance(alt, xr.DataArray)
        assert alt.name == "franxl1s100"

    def test_geos_data(self):
        geos = GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [1, 2], coords={"id": ["id_1", "id_2"]}
            ),
            mask_id=["id_1", "id_2"],
        )
        weather_compo = SynthesisModuleFactory(geos=geos)
        assert_identically_close(
            weather_compo.geos_data(),
            xr.DataArray([1, 2], coords={"id": ["id_1", "id_2"]}),
        )
        assert_identically_close(
            weather_compo.geos_data(geo_id="id_1"),
            xr.DataArray(1, coords={"id": "id_1"}),
        )

    def test_weather_data(self, assert_equals_result):
        lon, lat = [35], [40, 41, 42]
        ids = ["id1", "id2"]

        field = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[1.0, 2.0, 3.0]], coords={"longitude": lon, "latitude": lat}
            )
        )
        geos = GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[[True, False, True]], [[False, True, False]]],
                coords={"id": ids, "longitude": lon, "latitude": lat},
            ),
            mask_id=ids,
        )

        module = SynthesisModuleFactory(id="tempe", params={"tempe": field}, geos=geos)
        assert_equals_result(
            {
                "id1": module.weather_data("id1").to_dict(),
                "id2": module.weather_data("id2").to_dict(),
                "all": module.weather_data().to_dict(),
            }
        )

    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_geos_descriptive(self, test_file):
        lon, lat = [31], [40]
        ids = ["id_axis", "id_1", "id_2", "id_axis_altitude", "id_axis_compass"]
        ds = xr.Dataset(
            {
                "A": (
                    ["longitude", "latitude", "id"],
                    [[[True, True, False, True, False]]],
                )
            },
            coords={
                "id": ids,
                "longitude": lon,
                "latitude": lat,
                "areaType": (
                    ["id"],
                    ["Axis", "areaType1", "areaType2", "Altitude", "compass"],
                ),
            },
        )
        ds.to_netcdf(test_file)

        weather_compo = SynthesisModuleFactory(
            geos=GeoCompositeFactory(file=test_file, grid_name="A"),
            localisation=LocalisationConfig(
                geos_descriptive=["id_1", "id_2"],
                compass_split=True,
                altitude_split=True,
            ),
        )
        assert_identically_close(
            weather_compo.geos_descriptive("id_axis"),
            xr.DataArray(
                [[[1.0, 1.0, np.nan, 1.0, np.nan]]],
                coords={
                    "id": [
                        "id_axis",
                        "id_1",
                        "id_2",
                        "id_axis_altitude",
                        "id_axis_compass",
                    ],
                    "longitude": lon,
                    "latitude": lat,
                    "areaName": (
                        ["id"],
                        ["unknown", "unknown", "unknown", "unknown", "unknown"],
                    ),
                    "altAreaName": (
                        ["id"],
                        ["unknown", "unknown", "unknown", "unknown", "unknown"],
                    ),
                    "areaType": (
                        ["id"],
                        ["Axis", "areaType1", "areaType2", "Altitude", "compass"],
                    ),
                },
                dims=["longitude", "latitude", "id"],
                name="A",
            ),
        )

        weather_compo.localisation.compass_split = False
        weather_compo.localisation.altitude_split = False
        assert_identically_close(
            weather_compo.geos_descriptive("id_axis"),
            xr.DataArray(
                [[[1.0, 1.0, np.nan]]],
                coords={
                    "id": ["id_axis", "id_1", "id_2"],
                    "longitude": lon,
                    "latitude": lat,
                    "areaName": (["id"], ["unknown", "unknown", "unknown"]),
                    "altAreaName": (["id"], ["unknown", "unknown", "unknown"]),
                    "areaType": (["id"], ["Axis", "areaType1", "areaType2"]),
                },
                dims=["longitude", "latitude", "id"],
                name="A",
            ),
        )
