from datetime import datetime

import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.composite.field import Selection
from mfire.utils.date import Datetime
from tests.composite.factories import FieldCompositeFactory, SelectionFactory
from tests.functions_test import assert_identically_close


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


class TestFieldComposite:
    def test_check_selection(self):
        field_compo = FieldCompositeFactory()
        assert field_compo.selection == Selection()

    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_compute(self, test_file):
        da = xr.DataArray(
            [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]],
            coords={"A": [1, 2, 3], "B": [4, 5]},
            name="field_name",
        )
        da.to_netcdf(test_file)

        selection = Selection(sel={"B": 5}, slice={"A": slice(2, 3)})
        field_compo = FieldCompositeFactory(file=test_file, selection=selection)
        assert_identically_close(
            field_compo.compute(),
            xr.DataArray(
                [4.0, 6.0], coords={"A": [2, 3], "B": 5}, dims=["A"], name="field_name"
            ),
        )

        selection = Selection(isel={"B": 0}, islice={"A": slice(0, 2)})
        field_compo = FieldCompositeFactory(file=test_file, selection=selection)
        assert_identically_close(
            field_compo.compute(),
            xr.DataArray(
                [1.0, 3.0], coords={"A": [1, 2], "B": 4}, dims=["A"], name="field_name"
            ),
        )

    @pytest.mark.parametrize(
        "test_file", [{"nbr": 2, "extension": "nc"}], indirect=True
    )
    def test_compute_with_list(self, test_file):
        da = xr.DataArray(
            [[[1.0, 2.0, 3.0, 4.0, 5.0], [6.0, 7.0, 8.0, 9.0, 10.0]]],
            coords={
                "valid_time": [Datetime(2023, 3, 1).as_np_dt64],
                "latitude": [41.02, 41.03],
                "longitude": [10.40, 10.41, 10.42, 10.43, 10.44],
            },
            name="field_name_1",
            attrs={"units": "cm"},
        )
        da.to_netcdf(test_file[0])

        da = xr.DataArray(
            [[[110, 120, 130], [140, 150, 160]]],
            coords={
                "valid_time": [Datetime(2023, 3, 2).as_np_dt64],
                "latitude": [41.02, 41.03],
                "longitude": [10.40, 10.42, 10.44],
            },
            name="field_name_2",
            attrs={"units": "mm"},
        )
        da.to_netcdf(test_file[1])

        field_compo = FieldCompositeFactory(file=test_file, grid_name="franxl1s100")

        result = field_compo.compute()
        expected = xr.DataArray(
            [
                [
                    [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
                    [1.0, 2.0, 3.0, 4.0, 5.0, np.nan],
                    [6.0, 7.0, 8.0, 9.0, 10.0, np.nan],
                ],
                [
                    [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
                    [11.0, 11.0, 12.0, 12.0, 13.0, np.nan],
                    [14.0, 14.0, 15.0, 15.0, 16.0, np.nan],
                ],
            ],
            coords={
                "valid_time": [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 3)],
                "latitude": [41.01, 41.02, 41.03],
                "longitude": [10.40, 10.41, 10.42, 10.43, 10.44, 10.45],
            },
            name="field_name_1",
            attrs={"units": "cm"},
        )
        assert_identically_close(result, expected)

    @pytest.mark.parametrize(
        "test_file", [{"nbr": 2, "extension": "nc"}], indirect=True
    )
    def test_compute_with_list_and_wwmf(self, test_file):
        da = xr.DataArray(
            [[[1, 4, 11, 14, 17], [19, 20, 25, 29, 16]]],
            coords={
                "valid_time": [Datetime(2023, 3, 1).as_np_dt64],
                "latitude": [41.02, 41.03],
                "longitude": [10.40, 10.41, 10.42, 10.43, 10.44],
            },
            name="field_name_1",
            attrs={"units": "w1"},
        )
        da.to_netcdf(test_file[0])

        da = xr.DataArray(
            [[[62, 59, 51], [31, 40, 92]]],
            coords={
                "valid_time": [Datetime(2023, 3, 2).as_np_dt64],
                "latitude": [41.02, 41.03],
                "longitude": [10.40, 10.42, 10.44],
            },
            name="field_name_2",
            attrs={"units": "wwmf"},
        )
        da.to_netcdf(test_file[1])

        field_compo = FieldCompositeFactory(file=test_file, grid_name="franxl1s100")

        result = field_compo.compute()
        expected = xr.DataArray(
            [
                [
                    [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
                    [31, 38, 53, 58, 63, np.nan],
                    [70, 77, 93, 98, 62, np.nan],
                ],
                [
                    [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
                    [62, 62, 59, 59, 51, np.nan],
                    [31, 31, 40, 40, 92, np.nan],
                ],
            ],
            coords={
                "valid_time": [Datetime(2023, 3, i).as_np_dt64 for i in range(1, 3)],
                "latitude": [41.01, 41.02, 41.03],
                "longitude": [10.40, 10.41, 10.42, 10.43, 10.44, 10.45],
            },
            name="field_name_1",
            attrs={"units": "wwmf"},
        )
        assert_identically_close(result, expected)

    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_coord(self, test_file):
        da = xr.DataArray([1, 2, 3, 4], coords={"A": [1.0, 2.0, 3.0, 4.0]})
        da.to_netcdf(test_file)

        # Test without selection
        field_compo = FieldCompositeFactory(file=test_file)
        assert_identically_close(field_compo.coord("A"), np.array([1.0, 2.0, 3.0, 4.0]))

        # Test with selection
        field_compo = FieldCompositeFactory(
            file=test_file, selection=Selection(slice={"A": slice(2.0, 3.0)})
        )
        assert_identically_close(field_compo.coord("A"), np.array([2.0, 3.0]))
