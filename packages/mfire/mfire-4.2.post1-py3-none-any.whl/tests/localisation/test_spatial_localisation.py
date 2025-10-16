import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.composite.aggregation import AggregationType
from mfire.composite.event import Category, Threshold
from mfire.composite.level import LocalisationConfig
from mfire.composite.operator import ComparisonOperator
from mfire.utils.date import Datetime
from mfire.utils.exception import LocalisationError, LocalisationWarning
from tests.composite.factories import (
    AggregationFactory,
    AltitudeCompositeFactory,
    EventCompositeFactory,
    FieldCompositeFactory,
    GeoCompositeFactory,
    LevelCompositeFactory,
    RiskComponentCompositeFactory,
)
from tests.functions_test import assert_identically_close
from tests.localisation.factories import SpatialLocalisationFactory


class TestSpatialLocalisation:
    def test_covers_domain(self):
        areas = xr.DataArray(
            [[[i == j for j in range(10)]] for i in range(9)],
            coords={
                "id": [f"id_{i+1}" for i in range(9)],
                "longitude": [10],
                "latitude": [40 + i for i in range(10)],
            },
        )
        domain = xr.DataArray(
            [[[1] * 10]],
            coords={
                "id": ["axis"],
                "longitude": [10],
                "latitude": [40 + i for i in range(10)],
            },
        )

        loc = SpatialLocalisationFactory(areas=areas, domain=domain)
        assert loc.covers_domain

        loc = SpatialLocalisationFactory(areas=areas.isel(id=range(8)), domain=domain)
        assert not loc.covers_domain

    def test_completed_areas(self):
        # Test when all cuts were done => we don't change areas
        areas = xr.DataArray(coords={"id": ["id1", "id2", "id3"]}, dims=["id"])
        loc = SpatialLocalisationFactory(areas=areas, covers_domain_factory=True)
        assert_identically_close(loc.completed_areas, areas)

        areas = xr.DataArray(
            coords={
                "id": ["id1"],
                "areaName": (["id"], ["area"]),
                "altAreaName": (["id"], ["alt_area"]),
                "areaType": (["id"], ["area_type"]),
            },
            dims=["id"],
        )

        # Covers domain
        loc = SpatialLocalisationFactory(areas=areas, covers_domain_factory=True)
        assert_identically_close(loc.completed_areas, areas)

        # No domain covering
        loc = SpatialLocalisationFactory(areas=areas, covers_domain_factory=False)
        assert_identically_close(
            loc.completed_areas,
            xr.DataArray(
                coords={
                    "id": ["id1", "zero"],
                    "areaName": (["id"], ["area", "Zone Zero"]),
                    "altAreaName": (["id"], ["alt_area", "Zone Zero"]),
                    "areaType": (["id"], ["area_type", ""]),
                },
                dims=["id"],
            ),
        )

    def test_risk_level(self):
        # Empty risk
        loc = SpatialLocalisationFactory()
        assert loc.risk_level == 0

        # Non-empty risk
        compo = RiskComponentCompositeFactory(
            data=xr.Dataset({"A": ("B", [...])}, coords={"B": [...]}),
            final_risk_da_factory=xr.DataArray(
                [[1, 2], [4, 5]], coords={"id": ["id_1", "id_2"], "A": [..., ...]}
            ),
        )
        assert SpatialLocalisationFactory(parent=compo, geo_id="id_1").risk_level == 2
        assert SpatialLocalisationFactory(parent=compo, geo_id="id_2").risk_level == 5

    @pytest.mark.parametrize("risk_level", [1, 2, 3])
    def test_localised_risk_ds(self, risk_level, assert_equals_result):
        valid_time = [Datetime(2023, 3, 1).as_np_dt64, Datetime(2023, 3, 2).as_np_dt64]
        lon, lat = [15], [30, 31, 32, 33]

        altitude = AltitudeCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[10, np.nan, 20, 30]], coords={"longitude": lon, "latitude": lat}
            )
        )

        geos1 = GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[[False, True, True, True]]],
                coords={"id": ["id"], "longitude": lon, "latitude": lat},
            )
        )
        geos2 = GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[[False, True, False, True]]],
                coords={"id": ["id"], "longitude": lon, "latitude": lat},
            ),
            grid_name=None,
        )

        field1 = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [
                    [
                        [
                            [1000, 2000],  # masked values by geos
                            [1500, 3000],  # masked values by altitude
                            [1.7, 1.9],  # isn't risked with threshold and geos
                            [1.8, 1.9],
                        ]
                    ]
                ],
                coords={
                    "id": ["id"],
                    "longitude": lon,
                    "latitude": lat,
                    "valid_time": valid_time,
                },
                attrs={"units": "cm"},
                name="NEIPOT24__SOL",
            )
        )
        field2 = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [
                    [
                        [
                            [1500, 1700],  # masked values by geos
                            [2000, 2500],  # masked values by altitude
                            [1.6, 1.75],  # isn't risked with threshold
                            [1.9, 1.8],
                        ]
                    ]
                ],
                coords={
                    "id": ["id"],
                    "longitude": lon,
                    "latitude": lat,
                    "valid_time": valid_time,
                },
                attrs={"units": "cm"},
                name="NEIPOT1__SOL",
            )
        )
        evt1 = EventCompositeFactory(
            field=field1,
            geos=geos1,
            altitude=altitude,
            category=Category.QUANTITATIVE,
            plain=Threshold(
                threshold=2.0, comparison_op=ComparisonOperator.SUPEGAL, units="cm"
            ),
        )
        evt2 = EventCompositeFactory(
            field=field1,
            geos=geos2,
            altitude=altitude,
            category=Category.QUANTITATIVE,
            plain=Threshold(
                threshold=15, comparison_op=ComparisonOperator.SUPEGAL, units="mm"
            ),
        )
        evt3 = EventCompositeFactory(
            field=field2,
            geos=geos2,
            altitude=altitude,
            category=Category.QUANTITATIVE,
            plain=Threshold(
                threshold=2.0, comparison_op=ComparisonOperator.SUPEGAL, units="cm"
            ),
            mountain=Threshold(
                threshold=12, comparison_op=ComparisonOperator.SUPEGAL, units="mm"
            ),
            mountain_altitude=15,
        )

        lvl1 = LevelCompositeFactory(
            level=1,
            events=[evt1, evt2],
            logical_op_list=["or"],
            aggregation_type=AggregationType.DOWN_STREAM,
            aggregation=AggregationFactory(),
        )
        lvl2 = LevelCompositeFactory(
            level=2,
            events=[evt1, evt2],
            logical_op_list=["and"],
            aggregation_type=AggregationType.DOWN_STREAM,
            aggregation=AggregationFactory(),
        )
        lvl3 = LevelCompositeFactory(
            level=3,
            events=[evt3],
            aggregation_type=AggregationType.DOWN_STREAM,
            aggregation=AggregationFactory(),
        )
        loc = SpatialLocalisationFactory(
            risk_ds=xr.Dataset(coords={"valid_time": valid_time}),
            parent=RiskComponentCompositeFactory(levels=[lvl1, lvl2, lvl3]),
            risk_level_factory=risk_level,
            geo_id="id",
            areas=xr.DataArray(
                [[[False, True, True, True]]],
                coords={"id": ["id"], "longitude": lon, "latitude": lat},
            ),
            domain=xr.DataArray(
                [[True, True, True, True]], coords={"longitude": lon, "latitude": lat}
            ),
        )

        assert_equals_result(loc.localised_risk_ds.to_dict())

    @pytest.mark.parametrize(
        "risk_axis,risk_z1,risk_z2,expected",
        [
            # No modification
            (True, True, True, [True, True]),
            (True, True, False, [True, False]),
            (True, False, True, [False, True]),
            # Test when no risk in axis but risk in areas
            (False, True, True, [False, False]),
            # Test when risk in axis but no risk in areas
            (True, False, False, [False, True]),  # 2nd area has best risk density
        ],
    )
    def test_risk_areas(self, risk_axis, risk_z1, risk_z2, expected):
        ids = ["id1", "id2"]
        valid_time = [Datetime(2023, 3, 1).as_np_dt64]

        localised_risk_ds = xr.Dataset(
            {
                "occurrence": (
                    ["risk_level", "valid_time", "id"],
                    [[[risk_z1, risk_z2]]],
                ),
                "risk_density": (["risk_level", "valid_time", "id"], [[[0.4, 0.6]]]),
            },
            coords={
                "id": ids,
                "valid_time": valid_time,
                "areaName": (["id"], [..., ...]),
                "altAreaName": (["id"], [..., ...]),
                "areaType": (["id"], [..., ...]),
                "risk_level": [3],
            },
        )
        risk_ds = xr.Dataset(
            {"occurrence": (["id", "valid_time"], [[risk_axis]])},
            coords={"id": ["id_axis"], "valid_time": valid_time},
        )

        loc = SpatialLocalisationFactory(
            risk_ds=risk_ds,
            localised_risk_ds_factory=localised_risk_ds,
            covers_domain_factory=False,
        )

        assert_identically_close(
            loc.risk_areas,
            xr.DataArray(
                [expected + [False]],
                coords={
                    "valid_time": valid_time,
                    "id": ids + ["zero"],
                    "areaName": (["id"], [..., ..., "Zone Zero"]),
                    "altAreaName": (["id"], [..., ..., "Zone Zero"]),
                    "areaType": (["id"], [..., ..., ""]),
                    "risk_level": 3,
                },
                dims=["valid_time", "id"],
                name="occurrence",
            ),
        )

    @pytest.mark.parametrize(
        "compass,altitude,spatial_risk",
        [
            # Test simple area
            (True, True, [[1.0, 0.0, 0.0, 0.0, 0.0, 0.0]]),
            # Test combined areas
            (True, True, [[1.0, 1.0, 1.0, 0.0, 0.0, 0.0]]),
            # Test compass
            (True, True, [[1.0, 1.0, 0.0, 1.0, 0.0, 0.0]]),
            (False, True, [[1.0, 1.0, 0.0, 1.0, 0.0, 0.0]]),
            # Test altitude
            (False, True, [[1.0, 1.0, 0.0, 0.0, 1.0, 0.0]]),
            (False, False, [[1.0, 1.0, 0.0, 0.0, 1.0, 0.0]]),
        ],
    )
    def test_compute_domain_and_areas(
        self, compass, altitude, spatial_risk, assert_equals_result
    ):
        valid_time = [Datetime(2023, 3, 1)]
        ids = ["iddomain" + id for id in ["", "_id1", "_id2", "_id3", "_id4"]]
        lon, lat = [40], [30, 31, 32, 33, 34, 35]
        geos_da = xr.DataArray(
            [
                [[1.0, 1.0, 1.0, 1.0, 1.0, 1.0]],
                [[1.0, 1.0, np.nan, np.nan, np.nan, np.nan]],
                [[np.nan, np.nan, 1.0, np.nan, np.nan, np.nan]],
                [[np.nan, np.nan, np.nan, 1.0, np.nan, np.nan]],
                [[np.nan, np.nan, np.nan, np.nan, 1.0, np.nan]],
            ],
            coords={
                "id": ids,
                "longitude": lon,
                "latitude": lat,
                "areaName": (["id"], ["domain", "area1", "area2", "area3", "area4"]),
                "altAreaName": (
                    ["id"],
                    ["altDomain", "altArea1", "altArea2", "altArea3", "altArea4"],
                ),
                "areaType": (
                    ["id"],
                    ["domain", "type1", "type2", "compass", "Altitude"],
                ),
            },
            dims=["id", "longitude", "latitude"],
        )
        level = LevelCompositeFactory(
            compute_factory=xr.Dataset,  # to avoid computing
            events=[
                EventCompositeFactory(
                    geos=GeoCompositeFactory(compute_factory=lambda: geos_da)
                )
            ],
            localisation=LocalisationConfig(
                compass_split=compass, altitude_split=altitude
            ),
            spatial_risk_da_factory=xr.DataArray(
                [[spatial_risk]],
                coords={
                    "id": [ids[0]],
                    "valid_time": valid_time,
                    "longitude": lon,
                    "latitude": lat,
                },
            ),
        )

        loc = SpatialLocalisationFactory(geo_id=ids[0])
        loc._compute_domain_and_areas(level=level, periods=valid_time)

        assert_identically_close(loc.domain, geos_da.isel(id=0))
        assert_equals_result(loc.areas.to_dict())

    def test_compute_fails_with_risk_level_0(self):
        with pytest.raises(
            LocalisationWarning,
            match="RiskLocalisation is only possible for risk level > 0.",
        ):
            SpatialLocalisationFactory().compute()

    def test_compute_fails_with_upstream(self):
        valid_time = [Datetime(2023, 3, 1).as_np_dt64]
        risk_compo = RiskComponentCompositeFactory(
            final_risk_da_factory=xr.DataArray(
                [[1]], coords={"id": ["geo_id"], "valid_time": valid_time}
            ),
            levels=[LevelCompositeFactory(level=1, cover_period_factory=valid_time)],
        )

        with pytest.raises(
            LocalisationWarning,
            match="RiskLocalisation is only possible for downstream risk.",
        ):
            SpatialLocalisationFactory(
                parent=risk_compo, risk_level_factory=1
            ).compute()

    def test_compute_fails_with_mask_not_available(self):
        # With GeoComposite as geos
        valid_time = [Datetime(2023, 3, 1).as_np_dt64]
        risk_component = RiskComponentCompositeFactory(
            final_risk_da_factory=xr.DataArray(
                [[1]], coords={"id": ["geo_id"], "valid_time": valid_time}
            ),
            levels=[
                LevelCompositeFactory(
                    level=1,
                    cover_period_factory=valid_time,
                    aggregation_type=AggregationType.DOWN_STREAM,
                    aggregation=AggregationFactory(),
                )
            ],
        )
        with pytest.raises(
            LocalisationError, match="Mask with id 'geo_id' not available"
        ):
            SpatialLocalisationFactory(
                parent=risk_component, risk_level_factory=1
            ).compute()

        # With DataArray as geos
        valid_time = [Datetime(2023, 3, 1).as_np_dt64]
        risk_component = RiskComponentCompositeFactory(
            final_risk_da_factory=xr.DataArray(
                [[1]], coords={"id": ["geo_id"], "valid_time": valid_time}
            ),
            levels=[
                LevelCompositeFactory(
                    level=1,
                    events=[
                        EventCompositeFactory(
                            geos=xr.DataArray(coords={"id": ["id"]}, dims=["id"])
                        )
                    ],
                    cover_period_factory=valid_time,
                    aggregation_type=AggregationType.DOWN_STREAM,
                    aggregation=AggregationFactory(),
                )
            ],
        )
        with pytest.raises(
            LocalisationError, match="Mask with id 'geo_id' not available"
        ):
            SpatialLocalisationFactory(
                parent=risk_component, risk_level_factory=1
            ).compute()

    def test_compute_fails_without_area(self):
        ids = ["geo_id"]
        valid_time = [Datetime(2023, 3, 1).as_np_dt64]
        geos = GeoCompositeFactory(
            mask_id=ids,
            compute_factory=lambda: xr.DataArray(
                [...],
                coords={
                    "id": ids,
                    "areaName": (["id"], ["area1"]),
                    "altAreaName": (["id"], ["altArea1"]),
                    "areaType": (["id"], ["compass"]),
                },
                dims=["id"],
            ),
        )

        risk_component = RiskComponentCompositeFactory(
            final_risk_da_factory=xr.DataArray(
                [[1]], coords={"id": ["geo_id"], "valid_time": valid_time}
            ),
            levels=[
                LevelCompositeFactory(
                    level=1,
                    cover_period_factory=valid_time,
                    aggregation_type=AggregationType.DOWN_STREAM,
                    aggregation=AggregationFactory(),
                    events=[EventCompositeFactory(geos=geos)],
                    localisation=LocalisationConfig(compass_split=False),
                )
            ],
        )

        with pytest.raises(
            LocalisationWarning, match="There is no area for localisation process."
        ):
            SpatialLocalisationFactory(
                parent=risk_component, risk_level_factory=1
            ).compute()

    def test_compute_with_failed_localisation(self, assert_equals_result):
        valid_time = [Datetime(2023, 3, 1).as_np_dt64]
        lon, lat = [30], [40, 41]
        geos = GeoCompositeFactory(
            mask_id=["iddomain"],
            compute_factory=lambda: xr.DataArray(
                [[[1.0, 1.0]], [[1.0, 0.0]]],
                coords={
                    "id": ["iddomain", "iddomain_id1"],
                    "longitude": lon,
                    "latitude": lat,
                    "areaName": (["id"], ["Domain", "area1"]),
                    "altAreaName": (["id"], ["Domain", "altArea1"]),
                    "areaType": (["id"], ["domain", "type1"]),
                },
                dims=["id", "longitude", "latitude"],
            ),
        )

        compo = RiskComponentCompositeFactory(
            final_risk_da_factory=xr.DataArray(
                [[1]], coords={"id": ["iddomain"], "valid_time": valid_time}
            ),
            levels=[
                LevelCompositeFactory(
                    level=1,
                    compute_factory=xr.Dataset,  # to avoid computing
                    cover_period_factory=valid_time,
                    aggregation_type=AggregationType.DOWN_STREAM,
                    aggregation=AggregationFactory(),
                    events=[EventCompositeFactory(geos=geos)],
                    spatial_risk_da_factory=xr.DataArray(
                        [[[[0.0, 1.0]]]],
                        coords={
                            "id": ["iddomain"],
                            "valid_time": valid_time,
                            "longitude": lon,
                            "latitude": lat,
                            "areaName": (["id"], ["area1"]),
                            "altAreaName": (["id"], ["altArea1"]),
                            "areaType": (["id"], ["type1"]),
                        },
                        dims=["id", "valid_time", "longitude", "latitude"],
                    ),
                )
            ],
        )

        with pytest.raises(LocalisationWarning, match="There is no area selected."):
            SpatialLocalisationFactory(
                parent=compo, geo_id="iddomain", risk_level_factory=1
            ).compute()

    def test_compute(self, assert_equals_result):
        valid_time = [Datetime(2023, 3, 1).as_np_dt64]
        lon, lat = [30, 31], [40, 41]
        geos = GeoCompositeFactory(
            mask_id=["iddomain"],
            compute_factory=lambda: xr.DataArray(
                [[[1.0, 1.0], [1.0, 1.0]], [[1.0, 0.0], [1.0, 0.0]]],
                coords={
                    "id": ["iddomain", "iddomain_id1"],
                    "longitude": lon,
                    "latitude": lat,
                    "areaName": (["id"], ["domain", "area1"]),
                    "altAreaName": (["id"], ["altDomain", "altArea1"]),
                    "areaType": (["id"], ["domain", "type1"]),
                },
                dims=["id", "longitude", "latitude"],
            ),
        )

        risk_compo = RiskComponentCompositeFactory(
            final_risk_da_factory=xr.DataArray(
                [[1]], coords={"id": ["iddomain"], "valid_time": valid_time}
            ),
            levels=[
                LevelCompositeFactory(
                    level=1,
                    compute_factory=xr.Dataset,  # to avoid computing
                    cover_period_factory=valid_time,
                    aggregation_type=AggregationType.DOWN_STREAM,
                    aggregation=AggregationFactory(),
                    events=[EventCompositeFactory(geos=geos)],
                    spatial_risk_da_factory=xr.DataArray(
                        [[[[1.0, 0.0], [1.0, 0.0]]]],
                        coords={
                            "id": ["iddomain"],
                            "valid_time": valid_time,
                            "longitude": lon,
                            "latitude": lat,
                            "areaName": (["id"], ["area1"]),
                            "altAreaName": (["id"], ["altArea1"]),
                            "areaType": (["id"], ["type1"]),
                        },
                        dims=["id", "valid_time", "longitude", "latitude"],
                    ),
                )
            ],
        )
        loc = SpatialLocalisationFactory(
            parent=risk_compo, geo_id="iddomain", risk_level_factory=1
        ).compute()

        assert_equals_result(
            {"domain": loc.domain.to_dict(), "areas": loc.areas.to_dict()}
        )
