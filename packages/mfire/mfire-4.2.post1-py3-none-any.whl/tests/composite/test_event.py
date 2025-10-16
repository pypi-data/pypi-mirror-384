from datetime import datetime
from math import isclose
from pathlib import Path

import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.composite.aggregation import Aggregation, AggregationMethod
from mfire.composite.event import Category, Threshold
from mfire.composite.operator import ComparisonOperator
from mfire.utils.calc import compute_accumulation
from mfire.utils.date import Datetime
from tests.composite.factories import (
    AggregationFactory,
    AltitudeCompositeFactory,
    EventAccumulationCompositeFactory,
    EventCompositeFactory,
    FieldCompositeFactory,
    GeoCompositeFactory,
)
from tests.functions_test import assert_identically_close
from tests.utils.factories import SelectionFactory


class TestThreshold:
    def test_init_comparison_op(self):
        assert (
            Threshold(threshold=0.5, comparison_op="egal").comparison_op
            == ComparisonOperator.EGAL
        )

    @pytest.mark.parametrize(
        "t1,t2,expected",
        [
            # Not same operator
            (
                {"threshold": 0.5, "comparison_op": "egal"},
                {"threshold": 0.5, "comparison_op": "isin"},
                False,
            ),
            # Not same units
            (
                {"threshold": 0.5, "units": "cm", "comparison_op": "egal"},
                {"threshold": 0.5, "units": "m", "comparison_op": "egal"},
                False,
            ),
            # Not same next_critical
            (
                {"threshold": 0.5, "next_critical": 0.1, "comparison_op": "egal"},
                {"threshold": 0.5, "next_critical": 0.2, "comparison_op": "egal"},
                False,
            ),
            # Not same threshold
            (
                {"threshold": 0.5, "comparison_op": "egal"},
                {"threshold": 0.4, "comparison_op": "egal"},
                False,
            ),
            (
                {"threshold": "s1", "comparison_op": "egal"},
                {"threshold": "s2", "comparison_op": "egal"},
                False,
            ),
            (
                {"threshold": [0.5, 0.5], "comparison_op": "egal"},
                {"threshold": [0.5, 0.4], "comparison_op": "egal"},
                False,
            ),
            (
                {"threshold": ["s1", "s1"], "comparison_op": "egal"},
                {"threshold": ["s1", "s2"], "comparison_op": "egal"},
                False,
            ),
            # Same values
            (
                {"threshold": 0.5, "comparison_op": "egal"},
                {"threshold": 0.5, "comparison_op": "egal"},
                True,
            ),
            (
                {"threshold": "s1", "comparison_op": "egal"},
                {"threshold": "s1", "comparison_op": "egal"},
                True,
            ),
            (
                {"threshold": [0.5, 0.5], "comparison_op": "egal"},
                {
                    "threshold": [0.5000000000001, 0.5000000000002],
                    "comparison_op": "egal",
                },
                True,
            ),
            (
                {"threshold": ["s1", "s1"], "comparison_op": "egal"},
                {"threshold": ["s1", "s1"], "comparison_op": "egal"},
                True,
            ),
            # Not same length
            (
                {"threshold": [0.5, 0.5, 0.5], "comparison_op": "egal"},
                {"threshold": [0.5, 0.5], "comparison_op": "egal"},
                False,
            ),
        ],
    )
    def test_eq(self, t1, t2, expected):
        assert (Threshold(**t1) == Threshold(**t2)) == expected

    @pytest.mark.parametrize(
        "threshold,expected",
        [
            (
                {"threshold": 0.5, "comparison_op": "egal"},
                Threshold(threshold=0.5, comparison_op=ComparisonOperator.EGAL),
            ),
            (
                {"threshold": [0.2, 0.5], "comparison_op": "supegal"},
                Threshold(
                    threshold=[0.2, 0.5], comparison_op=ComparisonOperator.SUPEGAL
                ),
            ),
            (
                {"threshold": [0.2], "comparison_op": "egal"},
                Threshold(threshold=0.2, comparison_op=ComparisonOperator.EGAL),
            ),
            (
                {"threshold": [0.2], "comparison_op": "dif"},
                Threshold(threshold=0.2, comparison_op=ComparisonOperator.DIF),
            ),
            (
                {"threshold": [0.2, 0.5], "comparison_op": "egal"},
                Threshold(threshold=[0.2, 0.5], comparison_op=ComparisonOperator.ISIN),
            ),
            (
                {"threshold": [0.2, 0.5], "comparison_op": "dif"},
                Threshold(
                    threshold=[0.2, 0.5], comparison_op=ComparisonOperator.NOT_ISIN
                ),
            ),
        ],
    )
    def test_check_comparison_op_and_value(self, threshold, expected):
        assert Threshold(**threshold) == expected

    def test_from_configuration(self):
        assert Threshold.from_configuration(
            {"threshold": 8, "comparisonOp": "sup", "units": "m"}
        ) == Threshold(threshold=8, comparison_op="sup", units="m")

    @pytest.mark.parametrize(
        "threshold,context,expected",
        [
            ({"threshold": 1, "units": None}, None, {"threshold": 1, "units": None}),
            ({"threshold": 1, "units": 1}, None, {"threshold": 1, "units": 1}),
            ({"threshold": 1, "units": "km"}, None, {"threshold": 1000, "units": "m"}),
            (
                {"threshold": 1, "units": "km", "next_critical": 2},
                None,
                {"threshold": 1000, "units": "m", "next_critical": 2000},
            ),
            (
                {"threshold": 1, "units": "kg m**-2 s**-1"},
                "precipitation",
                {"threshold": 0.001, "units": "m"},
            ),
            (
                {"threshold": 1, "units": "kg m**-2 s**-1"},
                "snow",
                {"threshold": 0.01, "units": "m"},
            ),
        ],
    )
    def test_change_units(self, threshold, context, expected):
        thr = Threshold(**threshold, comparison_op="supegal")
        result = thr.change_units("m", context=context)
        assert result == Threshold(**expected, comparison_op="supegal")

    @pytest.mark.parametrize(
        "value,expected",
        [
            (1, 1),
            (1.2, 1.2),
            (1.0, 1),
            (True, True),
            ([1, 1.2, 1.0, False], [1, 1.2, 1, False]),
        ],
    )
    def test_validate_threshold(self, value, expected):
        assert Threshold.validate_threshold(value) == expected

    @pytest.mark.parametrize(
        "t1,expected",
        [
            # Second threshold is weaker
            ({"threshold": 4.0, "units": "cm"}, {"threshold": 4.0, "units": "cm"}),
            # Second threshold is strong and no next_critical
            (
                {"threshold": 2.0, "units": "cm"},
                {"threshold": 2.0, "units": "cm", "next_critical": 3.0},
            ),
            # Second threshold is strong and with next_critical
            (
                {"threshold": 2.0, "units": "cm", "next_critical": 2.5},
                {"threshold": 2.0, "units": "cm", "next_critical": 3.0},
            ),
            (
                {"threshold": 2.0, "units": "cm", "next_critical": 5.0},
                {"threshold": 2.0, "units": "cm", "next_critical": 5.0},
            ),
            # With different units
            ({"threshold": 40, "units": "mm"}, {"threshold": 40, "units": "mm"}),
            (
                {"threshold": 20, "units": "mm"},
                {"threshold": 20, "units": "mm", "next_critical": 30},
            ),
            (
                {"threshold": 20, "units": "mm", "next_critical": 25},
                {"threshold": 20, "units": "mm", "next_critical": 30},
            ),
        ],
    )
    def test_update_next_critical(self, t1, expected):
        t1 = Threshold(comparison_op="sup", **t1)
        t2 = Threshold(comparison_op="sup", threshold=3.0, units="cm")
        t1.update_next_critical(t2)
        assert t1 == Threshold(comparison_op="sup", **expected)


