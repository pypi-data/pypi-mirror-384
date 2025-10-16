from pathlib import Path

import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.composite.aggregation import (
    Aggregation,
    AggregationMethod,
    Aggregator,
    InputError,
)
from mfire.utils.date import Datetime
from tests.composite.factories import GeoCompositeFactory
from tests.functions_test import assert_identically_close


class TestAggregationMethod:
    @pytest.mark.parametrize(
        "method,expected",
        [
            ("mean", False),
            ("density", True),
            ("requiredDensity", True),
            ("requiredDensityWeighted", True),
            ("requiredDensityConditional", True),
            ("all", True),
            ("any", True),
            ("max", False),
            ("min", False),
            ("median", False),
            ("sum", False),
            ("std", False),
            ("var", False),
            ("quantile", False),
        ],
    )
    def test_is_post_aggregation(self, method, expected):
        assert AggregationMethod(method).is_post_aggregation == expected


class TestAggregation:
    def test_default_kwargs(self):
        assert Aggregation(method=AggregationMethod.RDENSITY).kwargs == {"dr": 0.5}

        central_mask = GeoCompositeFactory()
        assert Aggregation(
            method=AggregationMethod.RDENSITY_WEIGHTED,
            kwargs={"central_mask": central_mask},
        ).kwargs == {
            "dr": 0.5,  # Le threshold par defaut
            "central_weight": 10,
            "outer_weight": 1,
            "central_mask": central_mask,
        }
        assert Aggregation(method=AggregationMethod.QUANTILE).kwargs == {"q": 0.5}

    def test_missing_key(self):
        with pytest.raises(ValueError) as err:
            Aggregation(
                method=AggregationMethod.RDENSITY_CONDITIONAL, kwargs={"dr": 0.5}
            )
        assert "Missing expected values: ['central_mask']" in str(err.value)

        with pytest.raises(ValueError) as err:
            Aggregation(method=AggregationMethod.RDENSITY_WEIGHTED, kwargs={"dr": 0.5})
        assert "Missing expected values: ['central_mask']" in str(err.value)

    def test_unexpected_key(self):
        with pytest.raises(ValueError) as err:
            Aggregation(method=AggregationMethod.MEAN, kwargs={"dr": 0.5})
        assert "Unexpected values: ['dr']" in str(err.value)

        with pytest.raises(ValueError) as err:
            Aggregation(
                method=AggregationMethod.RDENSITY,
                kwargs={"dr": 0.5, "central_mask": GeoCompositeFactory()},
            )
        assert "Unexpected values: ['central_mask']" in str(err.value)

        with pytest.raises(ValueError) as err:
            Aggregation(
                method=AggregationMethod.RDENSITY_CONDITIONAL,
                kwargs={
                    "dr": 0.5,
                    "central_mask": GeoCompositeFactory(),
                    "central_weight": 1,
                    "outer_weight": 1,
                },
            )
        assert "Unexpected values: ['central_weight', 'outer_weight']" in str(err.value)

    def test_check_method_kwargs(self):
        agg = Aggregation(
            method=AggregationMethod.MEAN,
            kwargs={
                "dr": None,
                "central_weight": None,
                "outer_weight": None,
                "central_mask": None,
            },
        )
        assert isinstance(agg, Aggregation)
        assert agg.kwargs == {}

    @pytest.mark.parametrize(
        "configuration,grid_name",
        [
            ({"method": "mean"}, None),
            ({"kwargs": {"dr": 5}, "method": "requiredDensity"}, None),
            ({"kwargs": {"drConditional": 5}, "method": "requiredDensity"}, None),
            ({"kwargs": {"drCentralZone": 5}, "method": "requiredDensity"}, None),
            (
                {
                    "kwargs": {
                        "drCentralZone": 5,
                        "centralWeight": 8,
                        "outerWeight": 3,
                        "centralZone": "mask_id",
                    },
                    "method": "requiredDensityWeighted",
                },
                None,
            ),
            (
                {
                    "kwargs": {
                        "drCentralZone": 5,
                        "centralWeight": 8,
                        "outerWeight": 3,
                        "centralZoneConditional": "mask_id",
                    },
                    "method": "requiredDensityWeighted",
                },
                None,
            ),
            (
                {
                    "kwargs": {
                        "drCentralZone": 5,
                        "centralWeight": 5,
                        "outerWeight": 5,
                        "centralZone": "mask_id",
                    },
                    "method": "requiredDensityWeighted",
                },
                "grid_name",
            ),
        ],
    )
    def test_from_configuration(self, configuration, grid_name, assert_equals_result):
        aggregation = Aggregation.from_configuration(
            configuration, mask_file=Path("mask_file"), grid_name=grid_name
        )
        assert_equals_result(aggregation)

    @pytest.mark.parametrize(
        "method,expected",
        [
            ("mean", False),
            ("density", True),
            ("requiredDensity", True),
            ("all", True),
            ("any", True),
            ("max", False),
            ("min", False),
            ("median", False),
            ("sum", False),
            ("std", False),
            ("var", False),
            ("quantile", False),
        ],
    )
    def test_is_post(self, method, expected):
        assert Aggregation(method=method).is_post == expected

    @pytest.mark.parametrize(
        "method,expected",
        [
            ("mean", True),
            ("density", False),
            ("requiredDensity", False),
            ("all", False),
            ("any", False),
            ("max", True),
            ("min", True),
            ("median", True),
            ("sum", True),
            ("std", True),
            ("var", True),
            ("quantile", True),
        ],
    )
    def test_is_pre(self, method, expected):
        assert Aggregation(method=method).is_pre == expected


