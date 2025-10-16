import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from tests.functions_test import assert_identically_close


class TestTypeAccessor:
    def test_bool(self):
        da = xr.DataArray([1.0, -1.0, np.nan])

        result = da.wheretype.bool(da > 0)
        expected = xr.DataArray([True, False, False])
        assert_identically_close(result, expected)

    def test_f32(self):
        da = xr.DataArray([1.0, -1.0, np.nan])

        result = da.wheretype.f32(da > 0)
        expected = xr.DataArray([1.0, np.nan, np.nan])
        assert_identically_close(result, expected)


class TestMaskAccessor:
    def test_bad_dtype(self):
        with pytest.raises(
            ValueError,
            match="Dtype for DataArray of MaskAccessor must be numeric or boolean",
        ):
            _ = xr.DataArray(["hello"]).mask

    @pytest.mark.parametrize(
        "da,expected",
        [([True, False], [True, False]), ([1.0, 0.0, np.nan], [True, False, False])],
    )
    def test_bool(self, da, expected):
        assert_identically_close(xr.DataArray(da).mask.bool, xr.DataArray(expected))

    @pytest.mark.parametrize("da", [[True, False], [1.0, 0.0, np.nan]])
    def test_bool_dropped(self, da):
        da = xr.DataArray(da, coords={"A": range(len(da))})
        expected = xr.DataArray([True], coords={"A": [0]})
        assert_identically_close(da.mask.bool_dropped, expected)

    @pytest.mark.parametrize(
        "da,expected",
        [
            ([True, False], [1.0, np.nan]),
            ([1.0, 20.0, 0.0, np.nan], [1.0, 1.0, np.nan, np.nan]),
        ],
    )
    def test_f32(self, da, expected):
        result = xr.DataArray(da).mask.f32
        assert_identically_close(result, xr.DataArray(expected))
        assert result.dtype == "float32"

    @pytest.mark.parametrize(
        "da", [[True, False], [1.0, 0.0, np.nan], [20.0, 0.0, np.nan]]
    )
    def test_f32_dropped(self, da):
        result = xr.DataArray(da, coords={"A": range(len(da))}).mask.f32_dropped
        expected = xr.DataArray([1.0], coords={"A": [0]})
        assert_identically_close(result, expected)
        assert result.dtype == "float32"

    @pytest.mark.parametrize(
        "da1,da2,expected_f32",
        [
            ([True, True, False], [True, False, False], [1.0, 1.0, np.nan]),
            ([1.0, 1.0, 1.0], [1.0, 0.0, np.nan], [1.0, 1.0, 1.0]),
            ([0.0, 0.0], [0.0, np.nan], [np.nan, np.nan]),
            ([np.nan], [np.nan], [np.nan]),
        ],
    )
    def test_union(self, da1, da2, expected_f32):
        da1 = xr.DataArray(da1)
        da2 = xr.DataArray(da2)
        expected = xr.DataArray(expected_f32)

        assert_identically_close(da1.mask.union(da2).f32, expected)
        assert_identically_close(da2.mask.union(da1).f32, expected)
        assert_identically_close(da1.mask.union(da2.mask).f32, expected)
        assert_identically_close(da2.mask.union(da1.mask).f32, expected)

    def test_unions(self):
        da1 = xr.DataArray([1.0, np.nan, np.nan, np.nan])
        da2 = xr.DataArray([1.0, 1.0, np.nan, np.nan])
        da3 = xr.DataArray([1.0, 1.0, 1.0, np.nan])

        assert_identically_close(xr.MaskAccessor.unions(da1, da2, da3).f32, da3)
        assert_identically_close(xr.MaskAccessor.unions(da1, da3, da2).f32, da3)
        assert_identically_close(xr.MaskAccessor.unions(da2, da1, da3).f32, da3)
        assert_identically_close(xr.MaskAccessor.unions(da2, da3, da1).f32, da3)
        assert_identically_close(xr.MaskAccessor.unions(da3, da1, da2).f32, da3)
        assert_identically_close(xr.MaskAccessor.unions(da3, da2, da1).f32, da3)

    def test_sum(self):
        A = xr.DataArray([1.0, 0.0, np.nan, 1.0])
        B = xr.DataArray([np.nan, np.nan, np.nan, 1.0])
        assert_identically_close(xr.MaskAccessor.sum(A, None), A)
        assert_identically_close(xr.MaskAccessor.sum(None, B), B)
        assert_identically_close(
            xr.MaskAccessor.sum(A, B), xr.DataArray([1.0, 0.0, np.nan, 1.0])
        )