class TestEventComposite:
    inputs_dir: Path = Path(__file__).parent / "inputs"

    def test_reset(self):
        event = EventCompositeFactory()
        event._values_ds = xr.Dataset({"B": (["A"], [1])}, coords={"A": [2]})
        event = event.reset()
        assert_identically_close(event._values_ds, xr.Dataset())

    def test_check_plain_or_mountain(self):
        with pytest.raises(ValueError, match="Either plain or mountain is required"):
            _ = EventCompositeFactory(plain=None, mountain=None)

        thr = Threshold(threshold=0.5, comparison_op="sup")

        evt = EventCompositeFactory(plain=thr, mountain=None)
        assert evt.plain == thr
        assert evt.mountain is None

        evt = EventCompositeFactory(plain=None, mountain=thr)
        assert evt.mountain is not None and evt.mountain == thr
        assert evt.plain is None

    def test_geos_da(self):
        da = xr.DataArray([1, 2, 3])
        event = EventCompositeFactory(geos=da)
        assert_identically_close(event.geos_da, da)

        event = EventCompositeFactory(
            geos=GeoCompositeFactory(compute_factory=lambda: da)
        )
        assert_identically_close(event.geos_da, da)

    def test_geos_id(self):
        ids = ["id1", "id2", "id3"]
        da = xr.DataArray([1, 2, 3], coords={"id": ids})

        event = EventCompositeFactory(geos=da)
        assert event.geos_id == ids

        event = EventCompositeFactory(geos=GeoCompositeFactory(mask_id=None))
        assert event.geos_id == []

        event = EventCompositeFactory(geos=GeoCompositeFactory(mask_id=ids))
        assert event.geos_id == ids

        event = EventCompositeFactory(geos=GeoCompositeFactory(mask_id="mask_id"))
        assert event.geos_id == ["mask_id"]

    @pytest.mark.parametrize(
        "event,expected",
        [
            ({"aggregation": None}, False),
            ({"aggregation": Aggregation(method=AggregationMethod.RDENSITY)}, False),
            ({"aggregation": Aggregation(method=AggregationMethod.MEAN)}, True),
        ],
    )
    def test_is_pre_aggregation(self, event, expected):
        evt = EventCompositeFactory(**event)
        assert evt.is_pre_aggregation == expected

    @pytest.mark.parametrize(
        "event,expected",
        [
            ({"aggregation": None}, False),
            ({"aggregation": Aggregation(method=AggregationMethod.RDENSITY)}, True),
            ({"aggregation": Aggregation(method=AggregationMethod.MEAN)}, False),
        ],
    )
    def test_is_post_aggregation(self, event, expected):
        evt = EventCompositeFactory(**event)
        assert evt.is_post_aggregation == expected

    def test_mask(self):
        ids = ["id"]
        lon, lat = [15], [30, 31, 32, 33]
        valid_time = [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 5)]

        geos_da = xr.DataArray(
            [[[False, True, True, True]]],
            coords={"id": ids, "longitude": lon, "latitude": lat},
        )

        field = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [
                    [
                        [1000, 2000, 1500, 2500],  # will be masked by geos
                        [10, 0.5, 2.2, 2.1],  # will be masked by altitude
                        [0.3, 1.5, 2.5, 2.4],
                        [0.9, 1.2, 1.3, 1.5],
                    ]
                ],
                coords={"longitude": lon, "latitude": lat, "valid_time": valid_time},
            )
        )
        altitude = AltitudeCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[10, np.nan, 20, 0]], coords={"longitude": lon, "latitude": lat}
            )
        )
        geos = GeoCompositeFactory(compute_factory=lambda: geos_da, mask_id=ids)

        expected = xr.DataArray(
            [[[np.nan, np.nan, 1.0, 1.0]]],
            coords={"id": ids, "longitude": lon, "latitude": lat},
        )

        # Test with GeoComposite
        event = EventCompositeFactory(field=field, geos=geos, altitude=altitude)
        assert_identically_close(event.mask.f32, expected)

        # Test with xr.DataArray
        event = EventCompositeFactory(field=field, geos=geos_da, altitude=altitude)
        assert_identically_close(event.mask.f32, expected)

    def test_field_da(self):
        lon, lat = [15], [30]
        valid_time = [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 5)]
        coords = {"longitude": lon, "latitude": lat, "valid_time": valid_time}

        field_da = xr.DataArray([[[0.3, 1.5, 2.5, 2.4]]], coords=coords)

        event = EventCompositeFactory(
            field=FieldCompositeFactory(compute_factory=lambda: field_da)
        )
        assert_identically_close(event.field_da, field_da)

    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_cover_period(self, test_file):
        valid_time = [Datetime(2023, 3, 1, i).as_np_dt64 for i in range(3)]
        da = xr.DataArray([1, 2, 3], coords={"valid_time": valid_time})
        da.to_netcdf(test_file)

        field_da = FieldCompositeFactory(file=test_file)
        event = EventCompositeFactory(field=field_da)
        assert_identically_close(event.cover_period, valid_time)

    @pytest.mark.parametrize(
        "event,expected",
        [
            (
                {},
                {
                    "plain": Threshold(
                        threshold=20, comparison_op="supegal", units="mm"
                    ),
                    "category": Category.BOOLEAN,
                    "aggregation": {"method": AggregationMethod.MEAN, "kwargs": {}},
                },
            ),
            (
                {
                    "mountain": {
                        "threshold": 10,
                        "comparison_op": "supegal",
                        "units": "mm",
                    },
                    "mountain_altitude": 400,
                },
                {
                    "plain": Threshold(
                        threshold=20, comparison_op="supegal", units="mm"
                    ),
                    "mountain": Threshold(
                        threshold=10, comparison_op="supegal", units="mm"
                    ),
                    "mountain_altitude": 400,
                    "category": Category.BOOLEAN,
                    "aggregation": {"method": AggregationMethod.MEAN, "kwargs": {}},
                },
            ),
            (
                {"aggregation": AggregationFactory()},
                {
                    "plain": Threshold(
                        threshold=20, comparison_op="supegal", units="mm"
                    ),
                    "category": Category.BOOLEAN,
                    "aggregation": {"method": AggregationMethod.MEAN, "kwargs": {}},
                },
            ),
        ],
    )
    def test_comparison(self, event, expected):
        evt = EventCompositeFactory(**event)
        assert evt.comparison == expected

    def test_get_risk(self):
        lon, lat = [30], [40, 41]
        valid_time = [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 5)]
        coords = {"longitude": lon, "latitude": lat, "valid_time": valid_time}
        threshold = Threshold(threshold=1, comparison_op="supegal")
        field_da = xr.DataArray(
            [[[0.5, 3, 0, np.nan], [np.nan, 0.75, 2, 3]]],
            coords=coords,
            name="NEIPOT24__SOL",
        )
        result = EventCompositeFactory().get_risk(field_da, threshold)

        assert_identically_close(
            result,
            xr.DataArray(
                [[[0.0, 1.0, 0.0, np.nan], [np.nan, 0.0, 1.0, 1.0]]],
                coords,
                name="NEIPOT24__SOL",
            ),
        )

    @pytest.mark.parametrize(
        "field_name,event,threshold,expected",
        [
            # Not quantitative category
            (
                "FF__HAUTEUR10",
                {"category": Category.BOOLEAN},
                {"threshold": 0.5, "comparison_op": "supegal", "units": "cm"},
                None,
            ),
            (
                "FF__HAUTEUR10",
                {"category": Category.CATEGORICAL},
                {"threshold": 0.5, "comparison_op": "supegal", "units": "cm"},
                None,
            ),
            # no aggregations
            (
                "FF__HAUTEUR10",
                {"category": Category.QUANTITATIVE, "aggregation": None},
                {"threshold": 0.5, "comparison_op": "supegal", "units": "cm"},
                0.9,
            ),
            # Basic aggregations
            (
                "FF__HAUTEUR10",
                {
                    "category": Category.QUANTITATIVE,
                    "aggregation": Aggregation(method=AggregationMethod.RDENSITY),
                },
                {"threshold": 0.5, "comparison_op": "supegal", "units": "cm"},
                0.9,
            ),
            (
                "FF__HAUTEUR10",
                {
                    "category": Category.QUANTITATIVE,
                    "aggregation": Aggregation(method=AggregationMethod.RDENSITY),
                },
                {"threshold": 0.6, "comparison_op": "infegal", "units": "cm"},
                0.1,
            ),
            (
                "FF__HAUTEUR10",
                {
                    "category": Category.QUANTITATIVE,
                    "aggregation": Aggregation(method=AggregationMethod.MEAN),
                },
                {"threshold": 0.5, "comparison_op": "supegal", "units": "cm"},
                0.5,
            ),
            # Test when the value is over the threshold
            (
                "FF__HAUTEUR10",
                {"category": Category.QUANTITATIVE, "aggregation": None},
                {"threshold": 0.6, "comparison_op": "supegal", "units": "cm"},
                0.9,
            ),
            (
                "FF__HAUTEUR10",
                {"category": Category.QUANTITATIVE, "aggregation": None},
                {"threshold": 0.4, "comparison_op": "inf", "units": "cm"},
                0.1,
            ),
            # different unit
            (
                "FF__HAUTEUR10",
                {
                    "category": Category.QUANTITATIVE,
                    "aggregation": Aggregation(method=AggregationMethod.RDENSITY),
                },
                {"threshold": 5, "comparison_op": "supegal", "units": "mm"},
                9.0,
            ),
            (
                "FF__HAUTEUR10",
                {"category": Category.QUANTITATIVE, "aggregation": None},
                {"threshold": 6, "comparison_op": "supegal", "units": "mm"},
                9.0,
            ),
            # precipitation
            (
                "PRECIP__SOL",
                {
                    "category": Category.QUANTITATIVE,
                    "aggregation": Aggregation(method=AggregationMethod.RDENSITY),
                },
                {"threshold": 0.5, "comparison_op": "supegal", "units": "mm"},
                7.5,
            ),
            (
                "EAU1__SOL",
                {
                    "category": Category.QUANTITATIVE,
                    "aggregation": Aggregation(method=AggregationMethod.RDENSITY),
                },
                {"threshold": 0.5, "comparison_op": "supegal", "units": "mm"},
                7.5,
            ),
            # snow
            (
                "NEIPOT24__SOL",
                {
                    "category": Category.QUANTITATIVE,
                    "aggregation": Aggregation(method=AggregationMethod.RDENSITY),
                },
                {"threshold": 0.5, "comparison_op": "supegal", "units": "mm"},
                5.0,
            ),
        ],
    )
    def test_get_representative_value(self, field_name, event, threshold, expected):
        evt = EventCompositeFactory(**event)
        threshold = Threshold(**threshold)

        lat, lon = [1], range(14, 25)
        field = xr.DataArray(
            [[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]],
            coords={"latitude": lat, "longitude": lon},
            attrs={"units": "cm"},
            name=field_name,
        )
        if expected is not None:
            expected = xr.DataArray(
                expected, name=field_name, attrs={"units": threshold.units}
            )
        assert_identically_close(
            evt.get_representative_values(field, threshold=threshold), expected
        )

    @pytest.mark.parametrize("method", [AggregationMethod.ALL, AggregationMethod.ANY])
    def test_get_representative_value_with_bad_agg_method(self, method):
        evt = EventCompositeFactory(
            category=Category.QUANTITATIVE, aggregation=Aggregation(method=method)
        )
        threshold = Threshold(threshold=0.1, comparison_op="supegal", units="cm")
        with pytest.raises(ValueError):
            evt.get_representative_values(
                xr.DataArray(name="NEIPOT24__SOL"), threshold=threshold
            )

    def test_get_representative_value_with_bad_comparison_op(self):
        evt = EventCompositeFactory(
            category=Category.QUANTITATIVE,
            aggregation=Aggregation(method=AggregationMethod.RDENSITY),
        )
        threshold = Threshold(threshold=0.1, comparison_op="egal", units="cm")
        with pytest.raises(ValueError):
            evt.get_representative_values(
                xr.DataArray(name="EAU1__SOL"), threshold=threshold
            )

    @pytest.mark.parametrize(
        "event,original_unit,expected",
        [
            ({"category": Category.BOOLEAN}, "cm", (None, None)),
            ({"category": Category.CATEGORICAL}, "cm", (None, None)),
            ({"category": Category.QUANTITATIVE}, "cm", (0.1, 1.0)),
            ({"category": Category.RESTRICTED_QUANTITATIVE}, "cm", (0.1, 1.0)),
            (
                {"category": Category.QUANTITATIVE},
                "mm",
                (1, 10),
            ),  # different original unit
        ],
    )
    def test_get_extreme_values(self, event, original_unit, expected):
        evt = EventCompositeFactory(**event)

        lat, lon = [1], range(15, 25)
        masked_field = xr.DataArray(
            [[0.1, 0.2, 0.8, 0.3, 0.7, 0.4, 1.0, 0.5, 0.6, 0.9]],
            coords={"latitude": lat, "longitude": lon},
            attrs={"units": "cm"},
        )
        assert evt.get_extreme_values(masked_field, original_unit) == expected

    def test_compute_density(self):
        evt = EventCompositeFactory()

        lat, lon = [1], [10, 11, 12, 13]
        valid_time = [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 3)]
        risk_field = xr.DataArray(
            [[[0.7, 0.8], [0.2, 0.4], [0.2, 0.6], [np.nan, np.nan]]],
            coords={"latitude": lat, "longitude": lon, "valid_time": valid_time},
            attrs={"units": "cm"},
        )
        assert np.allclose(
            evt.compute_density(risk_field), [1.1 / 3, 1.8 / 3]
        )  # sum of all values divided by the count

    def test_compute_summarized_density(self):
        evt = EventCompositeFactory()

        lat, lon = [1], [10, 11, 12, 13]
        valid_time = [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 4)]
        risk_field = xr.DataArray(
            [
                [
                    [10, 15, 16],
                    [0.2, 0.1, 0.4],
                    [0.3, 0.1, 0.2],
                    [np.nan, np.nan, np.nan],
                ]
            ],
            coords={"latitude": lat, "longitude": lon, "valid_time": valid_time},
            attrs={"units": "cm"},
        )
        mask = xr.DataArray(
            [[False, True, True, False]],
            coords={"latitude": lat, "longitude": lon},
            attrs={"units": "cm"},
        )
        assert isclose(
            evt.compute_summarized_density(risk_field, mask), (0.4 + 0.3) / 3
        )  # sum of all non-masked values divided by the count

    def test_update_selection(self):
        field = FieldCompositeFactory(selection=SelectionFactory())
        event = EventCompositeFactory(field=field)
        new_selection = SelectionFactory()
        event.update_selection(
            new_sel=new_selection.sel,
            new_slice=new_selection.slice,
            new_isel=new_selection.isel,
            new_islice=new_selection.islice,
        )
        assert event.field.selection == new_selection

    @pytest.mark.parametrize(
        "event",
        [
            # Plain case
            {"aggregation": None},
            {
                "aggregation": None,
                "plain": {"threshold": 50, "comparison_op": "supegal", "units": "mm"},
                "category": Category.QUANTITATIVE,
            },
            # Mountain case
            {
                "aggregation": None,
                "plain": {"threshold": 75.0, "comparison_op": "supegal", "units": "mm"},
                "mountain": {
                    "threshold": 45.0,
                    "comparison_op": "supegal",
                    "units": "mm",
                },
                "mountain_altitude": 125,
                "category": Category.BOOLEAN,
            },
            {
                "aggregation": None,
                "plain": {"threshold": 5.1, "comparison_op": "supegal", "units": "cm"},
                "mountain": {
                    "threshold": 40,
                    "comparison_op": "supegal",
                    "units": "mm",
                },
                "mountain_altitude": 80,
                "category": Category.RESTRICTED_QUANTITATIVE,
            },
            # Only plain case (i.e. with mountain_altitude and no mountain)
            {
                "aggregation": None,
                "plain": {"threshold": 50, "comparison_op": "supegal", "units": "mm"},
                "mountain": None,
                "mountain_altitude": 20,
                "category": Category.QUANTITATIVE,
            },
            # Only mountain case (i.e. with mountain_altitude and no plain)
            {
                "aggregation": None,
                "plain": None,
                "mountain": {
                    "threshold": 50,
                    "comparison_op": "supegal",
                    "units": "mm",
                },
                "mountain_altitude": 20,
                "category": Category.QUANTITATIVE,
            },
            # Test of aggregated values
            {
                "aggregation": Aggregation(method=AggregationMethod.MEAN),
                "category": Category.QUANTITATIVE,
            },
            {
                "aggregation": Aggregation(method=AggregationMethod.MEDIAN),
                "category": Category.QUANTITATIVE,
            },
            {
                "aggregation": Aggregation(method=AggregationMethod.MIN),
                "category": Category.QUANTITATIVE,
            },
            {
                "aggregation": Aggregation(method=AggregationMethod.MAX),
                "category": Category.QUANTITATIVE,
            },
            {
                "aggregation": Aggregation(method=AggregationMethod.SUM),
                "category": Category.QUANTITATIVE,
            },
            {
                "aggregation": Aggregation(method=AggregationMethod.STD),
                "category": Category.QUANTITATIVE,
            },
            {
                "aggregation": Aggregation(method=AggregationMethod.VAR),
                "category": Category.QUANTITATIVE,
            },
            {
                "aggregation": Aggregation(method=AggregationMethod.QUANTILE),
                "category": Category.QUANTITATIVE,
            },
            {
                "aggregation": Aggregation(method=AggregationMethod.MEAN),
                "category": Category.QUANTITATIVE,
                "plain": {"threshold": 42, "comparison_op": "supegal", "units": "mm"},
                "mountain": {
                    "threshold": 45,
                    "comparison_op": "supegal",
                    "units": "mm",
                },
                "mountain_altitude": 125,
            },
            # Test of non-aggregated values (drr)
            {"aggregation": Aggregation(method=AggregationMethod.RDENSITY)},
            {
                "aggregation": Aggregation(method=AggregationMethod.RDENSITY),
                "plain": {"threshold": 55, "comparison_op": "supegal", "units": "mm"},
                "mountain": {
                    "threshold": 60,
                    "comparison_op": "supegal",
                    "units": "mm",
                },
                "mountain_altitude": 125,
            },
        ],
    )
    def test_compute_plain_and_mountain(self, event, assert_equals_result):
        lon, lat = [15], [30, 31, 32, 33, 34, 35]
        valid_time = [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 5)]

        field_da = xr.DataArray(
            [
                [
                    # Last valid time isn't risked
                    [0.5, 0.6, 1.2, 0.0],  # altitude and not risked values
                    [10.0, 10.2, 10.3, 10.1],  # altitude and risked values
                    [0.5, 2.2, 2.0, 1.0],  # not risked values
                    [9.9, 10.5, 10.4, 20.0],  # risked values
                    [200.0, 30.0, 30.0, 40.0],  # masked values
                    [np.nan, np.nan, np.nan, np.nan],
                ]
            ],
            coords={"longitude": lon, "latitude": lat, "valid_time": valid_time},
            name="FF__HAUTEUR",
            attrs={"units": "cm"},
        )
        altitude_da = xr.DataArray(
            [[1000, 1500, 0, 10, 20, 30]], coords={"longitude": lon, "latitude": lat}
        )

        evt = EventCompositeFactory(
            **event,
            field=FieldCompositeFactory(compute_factory=lambda: field_da),
            altitude=AltitudeCompositeFactory(compute_factory=lambda: altitude_da),
            mask_factory=xr.DataArray(
                [[True, True, True, True, False, True]],
                coords={"longitude": lon, "latitude": lat},
            ).mask
        )

        plain, mountain = evt.compute_plain_and_mountain()
        if plain is not None:
            plain = plain.to_dict()
        if mountain is not None:
            mountain = mountain.to_dict()
        assert_equals_result(
            {"plain": plain, "mountain": mountain, "values_ds": evt.values_ds.to_dict()}
        )

    @pytest.mark.parametrize(
        "event",
        [
            {"aggregation": None},
            {"aggregation": Aggregation(method=AggregationMethod.MEAN)},
            {"aggregation": Aggregation(method=AggregationMethod.RDENSITY)},
        ],
    )
    def test_compute_post_aggregation(self, event, assert_equals_result):
        lon, lat = [15], [30, 31, 32]
        valid_time = [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 4)]
        coords = {"longitude": lon, "latitude": lat, "valid_time": valid_time}

        field = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(None, name="NEIPOT24__SOL")
        )
        evt = EventCompositeFactory(**event, field=field)
        plain_da = xr.DataArray(
            [[[0.0, 1.0, 1.0], [np.nan, np.nan, np.nan], [np.nan, np.nan, np.nan]]],
            coords=coords,
        )
        mountain_da = xr.DataArray(
            [[[np.nan, np.nan, np.nan], [1.0, 0.0, 1.0], [np.nan, np.nan, np.nan]]],
            coords=coords,
        )

        result = evt.compute_post_aggregation(plain_da, mountain_da)
        assert_equals_result(
            {"result": result.to_dict(), "values_ds": evt.values_ds.to_dict()}
        )

    @pytest.mark.parametrize(
        "aggregation",
        [
            None,
            Aggregation(method=AggregationMethod.MEAN),
            Aggregation(method=AggregationMethod.RDENSITY),
        ],
    )
    def test_compute(self, aggregation, assert_equals_result):
        ids = ["id"]
        lon, lat = [15], [30, 31, 32, 33, 34, 35, 36]
        valid_time = [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 3)]

        field = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [
                    [
                        [1000, 2000],  # masked by geos
                        [10, 0.5],  # masked by altitude
                        [3.1, 3.2],  # plain with risk
                        [2.1, 2.2],  # plain without risk
                        [2.1, 2.2],  # mountain with risk
                        [1.9, 1.8],  # mountain without risk
                        [np.nan, np.nan],  # nan values
                    ]
                ],
                coords={"longitude": lon, "latitude": lat, "valid_time": valid_time},
                name="NEIPOT24__SOL",
                attrs={"units": "cm"},
            )
        )
        altitude = AltitudeCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[10, np.nan, 20, 10, 500, 400, 30]],
                coords={"longitude": lon, "latitude": lat},
            )
        )
        geos = GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[[False, True, True, True, True, True, True]]],
                coords={"id": ids, "longitude": lon, "latitude": lat},
            ),
            mask_id=ids,
        )

        evt = EventCompositeFactory(
            plain=Threshold(threshold=30, comparison_op="supegal", units="mm"),
            mountain=Threshold(threshold=20, comparison_op="supegal", units="mm"),
            aggregation=aggregation,
            category=Category.QUANTITATIVE,
            mountain_altitude=100,
            field=field,
            geos=geos,
            altitude=altitude,
        )
        assert_equals_result(
            {"result": evt.compute().to_dict(), "values_ds": evt.values_ds.to_dict()}
        )


