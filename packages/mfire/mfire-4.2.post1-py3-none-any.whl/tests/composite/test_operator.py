import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.composite.operator import ComparisonOperator, LogicalOperator
from tests.functions_test import assert_identically_close


class TestLogicalOperator:
    @pytest.mark.parametrize(
        "value,expected", [("and", LogicalOperator.AND), ("or", LogicalOperator.OR)]
    )
    def test_init(self, value, expected):
        assert LogicalOperator(value) == expected

    @pytest.mark.parametrize(
        "first,second,expected",
        [
            (
                xr.DataArray([True, True, False, False]),
                xr.DataArray([True, False, True, False]),
                xr.DataArray([True, True, True, False]),
            ),
            (
                xr.DataArray([np.nan, np.nan]),
                xr.DataArray([True, False]),
                xr.DataArray([True, False]),
            ),
            (
                xr.Dataset(
                    {"data": (["A"], [True, True, False, False])},
                    coords={"A": [1, 2, 3, 4]},
                ),
                xr.Dataset(
                    {"data": (["A"], [True, False, True, False])},
                    coords={"A": [1, 2, 3, 4]},
                ),
                xr.Dataset(
                    {"data": (["A"], [True, True, True, False])},
                    coords={"A": [1, 2, 3, 4]},
                ),
            ),
            (
                xr.Dataset({"data": (["A"], [np.nan, np.nan])}, coords={"A": [1, 2]}),
                xr.Dataset({"data": (["A"], [True, False])}, coords={"A": [1, 2]}),
                xr.Dataset({"data": (["A"], [True, False])}, coords={"A": [1, 2]}),
            ),
        ],
    )
    def test_or_operator(self, first, second, expected):
        result = LogicalOperator.or_operator(first, second)
        assert_identically_close(result, expected)

    @pytest.mark.parametrize(
        "first,second,expected",
        [
            (
                xr.DataArray([True, True, False, False]),
                xr.DataArray([True, False, True, False]),
                xr.DataArray([True, False, False, False]),
            ),
            (
                xr.DataArray([np.nan, np.nan]),
                xr.DataArray([True, False]),
                xr.DataArray([False, False]),
            ),
            (
                xr.Dataset(
                    {"data": (["A"], [True, True, False, False])},
                    coords={"A": [1, 2, 3, 4]},
                ),
                xr.Dataset(
                    {"data": (["A"], [True, False, True, False])},
                    coords={"A": [1, 2, 3, 4]},
                ),
                xr.Dataset(
                    {"data": (["A"], [True, False, False, False])},
                    coords={"A": [1, 2, 3, 4]},
                ),
            ),
            (
                xr.Dataset({"data": (["A"], [np.nan, np.nan])}, coords={"A": [1, 2]}),
                xr.Dataset({"data": (["A"], [True, False])}, coords={"A": [1, 2]}),
                xr.Dataset({"data": (["A"], [False, False])}, coords={"A": [1, 2]}),
            ),
        ],
    )
    def test_and_operator(self, first, second, expected):
        result = LogicalOperator.and_operator(first, second)
        assert_identically_close(result, expected)

    def test_call(self):
        da1 = xr.DataArray([True, True, False, False])
        da2 = xr.DataArray([True, False, True, False])

        assert_identically_close(
            LogicalOperator.AND(da1, da2), xr.DataArray([True, False, False, False])
        )
        assert_identically_close(
            LogicalOperator.OR(da1, da2), xr.DataArray([True, True, True, False])
        )

    @pytest.mark.parametrize(
        "operators,expected",
        [
            ([LogicalOperator.OR, LogicalOperator.OR], [True, True, True, False]),
            ([LogicalOperator.AND, LogicalOperator.AND], [True, False, False, False]),
            ([LogicalOperator.OR, LogicalOperator.AND], [True, False, False, False]),
            ([LogicalOperator.AND, LogicalOperator.OR], [True, True, False, False]),
        ],
    )
    def test_apply(self, operators, expected):
        da1 = xr.DataArray([True, True, True, False])
        da2 = xr.DataArray([True, True, False, False])
        da3 = xr.DataArray([True, False, False, False])

        assert_identically_close(
            LogicalOperator.AND.apply(operators, [da1, da2, da3]),
            xr.DataArray(expected),
        )

    def test_apply_with_wrong_data(self):
        with pytest.raises(
            ValueError, match="Length of operands and operators are " "not compatible."
        ):
            _ = LogicalOperator.apply([LogicalOperator.AND], [])


