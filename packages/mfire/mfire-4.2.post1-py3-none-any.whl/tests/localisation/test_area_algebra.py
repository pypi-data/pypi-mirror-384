import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.localisation.area_algebra import compute_iol, compute_iou, compute_iou_left
from tests.functions_test import assert_identically_close


class TestAreaAlgebraFunctions:
    def test_compute_iou(self):
        left_da = xr.DataArray([[1, 1], [0, 1]], coords={"lon": [1, 2], "lat": [3, 4]})
        right_da = xr.DataArray(
            [[[1, 0], [1, 0]], [[0, 1], [0, 1]]],
            coords={"id": ["a", "b"], "lon": [1, 2], "lat": [3, 4]},
        )
        assert_identically_close(
            compute_iou(left_da, right_da, dims=("lon", "lat")),
            xr.DataArray([0.25, 2 / 3], coords={"id": ["a", "b"]}),
        )

    def test_compute_iou_left(self):
        left_da = xr.DataArray([[1, 1], [0, 1]], coords={"lon": [1, 2], "lat": [3, 4]})
        right_da = xr.DataArray(
            [[[1, 0], [1, 0]], [[0, 1], [0, 1]]],
            coords={"id": ["a", "b"], "lon": [1, 2], "lat": [3, 4]},
        )
        assert_identically_close(
            compute_iou_left(left_da, right_da, dims=("lon", "lat")),
            xr.DataArray([1 / 3, 2 / 3], coords={"id": ["a", "b"]}),
        )

    @pytest.mark.parametrize(
        "phenomenon_map,geos_descriptive,expected",
        [
            # a is excluded by IoL since IoL < 25% and IoU < 20%
            ([[0, 0, 0], [1, 0, 0], [0, 0, 0]], ["a", "b", "c"], (["a"], True)),
            # a is included since IoL(=0.25) >= 25%
            ([[0, 0, 0], [1, 1, 0], [0, 0, 0]], ["a", "b", "c"], (["a"], False)),
            # check the exclusion with a and b
            ([[1, 1, 0], [0, 0, 0], [0, 0, 0]], ["a", "b", "c"], (["b"], False)),
            ([[1, 1, 0], [1, 1, 0], [0, 0, 0]], ["a", "b", "c"], (["a"], False)),
            ([[1, 0, 0], [0, 0, 0], [0, 0, 0]], ["a", "b", "c"], (["b"], False)),
            # several locations (locations are stored according to proportion of
            # phenomenon)
            ([[0, 0, 1], [1, 1, 1], [0, 0, 0]], ["a", "b", "c"], (["c", "a"], False)),
            ([[1, 0, 1], [0, 0, 1], [0, 0, 1]], ["a", "b", "c"], (["c", "b"], False)),
            # No geos descriptive
            ([[0, 0, 1], [1, 1, 1], [0, 0, 0]], [], (None, False)),
            # No geos descriptive touching phenom
            ([[0, 0, 1], [0, 0, 0], [0, 0, 0]], ["d"], (None, False)),
        ],
    )
    def test_compute_iol(self, phenomenon_map, geos_descriptive, expected):
        lat = [30, 31, 32]
        lon = [40, 41, 42]
        area_ids = ["a", "b", "c", "d"]

        geos_descriptive = xr.DataArray(
            np.array(
                [
                    [[1, 1, 0], [1, 1, 0], [1, 1, 0]],  # area "a"
                    [[1, 1, 0], [0, 0, 0], [0, 0, 0]],  # area "b"
                    [[0, 0, 1], [0, 0, 1], [0, 0, 1]],  # area "c"
                    [[0, 0, 0], [0, 0, 0], [1, 0, 0]],  # area "d"
                ]
            ),
            coords={"id": area_ids, "latitude": lat, "longitude": lon},
        ).sel(id=geos_descriptive)
        phenomenon_map = xr.DataArray(
            [phenomenon_map],
            coords={"id": ["id_axis"], "latitude": lat, "longitude": lon},
        )

        result = compute_iol(geos_descriptive, phenomenon_map)
        if result[0] is not None:
            result = (list(result[0].id.data), result[1])

        assert result == expected
