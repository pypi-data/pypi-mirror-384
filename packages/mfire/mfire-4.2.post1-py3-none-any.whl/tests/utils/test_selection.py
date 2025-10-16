from datetime import datetime

import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.utils.date import Datetime
from mfire.utils.selection import Selection
from tests.functions_test import assert_identically_close
from tests.utils.factories import SelectionFactory


class TestSelection:
    def test_check_all_keys(self):
        with pytest.raises(ValueError, match="Same keys are found!"):
            _ = Selection(
                sel={"valid_time": Datetime(2023, 3, 1)},
                slice={"valid_time": Datetime(2023, 3, 2)},
            )

    def test_init_slices(self):
        selection = Selection(
            slice={"index1": [datetime(2023, 4, 1), datetime(2023, 5, 2)]},
            islice={"index2": [datetime(2023, 3, 1), datetime(2023, 3, 2)]},
        )
        assert selection.slice == {
            "index1": slice(datetime(2023, 4, 1), datetime(2023, 5, 2))
        }
        assert selection.islice == {
            "index2": slice(datetime(2023, 3, 1), datetime(2023, 3, 2))
        }

    def test_all(self):
        selection = Selection(
            sel={"index1": "a"},
            slice={"index2": slice("b", "c")},
            isel={"index3": "d"},
            islice={"index4": slice("e", "f")},
        )
        assert selection.all == {
            "index1": "a",
            "index2": slice("b", "c"),
            "index3": "d",
            "index4": slice("e", "f"),
        }

    def test_check_valid_time(self):
        selection = Selection(sel={"valid_time": ["2023-03-01", "2023-03-02"]})
        assert selection.sel == {
            "valid_time": [np.datetime64("2023-03-01"), np.datetime64("2023-03-02")]
        }

        selection = Selection(
            slice={"valid_time": [datetime(2023, 4, 1), datetime(2023, 5, 2)]}
        )
        assert selection.slice == {
            "valid_time": slice(
                np.datetime64("2023-04-01"), np.datetime64("2023-05-02")
            )
        }

    def test_update_selection(self):
        selection = SelectionFactory()
        new_selection = SelectionFactory()
        selection.update(
            new_sel=new_selection.sel,
            new_slice=new_selection.slice,
            new_isel=new_selection.isel,
            new_islice=new_selection.islice,
        )

        assert selection == new_selection

    def test_select(self):
        da = xr.DataArray(
            [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], coords={"A": [1, 2, 3], "B": [4, 5]}
        )

        selection = Selection(sel={"B": 5}, slice={"A": slice(2, 3)})
        assert_identically_close(
            selection.select(da),
            xr.DataArray([4.0, 6.0], coords={"A": [2, 3], "B": 5}, dims=["A"]),
        )

        selection = Selection(isel={"B": 0}, islice={"A": slice(0, 2)})
        assert_identically_close(
            selection.select(da),
            xr.DataArray([1.0, 3.0], coords={"A": [1, 2], "B": 4}, dims=["A"]),
        )
