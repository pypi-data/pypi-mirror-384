from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.composite.geo import AltitudeComposite
from mfire.settings import ALT_MAX, ALT_MIN
from tests.composite.factories import AltitudeCompositeFactory, GeoCompositeFactory
from tests.functions_test import assert_identically_close


class TestGeoComposite:
    def test_bounds(self):
        lon, lat = [30, 31, 32], [40, 41, 42]
        ids = ["id1", "id2", "id3"]

        assert GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                np.random.rand(3, 3, 3),
                coords={"id": ids, "longitude": lon, "latitude": lat},
            ),
            mask_id=ids,
        ).bounds == (30, 40, 32, 42)

    @patch("mfire.utils.xr.MaskLoader.load")
    def test_compute(self, mock_func):
        mock_func.side_effect = lambda *args, **kwargs: (args, kwargs)
        geo = GeoCompositeFactory()
        assert geo.compute() == ((), {"ids": "mask_id"})

        geo = GeoCompositeFactory(mask_id=["mask_id"])
        assert geo.compute() == ((), {"ids": ["mask_id"]})

    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_mask_da(self, test_file):
        ds = xr.Dataset(
            {
                "A": (
                    ["id", "longitude_glob05", "latitude_monde"],
                    [[[1.0, 0.0], [0.0, 3.0]]],
                ),
                "B": (
                    ["id", "longitude_glob05", "latitude_monde"],
                    [[[True, True], [True, False]]],
                ),
                "areaName": (["id"], ["area1"]),
                "altAreaName": (["id"], ["altArea1"]),
                "areaType": (["id"], ["areatype1"]),
            },
            coords={
                "id": ["id"],
                "longitude_glob05": [15.0, 16.0],
                "latitude_monde": [17.0, 18.0],
            },
        )
        ds.to_netcdf(test_file)

        geo = GeoCompositeFactory(file=test_file, grid_name="A")
        assert_identically_close(
            geo.mask_da,
            xr.DataArray(
                [[[1.0, np.nan], [np.nan, 1.0]]],
                coords={
                    "id": ["id"],
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

        geo = GeoCompositeFactory(file=test_file, grid_name="B")
        assert_identically_close(
            geo.mask_da,
            xr.DataArray(
                [[[1.0, 1.0], [1.0, np.nan]]],
                coords={
                    "id": ["id"],
                    "longitude": [15.0, 16.0],
                    "latitude": [17.0, 18.0],
                    "areaName": (["id"], ["area1"]),
                    "altAreaName": (["id"], ["altArea1"]),
                    "areaType": (["id"], ["areatype1"]),
                },
                dims=["id", "longitude", "latitude"],
                name="B",
            ),
        )

    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_all_axis(self, test_file):
        ds = xr.Dataset(
            {
                "A": (["id", "longitude", "latitude"], [[[1.0]], [[1.0]]]),
                "areaName": (["id"], ["area1", "area2"]),
                "altAreaName": (["id"], ["altArea1", "altArea2"]),
                "areaType": (["id"], ["areatype1", "Axis"]),
            },
            coords={"id": ["id1", "id2"], "longitude": [15.0], "latitude": [17.0]},
        )
        ds.to_netcdf(test_file)

        geo = GeoCompositeFactory(file=test_file, grid_name="A")
        assert_identically_close(
            geo.all_axis,
            xr.DataArray(
                [[[1.0]]],
                coords={
                    "id": ["id2"],
                    "longitude": [15.0],
                    "latitude": [17.0],
                    "areaName": (["id"], ["area2"]),
                    "altAreaName": (["id"], ["altArea2"]),
                    "areaType": (["id"], ["Axis"]),
                },
                dims=["id", "longitude", "latitude"],
                name="A",
            ),
        )

    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_all_sub_areas(self, test_file):
        ds = xr.Dataset(
            {
                "A": (
                    ["id", "latitude", "longitude"],
                    [[[1.0, 1.0]], [[1.0, 0.0]], [[0.0, 1.0]]],
                ),
                "areaType": (["id"], ["Axis", "Axis", "Axis"]),
            },
            coords={
                "id": ["id1", "id2", "id3"],
                "longitude": [15.0, 16.0],
                "latitude": [17.0],
            },
        )
        ds.to_netcdf(test_file)

        geo = GeoCompositeFactory(file=test_file, grid_name="A")
        assert_identically_close(geo.all_sub_areas("id1"), ["id1", "id2", "id3"])
        assert_identically_close(geo.all_sub_areas("id2"), ["id2"])
        assert_identically_close(geo.all_sub_areas("id3"), ["id3"])


class TestAltitudeComposite:
    def test_init_alt_min(self):
        assert AltitudeCompositeFactory(alt_min=None).alt_min == ALT_MIN

    def test_init_alt_max(self):
        assert AltitudeCompositeFactory(alt_max=None).alt_max == ALT_MAX

    def test_default_init(self):
        with pytest.raises(FileNotFoundError, match="No such file test_file."):
            AltitudeCompositeFactory(filename=Path("test_file"))

    def test_from_grid_name(self):
        altitude = AltitudeComposite.from_grid_name(
            "franxl1s100", alt_min=15, alt_max=80
        )
        assert str(altitude.filename).endswith("franxl1s100.nc")
        assert altitude.alt_min == 15
        assert altitude.alt_max == 80

    @pytest.mark.parametrize("test_file", [{"extension": "nc"}], indirect=True)
    def test_compute(self, test_file):
        lon, lat = [30], [40, 41, 42]
        da = xr.DataArray([[125, 150, 175]], coords={"longitude": lon, "latitude": lat})
        da.to_netcdf(test_file)

        altitude = AltitudeCompositeFactory(
            filename=test_file, alt_min=130, alt_max=160
        )

        result = altitude.compute()
        expected = xr.DataArray(
            [[np.nan, 150, np.nan]], coords={"longitude": lon, "latitude": lat}
        )
        assert_identically_close(result, expected)