class TestComparisonOperator:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("sup", ComparisonOperator.SUP),
            ("supegal", ComparisonOperator.SUPEGAL),
            ("inf", ComparisonOperator.INF),
            ("infegal", ComparisonOperator.INFEGAL),
            ("egal", ComparisonOperator.EGAL),
            ("dif", ComparisonOperator.DIF),
            ("isin", ComparisonOperator.ISIN),
            ("not_isin", ComparisonOperator.NOT_ISIN),
        ],
    )
    def test_init(self, value, expected):
        assert ComparisonOperator(value) == expected

    @pytest.mark.parametrize(
        "op,expected",
        [
            (ComparisonOperator.SUP, [False, False, True]),
            (ComparisonOperator.SUPEGAL, [False, True, True]),
            (ComparisonOperator.INF, [True, False, False]),
            (ComparisonOperator.INFEGAL, [True, True, False]),
            (ComparisonOperator.EGAL, [False, True, False]),
            (ComparisonOperator.DIF, [True, False, True]),
            (ComparisonOperator.ISIN, [False, True, False]),
            (ComparisonOperator.NOT_ISIN, [True, False, True]),
        ],
    )
    def test_call(self, op, expected):
        result = op(xr.DataArray([1, 2, 3]), 2)
        assert_identically_close(result, xr.DataArray(expected))

    @pytest.mark.parametrize(
        "op,expected",
        [
            (ComparisonOperator.SUP, True),
            (ComparisonOperator.SUPEGAL, True),
            (ComparisonOperator.INF, True),
            (ComparisonOperator.INFEGAL, True),
            (ComparisonOperator.EGAL, False),
            (ComparisonOperator.DIF, False),
            (ComparisonOperator.ISIN, False),
            (ComparisonOperator.NOT_ISIN, False),
        ],
    )
    def test_is_order(self, op, expected):
        assert op.is_order == expected

    @pytest.mark.parametrize(
        "op,expected",
        [
            (ComparisonOperator.SUP, True),
            (ComparisonOperator.SUPEGAL, True),
            (ComparisonOperator.INF, False),
            (ComparisonOperator.INFEGAL, False),
            (ComparisonOperator.EGAL, False),
            (ComparisonOperator.DIF, False),
            (ComparisonOperator.ISIN, False),
            (ComparisonOperator.NOT_ISIN, False),
        ],
    )
    def test_is_increasing_order(self, op, expected):
        assert op.is_increasing_order == expected

    @pytest.mark.parametrize(
        "op,expected",
        [
            (ComparisonOperator.SUP, False),
            (ComparisonOperator.SUPEGAL, False),
            (ComparisonOperator.INF, True),
            (ComparisonOperator.INFEGAL, True),
            (ComparisonOperator.EGAL, False),
            (ComparisonOperator.DIF, False),
            (ComparisonOperator.ISIN, False),
            (ComparisonOperator.NOT_ISIN, False),
        ],
    )
    def test_is_decreasing_order(self, op, expected):
        assert op.is_decreasing_order == expected

    def test_critical_value(self):
        # Test with DataArray
        val = xr.DataArray(
            [[1, 2], [3, 4], [5, 6]], coords={"A": [7, 8, 9], "B": [10, 11]}
        )
        assert_identically_close(
            ComparisonOperator.SUP.critical_value(val, dim="A"),
            xr.DataArray([5, 6], coords={"B": [10, 11]}),
        )
        assert_identically_close(
            ComparisonOperator.INF.critical_value(val, dim="A"),
            xr.DataArray([1, 2], coords={"B": [10, 11]}),
        )
        assert_identically_close(
            ComparisonOperator.SUP.critical_value(val), xr.DataArray(6)
        )
        assert_identically_close(
            ComparisonOperator.INF.critical_value(val), xr.DataArray(1)
        )
        assert np.isnan(ComparisonOperator.EGAL.critical_value(val, dim="A"))

        # Test with Dataset
        val = xr.Dataset(
            {"C": (["A", "B"], [[1, 2], [3, 4], [5, 6]])},
            coords={"A": [7, 8, 9], "B": [10, 11]},
        )
        assert_identically_close(
            ComparisonOperator.SUPEGAL.critical_value(val, dim="A"),
            xr.Dataset({"C": (["B"], [5, 6])}, coords={"B": [10, 11]}),
        )
        assert_identically_close(
            ComparisonOperator.INFEGAL.critical_value(val, dim="A"),
            xr.Dataset({"C": (["B"], [1, 2])}, coords={"B": [10, 11]}),
        )
        assert_identically_close(
            ComparisonOperator.SUPEGAL.critical_value(val), xr.Dataset({"C": 6})
        )
        assert_identically_close(
            ComparisonOperator.INFEGAL.critical_value(val), xr.Dataset({"C": 1})
        )
        assert np.isnan(ComparisonOperator.EGAL.critical_value(val, dim="A"))

        # Test with list
        assert ComparisonOperator.SUPEGAL.critical_value([1, 2, 3, 4]) == 4
        assert ComparisonOperator.INFEGAL.critical_value([1, 2, 3, 4]) == 1

    @pytest.mark.parametrize(
        "op,expected",
        [
            (ComparisonOperator.SUP, ComparisonOperator.SUP),
            (ComparisonOperator.SUPEGAL, ComparisonOperator.SUP),
            (ComparisonOperator.INF, ComparisonOperator.INF),
            (ComparisonOperator.INFEGAL, ComparisonOperator.INF),
            (ComparisonOperator.EGAL, ComparisonOperator.EGAL),
            (ComparisonOperator.DIF, ComparisonOperator.DIF),
            (ComparisonOperator.ISIN, ComparisonOperator.ISIN),
            (ComparisonOperator.NOT_ISIN, ComparisonOperator.NOT_ISIN),
        ],
    )
    def test_strict(self, op, expected):
        assert op.strict == expected