class TestAggregator:
    def test_compute_fails(self):
        agg = Aggregator(xr.DataArray())

        with pytest.raises(InputError, match="DR given = 1.5"):
            agg.compute(
                Aggregation(method=AggregationMethod.RDENSITY, kwargs={"dr": 1.5})
            )

        with pytest.raises(InputError, match="DR given = -1"):
            agg.compute(
                Aggregation(
                    method=AggregationMethod.RDENSITY_CONDITIONAL,
                    kwargs={"dr": -1, "central_mask": {}},
                )
            )

        with pytest.raises(InputError, match="DR given = -1"):
            agg.compute(
                Aggregation(
                    method=AggregationMethod.RDENSITY_WEIGHTED,
                    kwargs={
                        "dr": -1,
                        "central_mask": {},
                        "central_weight": 0.0,
                        "outer_weight": 0.0,
                    },
                )
            )

    def test_density(self):
        lon, lat = [31, 32, 33, 34], [40]
        valid_time = [Datetime(2023, 3, 1).as_np_dt64, Datetime(2023, 3, 2).as_np_dt64]

        da = xr.DataArray(
            [[[1.0, 1.0], [1.0, 0.0], [0.0, 0.0], [np.nan, np.nan]]],
            coords={"latitude": lat, "longitude": lon, "valid_time": valid_time},
        )
        agg_handler = Aggregator(da)
        agg = Aggregation(method=AggregationMethod.DENSITY)
        assert_identically_close(
            agg_handler.compute(agg),
            xr.DataArray([2 / 3, 1 / 3], coords={"valid_time": valid_time}),
        )

        # Test with not default aggregate_dim
        agg_handler.aggregate_dim = "valid_time"
        assert_identically_close(
            agg_handler.compute(agg),
            xr.DataArray(
                [[1.0, 0.5, 0.0, np.nan]], coords={"latitude": lat, "longitude": lon}
            ),
        )

    def test_required_density(self):
        # Without aggregate dimension
        lon, lat = [31, 32], [40]
        valid_time = [Datetime(2023, 3, 1).as_np_dt64, Datetime(2023, 3, 2).as_np_dt64]

        da = xr.DataArray(
            [[[0.1, 0.2], [0.3, 0.4]]],
            coords={"latitude": lat, "longitude": lon, "valid_time": valid_time},
        )
        agg_handler = Aggregator(da)

        agg = Aggregation(method=AggregationMethod.RDENSITY, kwargs={"dr": 0.25})
        expected = xr.DataArray([False, True], coords={"valid_time": valid_time})
        assert_identically_close(agg_handler.compute(agg), expected)

        # With aggregate dimension
        agg_handler = Aggregator(da, aggregate_dim="valid_time")
        expected = xr.DataArray(
            [[False, True]], coords={"latitude": lat, "longitude": lon}
        )
        assert_identically_close(agg_handler.compute(agg), expected)

        # Test the minimal threshold - see #?????
        agg_handler = Aggregator(
            xr.DataArray([[0.001]], coords={"latitude": [30], "longitude": [40]})
        )
        agg = Aggregation(method=AggregationMethod.RDENSITY, kwargs={"dr": 0})
        assert_identically_close(agg_handler.compute(agg), xr.DataArray(False))
        agg_handler = Aggregator(
            xr.DataArray([[0.00101]], coords={"latitude": [30], "longitude": [40]})
        )
        assert_identically_close(agg_handler.compute(agg), xr.DataArray(True))

    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_drr_weighted(self, test_file):
        lon, lat = [15.0, 16.0], [17.0]
        valid_time = [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 4)]
        ds = xr.Dataset(
            {"A": (["id", "latitude_monde", "longitude_glob05"], [[[True, False]]])},
            coords={
                "id": ["id_central_mask"],
                "latitude_monde": lat,
                "longitude_glob05": lon,
            },
        )
        ds.to_netcdf(test_file)

        da = xr.DataArray(
            [[[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]]],
            coords={
                "id": ["id_area"],
                "latitude": lat,
                "longitude": lon,
                "valid_time": valid_time,
            },
            attrs={"PROMETHEE_z_ref": "A"},
        )
        agg_handler = Aggregator(da)
        agg = Aggregation(
            method=AggregationMethod.RDENSITY_WEIGHTED,
            kwargs={
                "dr": 0.2,
                "central_mask": {"file": test_file, "mask_id": "id_central_mask"},
                "central_weight": 0.5,
                "outer_weight": 0.1,
            },
        )

        result = agg_handler.compute(agg)
        expected = xr.DataArray(
            [[False, False, True]],
            coords={
                "id": ["id_area"],
                "valid_time": valid_time,
                "areaName": "unknown",
                "altAreaName": "unknown",
                "areaType": "unknown",
            },
            dims=["id", "valid_time"],
            attrs={"PROMETHEE_z_ref": "A"},
        )
        assert_identically_close(result, expected)

    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_drr_conditional(self, test_file):
        lon, lat = [15.0, 16.0], [17.0]
        valid_time = [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 4)]
        ds = xr.Dataset(
            {"A": (["id", "latitude_monde", "longitude_glob05"], [[[True, False]]])},
            coords={
                "id": ["id_central_mask"],
                "latitude_monde": lat,
                "longitude_glob05": lon,
            },
        )
        ds.to_netcdf(test_file)

        da = xr.DataArray(
            [[[[0, 0.2, 0.3], [0.4, 0.5, 0.6]]]],
            coords={
                "id": ["id_area"],
                "latitude": lat,
                "longitude": lon,
                "valid_time": valid_time,
            },
            attrs={"PROMETHEE_z_ref": "A"},
        )
        agg = Aggregation(
            method=AggregationMethod.RDENSITY_CONDITIONAL,
            kwargs={
                "dr": 0.4,
                "central_mask": {"file": test_file, "mask_id": "id_central_mask"},
            },
        )

        # Test without aggregate_dim
        result = Aggregator(da).compute(agg)
        expected = xr.DataArray(
            [[False, True, True]],
            coords={
                "id": ["id_area"],
                "valid_time": valid_time,
                "areaName": "unknown",
                "altAreaName": "unknown",
                "areaType": "unknown",
            },
            dims=["id", "valid_time"],
            attrs={"PROMETHEE_z_ref": "A"},
        )
        assert_identically_close(result, expected)

        # Test with aggregate_dim
        result = Aggregator(da, aggregate_dim="valid_time").compute(agg)
        expected = xr.DataArray(
            [[[True, True]]],
            coords={
                "id": ["id_area"],
                "latitude": lat,
                "longitude": lon,
                "areaName": "unknown",
                "altAreaName": "unknown",
                "areaType": "unknown",
            },
            dims=["id", "latitude", "longitude"],
            attrs={"PROMETHEE_z_ref": "A"},
        )
        assert_identically_close(result, expected)
