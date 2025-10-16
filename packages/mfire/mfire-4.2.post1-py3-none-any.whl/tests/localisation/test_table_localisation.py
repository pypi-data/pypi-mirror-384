import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.utils.date import Datetime
from tests.functions_test import assert_identically_close
from tests.localisation.factories import (
    SpatialLocalisationFactory,
    TableLocalisationFactory,
)


class TestTableLocalisation:
    def test_init(self):
        a = xr.DataArray([1])
        table = TableLocalisationFactory(infos=a)
        table.infos *= 2
        assert_identically_close(a, xr.DataArray([1]))

    def test_name(self):
        # Basic test
        table = TableLocalisationFactory(
            infos=xr.DataArray(
                None,
                coords={
                    "period": [Datetime(2023, 3, 1), Datetime(2023, 3, 2)],
                    "raw": ["2", "3"],
                },
                dims=["period", "raw"],
            )
        )
        assert table.name == "P2_2_3"

        # Default localisation test
        table = TableLocalisationFactory(
            infos=xr.DataArray(
                None,
                coords={"period": [Datetime(2023, 3, 1)], "raw": ["0", "2"]},
                dims=["period", "raw"],
            ),
            spatial_localisation=SpatialLocalisationFactory(default_localisation=True),
        )
        assert table.name == "P1_2_default_localisation"

    @pytest.mark.parametrize(
        "ids",
        [  # One id
            ["id1"],
            ["idOtherType"],
            # One id with renaming
            ["id100_200"],
            ["id900_1000"],
            # Two ids with same type
            ["id1", "id2"],
            ["id1", "idOtherType"],
            ["id100_200", "id900_1000"],
            # All domain
            ["id1", "id2", "idOtherType"],
            ["id1", "id2", "id100_200", "id900_1000"],
        ],
    )
    def test_merge_similar_areas(self, ids, assert_equals_result):
        lat, lon = [30, 31], [40, 41]
        areas_id = ["id1", "id2", "id100_200", "id900_1000", "idOtherType"]
        areas_name = [
            "Area1",
            "Area2",
            "entre 100 m et 200 m",
            "entre 900 m et 1000 m",
            "AreaOtherType",
        ]
        areas_type = 2 * ["axis"] + 2 * ["Altitude"] + ["other_type"]

        table = TableLocalisationFactory(
            spatial_localisation=SpatialLocalisationFactory(
                domain=xr.DataArray(
                    [[1.0, 1.0], [1.0, 1.0]],
                    coords={
                        "latitude": lat,
                        "longitude": lon,
                        "areaName": "DomainName",
                        "altAreaName": "DomainName",
                    },
                    dims=["latitude", "longitude"],
                ),
                areas=xr.DataArray(
                    [
                        # axis1
                        [[1.0, np.nan], [np.nan, np.nan]],
                        # axis2
                        [[np.nan, 1.0], [np.nan, np.nan]],
                        # id100_200
                        [[np.nan, np.nan], [1.0, 1.0]],
                        # id900_1000
                        [[np.nan, np.nan], [1.0, np.nan]],
                        # idOtherType
                        [[np.nan, np.nan], [np.nan, 1.0]],
                    ],
                    coords={
                        "id": areas_id,
                        "latitude": lat,
                        "longitude": lon,
                        "areaName": (["id"], areas_name),
                        "altAreaName": (["id"], areas_name),
                        "areaType": (["id"], areas_type),
                    },
                    dims=["id", "latitude", "longitude"],
                ),
            )
        )

        da = xr.DataArray(
            coords={"id": ids, "raw": (["id"], [1] * len(ids))}, dims=["id"]
        )
        assert_equals_result(table._merge_similar_areas(da).to_dict())

    def test_squeeze_empty_period(self):
        areas = xr.DataArray([...], coords={"id": ["id_1"]}, dims=["id"])

        # Empty periods at left and right
        periods = [
            "20190727T06_to_20190727T09",
            "20190727T10_to_20190727T13",
            "20190727T14_to_20190727T17",
        ]

        table = TableLocalisationFactory(
            infos=xr.DataArray(
                [[0.0, 1.0, 0.0]], coords={"id": ["id_1"], "period": periods}
            ),
            spatial_localisation=SpatialLocalisationFactory(areas=areas),
        )
        table._squeeze_empty_period()
        assert_identically_close(
            table.infos,
            xr.DataArray(
                [[1.0]],
                coords={"id": ["id_1"], "period": ["20190727T10_to_20190727T13"]},
                dims=["id", "period"],
            ),
        )

        # Only empty periods
        periods = [
            "20190727T06_to_20190727T09",
            "20190727T10_to_20190727T13",
            "20190727T14_to_20190727T17",
        ]

        table = TableLocalisationFactory(
            infos=xr.DataArray(
                [[1.0, 1.0, 1.0]], coords={"id": ["id_1"], "period": periods}
            ),
            spatial_localisation=SpatialLocalisationFactory(areas=areas),
        )
        table._squeeze_empty_period()
        assert_identically_close(
            table.infos,
            xr.DataArray(
                [[1.0, 1.0, 1.0]],
                coords={
                    "id": ["id_1"],
                    "period": [
                        "20190727T06_to_20190727T09",
                        "20190727T10_to_20190727T13",
                        "20190727T14_to_20190727T17",
                    ],
                },
                dims=["id", "period"],
            ),
        )

    def test_clean_similar_period(self):
        periods = [
            "20190727T06_to_20190727T09",
            "20190727T10_to_20190727T13",
            "20190727T14_to_20190727T17",
        ]
        table = TableLocalisationFactory(
            infos=xr.DataArray(
                [[1.0, 1.0, 2.0]], coords={"id": ["id_1"], "period": periods}
            ),
            spatial_localisation=SpatialLocalisationFactory(
                areas=xr.DataArray([...], coords={"id": ["id_1"]}, dims=["id"])
            ),
        )
        assert table._clean_similar_period() is True
        assert_identically_close(
            table.infos,
            xr.DataArray(
                [[1.0, 2.0]],
                coords={
                    "id": ["id_1"],
                    "period": [
                        "20190727T06_to_20190727T09_+_20190727T10_to_20190727T13",
                        "20190727T14_to_20190727T17",
                    ],
                },
                dims=["id", "period"],
            ),
        )

    def test_clean_period_with_same_name(self):
        spatial_loc = SpatialLocalisationFactory(
            areas=xr.DataArray([...], coords={"id": ["id_1"]}, dims=["id"])
        )

        # Without error
        table = TableLocalisationFactory(
            infos=xr.DataArray(
                [[1.0, 2.0, 3.0]],
                coords={
                    "id": ["id_1"],
                    "period": [
                        "20230301T06_to_20230301T09",
                        "20230301T07_to_20230301T10",
                        "20230301T14_to_20230301T17",
                    ],
                },
                name="da",
            ),
            spatial_localisation=spatial_loc,
        )
        assert table._clean_period_with_same_name() is True
        assert_identically_close(
            # dims can be reordered by merging operation
            table.infos.transpose("id", "period"),
            xr.DataArray(
                [[2.0, 3.0]],
                coords={
                    "id": ["id_1"],
                    "period": [
                        "20230301T06_to_20230301T10",
                        "20230301T14_to_20230301T17",
                    ],
                },
                dims=["id", "period"],
                name="da",
            ),
        )

        # With error in the date
        table = TableLocalisationFactory(
            infos=xr.DataArray(
                [[1.0, 2.0, 3.0]],
                coords={
                    "id": ["id_1"],
                    "period": [
                        "20230301T06_to_20230301T09",
                        "20230301T07_to_20230301T10",
                        "20230301T14_to_truc",
                    ],
                },
                name="da",
            ),
            spatial_localisation=spatial_loc,
        )
        assert table._clean_period_with_same_name() is False
        assert_identically_close(
            table.infos,
            xr.DataArray(
                [[1.0, 2.0, 3.0]],
                coords={
                    "id": ["id_1"],
                    "period": [
                        "20230301T06_to_20230301T09",
                        "20230301T07_to_20230301T10",
                        "20230301T14_to_truc",
                    ],
                },
                dims=["id", "period"],
                name="da",
            ),
        )  # The table_localisation hasn't changed

    @pytest.mark.parametrize(
        "ids",
        [
            ["id1"],
            ["id100_200"],
            ["id900_1000"],
            ["idOtherType"],
            ["id1", "id2"],
            ["id100_200", "id900_1000"],
            ["id1", "idOtherType"],
            ["id1", "id2", "id900_1000"],
            ["id1", "id2", "idOtherType"],
        ],
    )
    def test_compute(self, ids, assert_equals_result):
        lat, lon = [30, 31], [40, 41]
        all_ids = ["id1", "id2", "id100_200", "id900_1000", "idOtherType"]
        areas_name = [
            "Area1",
            "Area2",
            "entre 100 m et 200 m",
            "entre 900 m et 1000 m",
            "AreaOtherType",
        ]
        areas_type = 2 * ["axis"] + 2 * ["Altitude"] + ["other_type"]

        periods = [
            "20190727T06_to_20190727T09",
            "20190727T10_to_20190727T13",
            "20190727T14_to_20190727T17",
        ]

        spatial_loc = SpatialLocalisationFactory(
            domain=xr.DataArray(
                [[1.0, 1.0], [1.0, 1.0]],
                coords={
                    "latitude": lat,
                    "longitude": lon,
                    "areaName": "DomainName",
                    "altAreaName": "DomainName",
                },
                dims=["latitude", "longitude"],
                name="domain",
            ),
            areas=xr.DataArray(
                [
                    # axis1
                    [[1.0, np.nan], [np.nan, np.nan]],
                    # axis2
                    [[np.nan, 1.0], [np.nan, np.nan]],
                    # id100_200
                    [[np.nan, np.nan], [1.0, 1.0]],
                    # id900_1000
                    [[np.nan, np.nan], [1.0, np.nan]],
                    # idOtherType
                    [[np.nan, np.nan], [np.nan, 1.0]],
                ],
                coords={
                    "id": all_ids,
                    "latitude": lat,
                    "longitude": lon,
                    "areaName": (["id"], areas_name),
                    "altAreaName": (["id"], areas_name),
                    "areaType": (["id"], areas_type),
                },
                dims=["id", "latitude", "longitude"],
                name="areas",
            ),
        )
        table = TableLocalisationFactory(
            spatial_localisation=spatial_loc,
            infos=xr.DataArray(
                [[1, 1, 0, 1, 1], [0, 1, 1, 1, 1], [1, 0, 1, 0, 1]],
                coords={
                    "period": periods,
                    "id": all_ids,
                    "areaName": (["id"], areas_name),
                    "areaType": (["id"], areas_type),
                },
                dims=["period", "id"],
                name="elt",
            ).sel(id=ids),
        ).compute()

        assert_equals_result(
            {
                "table_localisation": table.table,
                "data": table.infos.to_dict(),
                "name": table.name,
            }
        )
