from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.composite.aggregation import AggregationMethod, AggregationType
from mfire.composite.event import Category, Threshold
from mfire.composite.level import LocalisationConfig
from mfire.composite.operator import ComparisonOperator, LogicalOperator
from mfire.utils.date import Datetime
from tests.composite.factories import (
    AggregationFactory,
    AltitudeCompositeFactory,
    EventAccumulationCompositeFactory,
    EventCompositeFactory,
    FieldCompositeFactory,
    GeoCompositeFactory,
    LevelCompositeFactory,
)
from tests.functions_test import assert_identically_close
from tests.utils.factories import SelectionFactory


class TestLevel:

    def test_events_discrimination(self):
        lvl = LevelCompositeFactory(
            events=[EventCompositeFactory(), EventAccumulationCompositeFactory()]
        )
        lvl = lvl.make_copy()
        assert isinstance(lvl.events[0], EventCompositeFactory)
        assert isinstance(lvl.events[1], EventAccumulationCompositeFactory)

    def test_init_logical_op_list(self):
        assert LevelCompositeFactory(
            events=[EventCompositeFactory(), EventCompositeFactory()],
            logical_op_list=["or"],
        ).logical_op_list == [LogicalOperator("or")]

    def test_check_aggregation(self):
        agg = AggregationFactory()
        lvl = LevelCompositeFactory(
            aggregation_type=AggregationType.UP_STREAM, aggregation=agg
        )
        assert lvl.aggregation is None

        with pytest.raises(
            ValueError, match="Missing expected value 'aggregation' in level"
        ):
            _ = LevelCompositeFactory(
                aggregation_type=AggregationType.DOWN_STREAM, aggregation=None
            )

        lvl = LevelCompositeFactory(
            aggregation_type=AggregationType.DOWN_STREAM, aggregation=agg
        )
        assert lvl.aggregation == agg

    def test_check_nb_elements(self):
        events = [EventCompositeFactory(), EventCompositeFactory()]
        logical_op_list = ["or"]

        lvl = LevelCompositeFactory(events=events, logical_op_list=logical_op_list)
        assert lvl.events == events

        with pytest.raises(
            ValueError,
            match="The number of logical operator is not "
            "consistent with the len of element list. "
            "Should be 1.",
        ):
            _ = LevelCompositeFactory(events=events, logical_op_list=[])

    @pytest.mark.parametrize(
        "lvl1,lvl2,expected",
        [
            # Basic equalities
            (LevelCompositeFactory(), LevelCompositeFactory(), True),
            (
                LevelCompositeFactory(
                    events=[
                        EventCompositeFactory(
                            plain=Threshold(
                                threshold=20, comparison_op=ComparisonOperator.SUP
                            ),
                            mountain=Threshold(
                                threshold=30, comparison_op=ComparisonOperator.SUP
                            ),
                        )
                    ]
                ),
                LevelCompositeFactory(
                    events=[
                        EventCompositeFactory(
                            plain=Threshold(
                                threshold=20, comparison_op=ComparisonOperator.SUP
                            ),
                            mountain=Threshold(
                                threshold=30, comparison_op=ComparisonOperator.SUP
                            ),
                        )
                    ]
                ),
                True,
            ),
            # Not same number of events
            (
                LevelCompositeFactory(events=[EventCompositeFactory()] * 2),
                LevelCompositeFactory(),
                False,
            ),
            # Not same logical operator list
            (
                LevelCompositeFactory(
                    events=[EventCompositeFactory()] * 2, logical_op_list=["or"]
                ),
                LevelCompositeFactory(
                    events=[EventCompositeFactory()] * 2, logical_op_list=["and"]
                ),
                False,
            ),
            # Basic differences
            (
                LevelCompositeFactory(
                    events=[
                        EventCompositeFactory(
                            plain=Threshold(
                                threshold=20, comparison_op=ComparisonOperator.SUP
                            )
                        )
                    ]
                ),
                LevelCompositeFactory(
                    events=[
                        EventCompositeFactory(
                            plain=Threshold(
                                threshold=30, comparison_op=ComparisonOperator.SUP
                            )
                        )
                    ]
                ),
                False,
            ),
            (
                LevelCompositeFactory(
                    events=[
                        EventCompositeFactory(
                            plain=Threshold(
                                threshold=20, comparison_op=ComparisonOperator.SUP
                            ),
                            mountain=Threshold(
                                threshold=20, comparison_op=ComparisonOperator.SUP
                            ),
                        )
                    ]
                ),
                LevelCompositeFactory(
                    events=[
                        EventCompositeFactory(
                            plain=Threshold(
                                threshold=20, comparison_op=ComparisonOperator.SUP
                            ),
                            mountain=Threshold(
                                threshold=30, comparison_op=ComparisonOperator.SUP
                            ),
                        )
                    ]
                ),
                False,
            ),
        ],
    )
    def test_same_than(self, lvl1, lvl2, expected):
        assert lvl1.is_same_than(lvl2) == expected
        assert lvl2.is_same_than(lvl1) == expected

    def test_reset(self):
        values_ds = xr.Dataset({"B": (["A"], [1])}, coords={"A": [2]})
        level = LevelCompositeFactory(
            events=[EventCompositeFactory(), EventCompositeFactory()]
        )
        level.events[0]._values_ds = values_ds
        level.events[1]._values_ds = values_ds
        level = level.reset()
        assert_identically_close(level.events[0]._values_ds, xr.Dataset())
        assert_identically_close(level.events[1]._values_ds, xr.Dataset())

    def test_grid_name(self):
        assert LevelCompositeFactory().grid_name == "franxl1s100"

    def test_geos_file(self):
        assert LevelCompositeFactory().geos_file == Path("geo_composite_file")

    def test_alt_min_and_alt_max(self):
        lvl = LevelCompositeFactory(
            events=[
                EventCompositeFactory(
                    altitude=AltitudeCompositeFactory(alt_min=10, alt_max=200)
                ),
                EventCompositeFactory(
                    altitude=AltitudeCompositeFactory(alt_min=50, alt_max=300)
                ),
            ]
        )

        assert lvl.alt_min == 10
        assert lvl.alt_max == 300

    @patch("mfire.utils.xr.MaskLoader.load")
    def test_geos_descriptive(self, mock_func):
        lvl = LevelCompositeFactory(
            localisation=LocalisationConfig(geos_descriptive=["id_1", "id_2"])
        )
        mock_func.side_effect = lambda *args, **kwargs: (args, kwargs)
        assert lvl.geos_descriptive == ((), {"ids": ["id_1", "id_2"]})

    def test_mask_da(self):
        ids = ["id"]
        lon, lat = [15], [30, 31, 32, 33]
        valid_time = [Datetime(2023, 3, 1).as_np_dt64 for i in range(1, 3)]

        altitude = AltitudeCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[10, np.nan, 20, 30]], coords={"longitude": lon, "latitude": lat}
            )
        )

        geos2_da = xr.DataArray(
            [[[False, True, False, True]]],
            coords={"id": ids, "longitude": lon, "latitude": lat},
        )
        geos1 = GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[[False, True, True, True]]],
                coords={"id": ids, "longitude": lon, "latitude": lat},
            ),
            mask_id=ids,
        )

        field = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                np.random.random((1, 4, 2)),
                coords={"longitude": lon, "latitude": lat, "valid_time": valid_time},
            )
        )

        evt1 = EventCompositeFactory(field=field, geos=geos1, altitude=altitude)
        evt2 = EventCompositeFactory(field=field, geos=geos2_da, altitude=altitude)
        lvl = LevelCompositeFactory(events=[evt1, evt2], logical_op_list=["or"])

        expected = xr.DataArray(
            [[[np.nan, np.nan, 1.0, 1.0]]],
            coords={"id": ids, "longitude": lon, "latitude": lat},
        )
        assert_identically_close(lvl.mask.f32, expected)

    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_cover_period(self, test_file):
        valid_time = [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 4)]
        da = xr.DataArray(
            [1, 2, 3], coords={"valid_time": valid_time}, dims=["valid_time"]
        )
        da.to_netcdf(test_file)

        field_da = FieldCompositeFactory(file=test_file)
        events = [EventCompositeFactory(field=field_da)]
        lvl = LevelCompositeFactory(events=events)

        assert_identically_close(lvl.cover_period, valid_time)

    def test_update_selection(self):
        events = [
            EventCompositeFactory(
                field=FieldCompositeFactory(selection=SelectionFactory())
            ),
            EventAccumulationCompositeFactory(
                field=FieldCompositeFactory(selection=SelectionFactory())
            ),
        ]
        lvl = LevelCompositeFactory(events=events, logical_op_list=["or"])
        new_selection = SelectionFactory()
        lvl.update_selection(
            new_sel=new_selection.sel,
            new_slice=new_selection.slice,
            new_isel=new_selection.isel,
            new_islice=new_selection.islice,
        )
        assert lvl.events[0].field.selection == new_selection
        assert lvl.events[1].field.selection == new_selection

        lvl.update_selection()  # does nothing
        assert lvl.events[0].field.selection == new_selection
        assert lvl.events[1].field.selection == new_selection

    def test_get_single_evt_comparison(self):
        lvl = LevelCompositeFactory(events=[EventCompositeFactory()])

        expected = {
            "plain": Threshold(
                threshold=20, comparison_op=ComparisonOperator.SUPEGAL, units="mm"
            ),
            "category": Category.BOOLEAN,
            "aggregation": AggregationFactory().model_dump(),
        }
        assert lvl.get_single_evt_comparison() == expected

    def test_comparison(self):
        evt1 = EventCompositeFactory(
            field=FieldCompositeFactory(name="field_1"), category=Category.QUANTITATIVE
        )
        evt2 = EventCompositeFactory(
            plain=Threshold(
                threshold=3.1, comparison_op=ComparisonOperator.SUPEGAL, units="cm"
            ),
            mountain=Threshold(
                threshold=2.4, comparison_op=ComparisonOperator.SUP, units="cm"
            ),
            field=FieldCompositeFactory(name="field_2"),
        )
        evt3 = EventCompositeFactory(field=FieldCompositeFactory(name="field_2"))
        lvl = LevelCompositeFactory(
            events=[evt1, evt2, evt3], logical_op_list=["or", "and"]
        )

        expected = {
            "field_1": {
                "plain": Threshold(
                    threshold=20, comparison_op=ComparisonOperator.SUPEGAL, units="mm"
                ),
                "category": Category.QUANTITATIVE,
                "aggregation": AggregationFactory().model_dump(),
            },
            "field_2": {
                "plain": Threshold(
                    threshold=3.1, comparison_op=ComparisonOperator.SUPEGAL, units="cm"
                ),
                "category": Category.BOOLEAN,
                "mountain": Threshold(
                    threshold=2.4, comparison_op=ComparisonOperator.SUP, units="cm"
                ),
                "aggregation": AggregationFactory().model_dump(),
            },
        }
        assert lvl.comparison == expected

    def test_is_accumulation(self):
        lvl = LevelCompositeFactory(
            events=[
                EventAccumulationCompositeFactory(),
                EventAccumulationCompositeFactory(),
            ],
            logical_op_list=["or"],
        )
        assert lvl.is_accumulation is True

        lvl = LevelCompositeFactory(
            events=[EventCompositeFactory(), EventAccumulationCompositeFactory()],
            logical_op_list=["or"],
        )
        assert lvl.is_accumulation is False

    @pytest.mark.parametrize("operator", ["or", "and"])
    def test_compute_upstream(self, operator, assert_equals_result):
        lon, lat = [15], [30, 31, 32, 33]
        valid_time = [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 3)]
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

        field = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [
                    [
                        [
                            [1000, 2000],  # masked values by geos
                            [1500, 3000],  # masked values by altitude
                            [1.7, 1.9],  # isn't risked with threshold and geos
                            [1.8, 1.9],
                        ]
                    ]
                ],
                coords={
                    "id": ids,
                    "longitude": lon,
                    "latitude": lat,
                    "valid_time": valid_time,
                },
                attrs={"units": "cm"},
                name="NEIPOT24__SOL",
            )
        )

        evt1 = EventCompositeFactory(
            field=field,
            geos=geos1,
            altitude=altitude,
            category=Category.QUANTITATIVE,
            plain=Threshold(
                threshold=2.0, comparison_op=ComparisonOperator.SUPEGAL, units="cm"
            ),
        )
        evt2 = EventCompositeFactory(
            field=field,
            geos=geos2,
            altitude=altitude,
            category=Category.QUANTITATIVE,
            plain=Threshold(
                threshold=15, comparison_op=ComparisonOperator.SUPEGAL, units="mm"
            ),
            mountain=Threshold(
                threshold=12, comparison_op=ComparisonOperator.SUPEGAL, units="mm"
            ),
            mountain_altitude=15,
        )

        lvl = LevelCompositeFactory(events=[evt1, evt2], logical_op_list=[operator])

        result = lvl.compute()
        assert_equals_result(
            {
                "result": result.to_dict(),
                "spatial_risk_da": lvl.spatial_risk_da.to_dict(),
            }
        )

    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    @pytest.mark.parametrize(
        "aggregation",
        [
            AggregationFactory(),
            AggregationFactory(method=AggregationMethod.DENSITY),
            AggregationFactory(method=AggregationMethod.MAX),
            AggregationFactory(method=AggregationMethod.RDENSITY, kwargs={"dr": 0.5}),
            AggregationFactory(
                method=AggregationMethod.RDENSITY_WEIGHTED,
                kwargs={"central_mask": ..., "dr": 0.5},
            ),
            AggregationFactory(
                method=AggregationMethod.RDENSITY_CONDITIONAL,
                kwargs={"central_mask": ..., "dr": 0.5},
            ),
        ],
    )
    @pytest.mark.parametrize("operator", ["or", "and"])
    def test_compute_downstream(
        self, aggregation, operator, test_file, assert_equals_result
    ):
        lon, lat = [15], [30, 31, 32, 33]
        valid_time = [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 3)]
        ids = ["id"]

        # Create a central_mask for aggregations RDENSITY_WEIGHTED and
        # RDENSITY_CONDITIONAL
        if "central_mask" in aggregation.kwargs:
            ds = xr.Dataset(
                {
                    "A": (
                        ["id", "longitude_glob05", "latitude_monde"],
                        [[[True, True, False, False]]],
                    )
                },
                coords={"id": ids, "longitude_glob05": lon, "latitude_monde": lat},
            )
            ds.to_netcdf(test_file)
            aggregation.kwargs["central_mask"] = {"file": test_file, "mask_id": ids[0]}

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

        field = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [
                    [
                        [
                            [1000, 2000],  # masked values by geos
                            [1500, 3000],  # masked values by altitude
                            [1.7, 1.9],  # isn't risked with threshold and geos
                            [1.8, 1.9],
                        ]
                    ]
                ],
                coords={
                    "id": ids,
                    "longitude": lon,
                    "latitude": lat,
                    "valid_time": valid_time,
                },
                attrs={"units": "cm", "PROMETHEE_z_ref": "A"},
                name="NEIPOT24__SOL",
            )
        )

        lvl = LevelCompositeFactory(
            aggregation=aggregation,
            aggregation_type=AggregationType.DOWN_STREAM,
            events=[
                EventCompositeFactory(
                    field=field,
                    geos=geos1,
                    altitude=altitude,
                    category=Category.QUANTITATIVE,
                    plain=Threshold(
                        threshold=2.0,
                        comparison_op=ComparisonOperator.SUPEGAL,
                        units="cm",
                    ),
                ),
                EventCompositeFactory(
                    field=field,
                    geos=geos2,
                    altitude=altitude,
                    category=Category.QUANTITATIVE,
                    plain=Threshold(
                        threshold=15,
                        comparison_op=ComparisonOperator.SUPEGAL,
                        units="mm",
                    ),
                ),
            ],
            logical_op_list=[operator],
        )

        assert_equals_result(
            {
                "result": lvl.compute().to_dict(),
                "spatial_risk_da": lvl.spatial_risk_da.to_dict(),
            }
        )

    def test_multiply_all_dr_by(self):
        # Test with level and events aggregation
        lvl = LevelCompositeFactory(
            aggregation=AggregationFactory(
                method=AggregationMethod.RDENSITY, kwargs={"dr": 0.5}
            ),
            aggregation_type=AggregationType.DOWN_STREAM,
            events=[
                EventCompositeFactory(
                    aggregation=AggregationFactory(
                        method=AggregationMethod.RDENSITY, kwargs={"dr": 0.2}
                    )
                ),
                EventCompositeFactory(
                    aggregation=AggregationFactory(
                        method=AggregationMethod.RDENSITY, kwargs={"dr": 0.9}
                    )
                ),
            ],
        )

        new_lvl = lvl.multiply_all_dr_by(0.1)
        assert_identically_close(new_lvl.aggregation.kwargs["dr"], 0.05)
        assert_identically_close(new_lvl.events[0].aggregation.kwargs["dr"], 0.02)
        assert_identically_close(new_lvl.events[1].aggregation.kwargs["dr"], 0.09)

        # Test only with level aggregation
        lvl = LevelCompositeFactory(
            aggregation=AggregationFactory(
                method=AggregationMethod.RDENSITY, kwargs={"dr": 0.5}
            ),
            aggregation_type=AggregationType.DOWN_STREAM,
            events=[EventCompositeFactory(aggregation=None)],
        )
        new_lvl = lvl.multiply_all_dr_by(0.1)
        assert_identically_close(new_lvl.aggregation.kwargs["dr"], 0.05)
        assert new_lvl.events[0].aggregation is None

        # Test only with event aggregation
        lvl = LevelCompositeFactory(
            events=[
                EventCompositeFactory(
                    aggregation=AggregationFactory(
                        method=AggregationMethod.RDENSITY, kwargs={"dr": 0.5}
                    )
                )
            ]
        )
        new_lvl = lvl.multiply_all_dr_by(0.1)
        assert new_lvl.aggregation is None
        assert_identically_close(new_lvl.events[0].aggregation.kwargs["dr"], 0.05)