class TestEventAccumulationComposite:
    @pytest.mark.parametrize(
        "cum_period,expected_rolling_values",
        [(6, [6.7, 6.7, 6.7, 6.7]), (3, [6.7, 6.7, 6.7, 2.4])],
    )
    def test_field_da(self, cum_period, expected_rolling_values):
        lon, lat = [15], [30]
        valid_time = [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 5)]
        coords = {"longitude": lon, "latitude": lat, "valid_time": valid_time}

        field_1_da = xr.DataArray(
            [[[0.3, 1.5, 2.5, 2.4]]],
            coords=coords,
            name="NEIPOT24__SOL",
            attrs={"GRIB_stepUnits": 1, "accum_hour": 1},
        )
        field_da = compute_accumulation(field_1_da, n=4)

        field = FieldCompositeFactory(compute_factory=lambda: field_da)
        field_1 = FieldCompositeFactory(compute_factory=lambda: field_1_da)

        event = EventAccumulationCompositeFactory(
            field=field, field_1=field_1, cum_period=cum_period
        )

        expected_representative_field_da = xr.DataArray(
            [[expected_rolling_values]],
            coords=coords,
            attrs={"GRIB_stepUnits": 1, "accum_hour": 4},
            name="NEIPOT24__SOL",
        )
        assert_identically_close(event.field_da, expected_representative_field_da)

    def test_field_da_with_different_step_units(self):
        lon, lat = [15], [30]
        valid_time = [Datetime(2023, 3, 1).as_np_dt64]
        coords = {"longitude": lon, "latitude": lat, "valid_time": valid_time}

        field_da = xr.DataArray([[[0.3]]], coords=coords, attrs={"GRIB_stepUnits": 1})
        field_1_da = xr.DataArray([[[0.3]]], coords=coords, attrs={"GRIB_stepUnits": 2})

        field = FieldCompositeFactory(compute_factory=lambda: field_da)
        field_1 = FieldCompositeFactory(compute_factory=lambda: field_1_da)

        event = EventAccumulationCompositeFactory(field=field, field_1=field_1)

        with pytest.raises(
            ValueError, match="Both cumulative fields do not have the same stepUnits."
        ):
            _ = event.field_da

    @pytest.mark.parametrize(
        "aggregation,field_1,expected",
        [
            (None, [1, 4, 6, 7, 5, 3, 0, 0, 1, 0, 0, 0], [0.0] + 5 * [1.0] + 6 * [0.0]),
            # test of aggregation method
            (
                Aggregation(method=AggregationMethod.MEAN),
                [1, 4, 6, 7, 5, 3, 0, 0, 1, 0, 0, 0],
                [0.0] + 5 * [1.0] + 6 * [0.0],
            ),
            # rolling operation is done once
            (None, [1, 4, 6, 7, 5, 3], [0.0] + 4 * [1.0] + [0.0]),
            # few valid time
            (None, [4, 24, 1, 1], [1.0, 1.0, 0.0, 0.0]),
        ],
    )
    def test_get_risk(self, aggregation, field_1, expected):
        nbr_valid_time = len(field_1)
        coords = {
            "id": ["sur tout le département"],
            "latitude": [30],
            "longitude": [40, 41],
            "valid_time": [datetime(2023, 3, 1, i) for i in range(nbr_valid_time)],
        }
        field_1_da = xr.DataArray(
            # NaN values to test masked values
            [[[field_1, [np.nan] * nbr_valid_time]]],
            name="NEIPOT24__SOL",
            coords=coords,
            attrs={"GRIB_stepUnits": 1, "accum_hour": 1},
        )
        field_1 = FieldCompositeFactory(compute_factory=lambda: field_1_da)
        field_da = compute_accumulation(field_1_da, n=min(6, nbr_valid_time))
        event = EventAccumulationCompositeFactory(
            field_1=field_1,
            field=FieldCompositeFactory(compute_factory=lambda: field_da),
            aggregation=aggregation,
        )
        threshold = Threshold(threshold=20.0, comparison_op="supegal")

        representative_val = field_da.rolling(
            {"valid_time": min(6, nbr_valid_time)}, min_periods=1
        ).max()
        result = event.get_risk(representative_val, threshold)
        expected = xr.DataArray(
            [
                [
                    [
                        expected,
                        [np.nan] * nbr_valid_time,  # big values are masked so no risk
                    ]
                ]
            ],
            coords=coords,
            name="NEIPOT24__SOL",
            attrs={"GRIB_stepUnits": 1, "accum_hour": 1},
        )
        assert_identically_close(result, expected)

    def test_get_risk_with_different_stepUnits(self):
        coords = {
            "id": ["sur tout le département"],
            "latitude": [30],
            "longitude": [40],
            "valid_time": [datetime(2023, 3, 1, 1)],
        }

        field_1_da = xr.DataArray(
            [[[[0.5]]]],
            dims=["id", "latitude", "longitude", "valid_time"],
            coords=coords,
            attrs={"GRIB_stepUnits": 1},
        )
        field_1 = FieldCompositeFactory(compute_factory=lambda: field_1_da)
        event = EventAccumulationCompositeFactory(field_1=field_1)
        threshold = Threshold(threshold=20.0, comparison_op="supegal")

        field_da = xr.DataArray(
            [[[[0.5]]]],  # big RR values to test the mask
            dims=["id", "latitude", "longitude", "valid_time"],
            coords=coords,
            attrs={"GRIB_stepUnits": 2},
        )

        with pytest.raises(
            ValueError, match="Both cumulative fields do not have the same stepUnits"
        ):
            event.get_risk(field_da, threshold)

    def test_update_selection(self):
        field = FieldCompositeFactory(selection=SelectionFactory())
        field_1 = FieldCompositeFactory(selection=SelectionFactory())
        event = EventAccumulationCompositeFactory(field=field, field_1=field_1)
        new_selection = SelectionFactory()
        event.update_selection(
            new_sel=new_selection.sel,
            new_slice=new_selection.slice,
            new_isel=new_selection.isel,
            new_islice=new_selection.islice,
        )
        assert event.field.selection == new_selection
        assert event.field_1.selection == new_selection
