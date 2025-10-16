import numpy as np
import pandas as pd
import pytest

from mfire.utils import mfxarray as xr
from mfire.utils.date import Datetime
from mfire.utils.exception import LoaderError
from mfire.utils.xr import (
    ArrayLoader,
    Loader,
    MaskLoader,
    compute_grib_step_size,
    compute_step_size,
    compute_sum_future,
    da_set_up,
    disaggregate_sum_values,
    extend_da,
    fill_da,
    finest_grid_name,
    from_0_360_to_center,
    from_center_to_0_360,
    interpolate_to_new_grid,
    rounding,
    slice_da,
    stepping_data,
)
from tests.functions_test import assert_identically_close


class TestXrUtilsGridFunctions:
    def test_da_set_up(self):
        mask = xr.DataArray(
            np.zeros((2, 5, 5)),
            dims=["id", "latitude", "longitude"],
            coords={
                "longitude": [10, 11, 12, 13, 14],
                "latitude": [40, 41, 42, 43, 44],
                "id": ["id1", "id2"],
                "areaName": (["id"], ["areaName1", "areaName2"]),
                "areaType": (["id"], ["areaType1", "areaType2"]),
            },
        )
        da = xr.DataArray(
            np.zeros((2, 2)),
            dims=["latitude", "longitude"],
            coords={
                "longitude": [11, 12],
                "latitude": [42, 43],
                "id": "id3",
                "areaName": "areaName3",
                "areaType": "areaType3",
            },
        )
        assert_identically_close(
            da_set_up(mask, da),
            xr.DataArray(
                np.zeros((2, 2, 2)),
                dims=["id", "latitude", "longitude"],
                coords={
                    "longitude": [11, 12],
                    "latitude": [42, 43],
                    "id": ["id1", "id2"],
                    "areaName": (["id"], ["areaName1", "areaName2"]),
                    "areaType": (["id"], ["areaType1", "areaType2"]),
                },
            ),
        )

    def test_from_0_360_to_center(self):
        lon = [-170, 0, 180]
        grid_da_0_360 = xr.DataArray([1, 2, 3], coords={"longitude": lon})

        # Perform transformation from [0:360] to [-180:180]
        expected_lon = xr.DataArray([-180, -170, 0], dims="longitude")
        expected_da = xr.DataArray([3, 1, 2], coords={"longitude": expected_lon})

        transformed_da = from_0_360_to_center(grid_da_0_360)

        # Check if the transformed data array matches the expected result
        assert_identically_close(transformed_da, expected_da)

    def test_from_center_to_0_360(self):
        lon = xr.DataArray([-10, 100, 190], dims="longitude")
        grid_da_center = xr.DataArray([1, 2, 3], coords={"longitude": lon})

        # Perform transformation from [-180:180] to [0:360]
        expected_lon = xr.DataArray([100, 190, 350], dims="longitude")
        expected_da = xr.DataArray([2, 3, 1], coords={"longitude": expected_lon})

        transformed_da = from_center_to_0_360(grid_da_center)

        # Check if the transformed data array matches the expected result
        assert_identically_close(transformed_da, expected_da)

    def test_interpolate_to_new_grid(self):
        da = xr.DataArray(
            [[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]],
            coords={
                "valid_time": [Datetime(2023, 3, 1).as_np_dt64],
                "latitude": [41.02, 41.03],
                "longitude": [10.40, 10.42, 10.44],
            },
        )

        result = interpolate_to_new_grid(da, "franxl1s100")
        expected = xr.DataArray(
            [
                [
                    [4.0, 4.0, 5.0, 5.0, 6.0, np.nan],
                    [1.0, 1.0, 2.0, 2.0, 3.0, np.nan],
                    [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
                ]
            ],
            coords={
                "valid_time": [Datetime(2023, 3, 1).as_np_dt64],
                "latitude": [41.03, 41.02, 41.01],
                "longitude": [10.40, 10.41, 10.42, 10.43, 10.44, 10.45],
            },
        )
        assert_identically_close(result, expected)

    def test_finest_grid_name(self):
        latitude_eurw1s100, longitude_eurw1s100 = [1, 2], [5, 6, 7]
        coords = {
            "id": ("id", ["zone1", "zone2", "zone3", "axe"]),
            "latitude_eurw1s100": ("latitude_eurw1s100", latitude_eurw1s100),
            "longitude_eurw1s100": ("longitude_eurw1s100", longitude_eurw1s100),
            "latitude_best": ("latitude_best", [1, 2, 3]),
            "longitude_best": ("longitude_best", [5, 6, 7, 4]),
        }
        value = [
            [[1, 0, 0], [1, 0, 0]],
            [[0, 1, 0], [0, 1, 0]],
            [[0, 0, 1], [0, 0, 1]],
            [[1, 1, 1], [1, 1, 1]],
        ]
        value_best = [
            [[1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]],
            [[0, 1, 0, 0], [0, 1, 0, 0], [0, 1, 0, 0]],
            [[0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 1, 0]],
            [[1, 1, 1, 0], [1, 1, 1, 0], [1, 1, 1, 0]],
        ]
        data_vars = {
            "eurw1s100": (["id", "latitude_eurw1s100", "longitude_eurw1s100"], value),
            "best": (["id", "latitude_best", "longitude_best"], value_best),
            "areaName": (["id"], ["nom1", "nom2", "nom3", "nom4"]),
        }
        ds = xr.Dataset(data_vars=data_vars, coords=coords)
        assert finest_grid_name(ds) == "best"


class TestXrUtilsDataArrayFunctions:
    def test_slice_da(self):
        # create reversed dates
        times = pd.date_range("2022-01-01", "2022-01-05", freq="D")

        # Create a test DataArray
        data = np.random.randn(len(times), 3, 4)
        da = xr.DataArray(
            data, coords=[times, range(3), range(4)], dims=["valid_time", "x", "y"]
        )

        # Call the slice_da function with specific parameters
        start = np.datetime64("2022-01-02")
        stop = np.datetime64("2022-01-08")
        step = 3
        sliced_da = slice_da(da, start=start, stop=stop, step=step)

        # Verify the expected results
        expected_da = da.sel(valid_time=slice("2022-01-02", "2022-01-06", 3))
        assert_identically_close(sliced_da, expected_da)

        # Call the slice_da function without specifying parameters
        da["valid_time"] = da["valid_time"].data[::-1]
        sliced_da_default = slice_da(da)

        # Verify the expected results using default minimum and maximum values
        assert_identically_close(sliced_da_default, da)

    def test_extend_da(self):
        # Create a test DataArray
        times = pd.date_range("2022-01-01", "2022-01-05", freq="D")
        data = np.random.randn(len(times), 3, 4)
        da = xr.DataArray(
            data,
            coords={"valid_time": times, "x": range(3), "y": range(4)},
            dims=["valid_time", "x", "y"],
        )

        # Call the extend_da function with specific parameters
        start = np.datetime64("2022-01-06")
        stop = np.datetime64("2022-01-10")
        step = 2
        freq_base = "D"
        extended_da = extend_da(
            da, start=start, stop=stop, step=step, freq_base=freq_base
        )

        # Verify the expected results
        expected_data = np.concatenate((data, np.ones((3, 3, 4)) * np.nan))
        expected_times = np.concatenate(
            (times, pd.date_range("2022-01-06", "2022-01-10", freq="2D")), axis=None
        )
        expected_da = xr.DataArray(
            expected_data,
            coords={"valid_time": expected_times, "x": range(3), "y": range(4)},
            dims=["valid_time", "x", "y"],
        )
        assert_identically_close(extended_da, expected_da)

    def test_fill_da(self):
        # Create a test DataArray
        times = pd.date_range("2022-01-01", "2022-01-02", freq="D")
        data = np.random.randn(len(times), 3, 4)
        da = xr.DataArray(
            data,
            coords={"valid_time": times, "x": range(3), "y": range(4)},
            dims=["valid_time", "x", "y"],
        )

        # Define the source steps and target step
        source_steps = [5, 2]
        target_step = 2

        # Call the fill_da function
        filled_da = fill_da(da, source_steps=source_steps, target_step=target_step)

        # Check if the filled values are correctly extended and filled
        expected_valid_time = [
            np.datetime64("2021-12-31T20:00"),
            np.datetime64("2021-12-31T22:00"),
            np.datetime64("2022-01-01T00:00"),
            np.datetime64("2022-01-01T23:00"),
            np.datetime64("2022-01-02T01:00"),
        ]
        assert np.array_equal(filled_da.valid_time, expected_valid_time)

        # Call fill_da with different siez between source_steps and valid_time
        not_filled_da = fill_da(da, source_steps=[5])
        assert_identically_close(da, not_filled_da)

    def test_disaggregate_sum_values(self):
        coords = {
            "valid_time": [
                np.datetime64("2023-03-01T05:00:00.000000000"),
                np.datetime64("2023-03-01T09:00:00.000000000"),
            ]
        }
        da = xr.DataArray([0, 12], coords=coords)
        da_step = xr.DataArray([2, 4], coords=coords)
        stepout = 2
        expected = xr.DataArray(
            [0.0, 6.0, 6.0],
            coords={
                "valid_time": [
                    Datetime(2023, 3, 1, 4).as_np_dt64,
                    Datetime(2023, 3, 1, 6).as_np_dt64,
                    Datetime(2023, 3, 1, 8).as_np_dt64,
                ]
            },
            attrs={
                "stepUnits": stepout,
                "accum_hour": stepout,
                "history": "Disaggregation performed. The assumption was made that "
                "filling by the forward value is needed. The value has been "
                "disaggregated by taking the mean.",
            },
        )

        result = disaggregate_sum_values(da, da_step, stepout)
        assert_identically_close(result, expected)

    def test_compute_step_size(self):
        # Test with Dataset
        ds = xr.Dataset(
            coords={
                "valid_time": [
                    Datetime(2023, 3, 1, 4),
                    Datetime(2023, 3, 1, 6),
                    Datetime(2023, 3, 1, 10),
                    Datetime(2023, 3, 1, 20),
                ]
            }
        )
        result = compute_step_size(ds)
        np.testing.assert_array_equal(result, [2, 4, 10, 10])

        # Test with DataArray
        da = xr.DataArray(
            [1.0, 2.0, 3.0, 4.0],
            coords={
                "valid_time": [
                    Datetime(2023, 3, 1, 4),
                    Datetime(2023, 3, 1, 6),
                    Datetime(2023, 3, 1, 10),
                    Datetime(2023, 3, 1, 20),
                ]
            },
        )
        result = compute_step_size(da)
        np.testing.assert_array_equal(result, [2, 4, 10, 10])

    @pytest.mark.parametrize(
        "data_list",
        [
            [
                xr.Dataset(
                    None,
                    coords={"valid_time": Datetime(2023, 3, 1, i).as_np_dt64},
                    attrs={"accum_hour": i},
                )
                for i in range(1, 4)
            ],
            [
                xr.DataArray(
                    None,
                    coords={"valid_time": Datetime(2023, 3, 1, i).as_np_dt64},
                    dims=[],
                    attrs={"accum_hour": i},
                )
                for i in range(1, 4)
            ],
        ],
    )
    def test_compute_grib_step_size(self, data_list):
        result = compute_grib_step_size(data_list)
        assert_identically_close(
            result,
            xr.DataArray(
                [1, 2, 3],
                coords={
                    "valid_time": [
                        Datetime(2023, 3, 1, i).as_np_dt64 for i in range(1, 4)
                    ]
                },
                attrs={"units": "hours"},
                name="step_size",
            ),
        )

    @pytest.mark.parametrize("step_out", [1, 6])
    def test_compute_sum_future(self, step_out, assert_equals_result):
        lon, lat = [15], [30]
        valid_time = [
            Datetime(2023, 3, 1).as_np_dt64,
            Datetime(2023, 3, 1, 3).as_np_dt64,
            Datetime(2023, 3, 1, 6).as_np_dt64,
        ]
        coords = {"longitude": lon, "latitude": lat, "valid_time": valid_time}

        da = xr.DataArray(
            [[[3, 6, 9]]], coords=coords, attrs={"GRIB_startStep": 0}, name="name"
        )
        da_step = xr.DataArray([3, 3, 3], coords={"valid_time": valid_time})

        assert_equals_result(
            compute_sum_future(da, da_step, step_out=step_out).to_dict()
        )

    @pytest.mark.parametrize("step_out", [1, 6])
    def test_stepping_data(self, step_out, assert_equals_result):
        lon, lat = [15], [30]
        valid_time = [
            Datetime(2023, 3, 1).as_np_dt64,
            Datetime(2023, 3, 1, 3).as_np_dt64,
            Datetime(2023, 3, 1, 6).as_np_dt64,
        ]
        coords = {"longitude": lon, "latitude": lat, "valid_time": valid_time}

        da = xr.DataArray(
            [[[3, 6, 9]]], coords=coords, attrs={"GRIB_startStep": 0}, name="name"
        )
        da_step = xr.DataArray([3, 3, 3], coords={"valid_time": valid_time})

        assert_equals_result(stepping_data(da, da_step, step_out=step_out).to_dict())


class TestXrUtilsFunctions:
    def test_rounding(self):
        val = xr.DataArray(
            [[[1.000015]]],
            coords={
                "longitude": [10.000015],
                "latitude": [9.000015],
                "other_val": [15.000015],
            },
        )
        result = rounding(val)
        expected = xr.DataArray(
            [[[1.000015]]],
            coords={
                "longitude": [10.00002],
                "latitude": [9.00002],
                "other_val": [15.000015],
            },
        )
        assert_identically_close(result, expected)


class TestLoader:
    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_load(self, test_file):
        ds = xr.Dataset({"B": (["A"], [1.0, 2.0, 3.0])}, coords={"A": [4.0, 5.0, 6.0]})
        ds.to_netcdf(test_file)

        loader = Loader(filename=test_file)
        assert_identically_close(loader.load(), ds)

        loader = Loader(filename="file_does_not_exist")
        with pytest.raises(LoaderError, match="file_does_not_exist"):
            loader.load()

    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_dump(self, test_file):
        ds = xr.Dataset({"B": (["A"], [1.0, 2.0, 3.0])}, coords={"A": [4.0, 5.0, 6.0]})
        loader = Loader(filename=test_file)

        assert loader.dump(ds) is True
        assert_identically_close(xr.open_dataset(test_file), ds)

        # test of the re-dump
        assert loader.dump(ds) is True
        assert_identically_close(xr.open_dataset(test_file), ds)


class TestArrayLoader:
    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_load(self, test_file):
        ds = xr.Dataset(
            {"B": (["A"], [1.0, 2.0, 3.0]), "C": (["A"], [4.0, 5.0, 6.0])},
            coords={"A": [7.0, 8.0, 9.0]},
        )
        da = xr.DataArray([1.0, 2.0, 3.0], coords={"A": [7.0, 8.0, 9.0]}, name="B")
        loader = ArrayLoader(filename=test_file)

        ds.to_netcdf(test_file)
        assert_identically_close(loader.load(var_name="B"), da)

        da.to_netcdf(test_file)
        assert_identically_close(loader.load(), da)

    def test_load_altitude(self):
        da = ArrayLoader.load_altitude("franxl1s100")
        assert da.name == "franxl1s100"


class TestMaskLoader:
    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_load(self, test_file):
        # Test when ids is a string
        ds = xr.Dataset(
            {
                "A": (
                    ["id", "longitude_glob05", "latitude_monde"],
                    [[[1.0, 0.0], [0.0, 3.0]], [[1.0, 0.0], [0.0, 1.0]]],
                ),
                "B": (
                    ["id", "longitude_glob05", "latitude_monde"],
                    [[[True, True], [True, False]], [[False, True], [False, False]]],
                ),
                "areaName": (["id"], ["area1", "area2"]),
                "altAreaName": (["id"], ["altArea1", "altArea2"]),
                "areaType": (["id"], ["areatype1", "areatype2"]),
            },
            coords={
                "id": ["id_1", "id_2"],
                "longitude_glob05": [15.0, 16.0],
                "latitude_monde": [17.0, 18.0],
            },
        )
        ds.to_netcdf(test_file)

        loader = MaskLoader(filename=test_file, grid_name="A")
        assert_identically_close(
            loader.load(ids="id_1"),
            xr.DataArray(
                [[[1.0, np.nan], [np.nan, 1.0]]],
                coords={
                    "id": ["id_1"],
                    "longitude": [15.0, 16.0],
                    "latitude": [17.0, 18.0],
                    "areaName": (["id"], ["area1"]),
                    "altAreaName": (["id"], ["altArea1"]),
                    "areaType": (["id"], ["areatype1"]),
                },
                dims=["id", "longitude", "latitude"],
                name="A",
            ),
        )

        # Test when ids is a list
        loader.grid_name = "B"
        assert_identically_close(
            loader.load(ids=["id_2"]),
            xr.DataArray(
                [[[np.nan, 1.0], [np.nan, np.nan]]],
                coords={
                    "id": ["id_2"],
                    "longitude": [15.0, 16.0],
                    "latitude": [17.0, 18.0],
                    "areaName": (["id"], ["area2"]),
                    "altAreaName": (["id"], ["altArea2"]),
                    "areaType": (["id"], ["areatype2"]),
                },
                dims=["id", "longitude", "latitude"],
                name="B",
            ),
        )

        # Test without grid_name and ids
        loader.grid_name = None
        da = xr.DataArray(
            [[[1.0, 0.0], [0.0, 3.0]], [[True, False], [False, True]]],
            coords={
                "id": ["id_1", "id_2"],
                "longitude_glob05": [15.0, 16.0],
                "latitude_monde": [17.0, 18.0],
            },
        )
        da.to_netcdf(test_file)
        assert_identically_close(
            loader.load(),
            xr.DataArray(
                [[[1.0, np.nan], [np.nan, 1.0]], [[1.0, np.nan], [np.nan, 1.0]]],
                coords={
                    "id": ["id_1", "id_2"],
                    "longitude": [15.0, 16.0],
                    "latitude": [17.0, 18.0],
                },
            ),
        )

        # Test without areaName and areaType
        ds = xr.Dataset(
            {
                "A": (
                    ["id", "longitude_glob05", "latitude_monde"],
                    [[[1.0, 0.0], [0.0, 3.0]], [[1.0, 0.0], [0.0, 1.0]]],
                )
            },
            coords={
                "id": ["id_1", "id_2"],
                "longitude_glob05": [15.0, 16.0],
                "latitude_monde": [17.0, 18.0],
            },
        )
        ds.to_netcdf(test_file)

        loader = MaskLoader(filename=test_file, grid_name="A")

        expected = xr.DataArray(
            [[[1.0, np.nan], [np.nan, 1.0]]],
            coords={
                "id": ["id_1"],
                "longitude": [15.0, 16.0],
                "latitude": [17.0, 18.0],
                "areaName": (["id"], ["unknown"]),
                "altAreaName": (["id"], ["unknown"]),
                "areaType": (["id"], ["unknown"]),
            },
            dims=["id", "longitude", "latitude"],
            name="A",
        )
        assert_identically_close(loader.load(ids="id_1"), expected)
