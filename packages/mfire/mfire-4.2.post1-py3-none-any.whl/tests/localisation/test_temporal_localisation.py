import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.localisation.temporal_localisation import TemporalLocalisation
from mfire.utils.date import Datetime
from tests.functions_test import assert_identically_close


class TestTemporalLocalisation:
    def test_init(self):
        lon, lat = [30], [40]
        valid_time = [Datetime(2023, 3, 1, i).as_np_dt64 for i in range(4)]
        ids = ["id1", "id2"]

        temporal_localisation = TemporalLocalisation(
            data=xr.DataArray(
                [[[[False, False, True, False]]], [[[False, True, False, False]]]],
                coords={
                    "id": ids,
                    "longitude": lon,
                    "latitude": lat,
                    "valid_time": valid_time,
                },
            )
        )
        assert_identically_close(
            temporal_localisation.data,
            xr.DataArray(
                [[[[0.0, 1.0]]], [[[1.0, 0.0]]]],
                coords={
                    "id": ids,
                    "longitude": lon,
                    "latitude": lat,
                    "valid_time": valid_time[1:3],
                },
            ),
        )

    def test_period_summary(self):
        valid_time = [Datetime(2023, 3, 1, i).as_np_dt64 for i in range(5)]
        data = xr.DataArray([True] * 5, coords={"valid_time": valid_time})
        assert_identically_close(
            TemporalLocalisation.period_summary(data),
            xr.Dataset(
                {"elt": (["period"], [True])},
                coords={"period": ["20230301T00_to_20230301T04"]},
            ),
        )

    @pytest.mark.parametrize(
        "data,expected",
        [
            # Basic tests
            (
                [1, 1, 1, 2, 1],
                [np.datetime64("2023-03-01T00"), np.datetime64("2023-03-01T04")],
            ),
            (
                [1, 1, 1, 2, 2, 2],
                [
                    np.datetime64("2023-03-01T00"),
                    np.datetime64("2023-03-01T02"),
                    np.datetime64("2023-03-01T05"),
                ],
            ),
            (
                [1, 1, 1, 2, 2, 2, 2, 2],
                [
                    np.datetime64("2023-03-01T00"),
                    np.datetime64("2023-03-01T02"),
                    np.datetime64("2023-03-01T07"),
                ],
            ),
            (
                [1, 1, 1, 1, 2, 2, 2, 2],
                [
                    np.datetime64("2023-03-01T00"),
                    np.datetime64("2023-03-01T03"),
                    np.datetime64("2023-03-01T07"),
                ],
            ),
            (
                [1, 1, 1, 1, 1, 2, 2, 2],
                [
                    np.datetime64("2023-03-01T00"),
                    np.datetime64("2023-03-01T04"),
                    np.datetime64("2023-03-01T07"),
                ],
            ),
            # More complex test
            (
                [1, 0, 0, 1, 2, 3, 3, 2],
                [
                    np.datetime64("2023-03-01T00"),
                    np.datetime64("2023-03-01T03"),
                    np.datetime64("2023-03-01T07"),
                ],
            ),
            (
                [1, 0, 0, 2, 2, 3, 3, 2],
                [
                    np.datetime64("2023-03-01T00"),
                    np.datetime64("2023-03-01T02"),
                    np.datetime64("2023-03-01T07"),
                ],
            ),
        ],
    )
    def test_two_columns(self, data, expected):
        valid_time = [Datetime(2023, 3, 1, i).as_np_dt64 for i in range(len(data))]
        temporal_localisation = TemporalLocalisation(
            data=xr.DataArray([data], coords={"id": ["id"], "valid_time": valid_time})
        )
        assert temporal_localisation.two_colums == expected

    @pytest.mark.parametrize(
        "data,expected",
        [
            # Basic tests
            (
                [1, 1, 1, 2, 2, 2, 3, 3],
                [np.datetime64("2023-03-01T00"), np.datetime64("2023-03-01T07")],
            ),
            (
                [1, 1, 1, 2, 2, 2, 3, 3, 3],
                [
                    np.datetime64("2023-03-01T00"),
                    np.datetime64("2023-03-01T02"),
                    np.datetime64("2023-03-01T05"),
                    np.datetime64("2023-03-01T08"),
                ],
            ),
            (
                [1, 1, 1, 2, 2, 2, 2, 3, 3, 3],
                [
                    np.datetime64("2023-03-01T00"),
                    np.datetime64("2023-03-01T02"),
                    np.datetime64("2023-03-01T06"),
                    np.datetime64("2023-03-01T09"),
                ],
            ),
            (
                [1, 1, 1, 1, 2, 2, 2, 3, 3, 3],
                [
                    np.datetime64("2023-03-01T00"),
                    np.datetime64("2023-03-01T03"),
                    np.datetime64("2023-03-01T06"),
                    np.datetime64("2023-03-01T09"),
                ],
            ),
            (
                [1, 1, 1, 2, 2, 2, 3, 3, 3, 3],
                [
                    np.datetime64("2023-03-01T00"),
                    np.datetime64("2023-03-01T02"),
                    np.datetime64("2023-03-01T05"),
                    np.datetime64("2023-03-01T09"),
                ],
            ),
            # More complex test
            (
                [1, 0, 1, 2, 1, 2, 2, 3, 2, 3],
                [
                    np.datetime64("2023-03-01T00"),
                    np.datetime64("2023-03-01T02"),
                    np.datetime64("2023-03-01T06"),
                    np.datetime64("2023-03-01T09"),
                ],
            ),
        ],
    )
    def test_three_columns(self, data, expected):
        valid_time = [Datetime(2023, 3, 1, i).as_np_dt64 for i in range(len(data))]
        temporal_localisation = TemporalLocalisation(
            data=xr.DataArray([data], coords={"id": ["id"], "valid_time": valid_time})
        )
        assert temporal_localisation.three_columns == expected

    @pytest.mark.parametrize(
        "data",
        [
            # Less than 6 hours
            [1, 1, 2, 2, 2],
            [1, 1, 1, 2, 2],
            # Between 6 and 8 hours
            [1, 1, 1, 2, 2, 2],
            [1, 1, 1, 2, 2, 2, 2],
            [1, 1, 1, 2, 2, 2, 2, 2],
            # More than 9 hours
            [1, 1, 1, 2, 2, 2, 3, 3, 3],
            [1, 1, 1, 2, 2, 2, 2, 3, 3, 3],
            [1, 1, 1, 2, 2, 2, 3, 3, 3, 3],
        ],
    )
    def test_compute(self, data, assert_equals_result):
        valid_time = [Datetime(2023, 3, 1, i).as_np_dt64 for i in range(len(data))]
        temporal_localisation = TemporalLocalisation(
            data=xr.DataArray([data], coords={"id": ["id"], "valid_time": valid_time})
        )
        assert_equals_result(temporal_localisation.compute().to_dict())
