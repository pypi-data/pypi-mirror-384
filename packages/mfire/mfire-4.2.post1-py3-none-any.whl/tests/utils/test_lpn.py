import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.utils.date import Datetime
from tests.functions_test import assert_identically_close
from tests.utils.factories import LpnFactory


class TestLpn:
    @pytest.mark.parametrize(
        "lpn,expected",
        [
            # No variations
            (
                [0],
                xr.DataArray(
                    [0], coords={"valid_time": [Datetime(2023, 3, 1).as_np_dt64]}
                ),
            ),
            (
                [0, 40, 30, 0],
                xr.DataArray(
                    [0], coords={"valid_time": [Datetime(2023, 3, 1).as_np_dt64]}
                ),
            ),
            (
                [110],
                xr.DataArray(
                    [100], coords={"valid_time": [Datetime(2023, 3, 1).as_np_dt64]}
                ),
            ),
            (
                [100] * 3 + [199] * 3,
                xr.DataArray(
                    [100], coords={"valid_time": [Datetime(2023, 3, 1).as_np_dt64]}
                ),
            ),
            # One variation
            (
                [100] * 3 + [330] * 3 + 3 * [450] + [670] * 3,
                xr.DataArray(
                    [100, 700],
                    coords={
                        "valid_time": [
                            Datetime(2023, 3, 1, i).as_np_dt64 for i in [0, 9]
                        ]
                    },
                ),
            ),
            (
                [560] * 3 + [330] * 3 + [45] * 3,
                xr.DataArray(
                    [600, 0],
                    coords={
                        "valid_time": [
                            Datetime(2023, 3, 1, i).as_np_dt64 for i in [0, 6]
                        ]
                    },
                ),
            ),
            # Two variations
            (
                [100] * 3 + [200] * 3 + [190] * 3 + [300] * 3,
                xr.DataArray(
                    [100, 300],
                    coords={
                        "valid_time": [
                            Datetime(2023, 3, 1, i).as_np_dt64 for i in [0, 9]
                        ]
                    },
                ),
            ),
            (
                [400] * 3 + [380] * 3 + 3 * [600],
                xr.DataArray(
                    [400, 600],
                    coords={
                        "valid_time": [
                            Datetime(2023, 3, 1, i).as_np_dt64 for i in [0, 6]
                        ]
                    },
                ),
            ),
            (
                [100] * 3 + [500] * 3 + [490] * 3,
                xr.DataArray(
                    [100, 500],
                    coords={
                        "valid_time": [
                            Datetime(2023, 3, 1, i).as_np_dt64 for i in [0, 6]
                        ]
                    },
                ),
            ),
            # More than 3 variations
            (
                [120] * 3
                + [500] * 3
                + [470] * 3
                + [460] * 3
                + [800] * 3
                + [820] * 3
                + [530] * 3,
                xr.DataArray(
                    [100, 800, 500],
                    coords={
                        "valid_time": [
                            Datetime(2023, 3, 1, i).as_np_dt64 for i in [0, 15, 18]
                        ]
                    },
                ),
            ),
            # Variation over less than 3 hours - see #42025
            (
                [1500, 700],
                xr.DataArray(
                    [1100], coords={"valid_time": [Datetime(2023, 3, 1).as_np_dt64]}
                ),
            ),
            # Variation over less than 3 hours in middle - see #42584
            (
                [1825] * 3 + [1500, 1500] + [1740] * 3 + [390] * 3,
                xr.DataArray(
                    [1800, 400],
                    coords={
                        "valid_time": [
                            Datetime(2023, 3, 1).as_np_dt64,
                            Datetime(2023, 3, 1, 8).as_np_dt64,
                        ]
                    },
                ),
            ),
        ],
    )
    def test_extremums_da(self, lpn, expected):
        lpn = LpnFactory(
            da=xr.DataArray(
                [[lpn, [v + 5 for v in lpn]]],  # test minimal value taken over space
                coords={
                    "latitude": [30],
                    "longitude": [40, 41],
                    "valid_time": [
                        Datetime(2023, 3, 1, i).as_np_dt64 for i in range(len(lpn))
                    ],
                },
            )
        )
        assert_identically_close(lpn.extremums_da, expected)

    @pytest.mark.parametrize(
        "extremums,expected",
        [
            (None, None),
            ([100], "1xlpn"),
            ([100, 200], "2xlpn+"),
            ([200, 100], "2xlpn-"),
            ([100, 200, 100], "3xlpn+"),
            ([200, 100, 200], "3xlpn-"),
        ],
    )
    def test_template_key(self, extremums, expected):
        lpn_da = xr.DataArray(
            [[[np.nan]]],
            coords={
                "longitude": [40],
                "latitude": [30],
                "valid_time": [Datetime(2023, 3, 1)],
            },
        )  # To handle extremums=None

        assert (
            LpnFactory(
                da=lpn_da,
                extremums_da_factory=xr.DataArray(extremums) if extremums else None,
            ).template_key
            == expected
        )
