import pytest

import mfire.utils.mfxarray as xr
from mfire.utils.date import Datetime
from tests.composite.factories import (
    AltitudeCompositeFactory,
    EventCompositeFactory,
    LevelCompositeFactory,
    RiskComponentCompositeFactory,
)
from tests.localisation.factories import (
    RiskLocalisationFactory,
    SpatialLocalisationFactory,
    TableLocalisationFactory,
)


class TestRiskLocalisation:
    def test_init_alt_min_and_alt_max(self):
        # Test with max_level=0
        events = [
            EventCompositeFactory(
                altitude=AltitudeCompositeFactory(alt_min=10, alt_max=200)
            ),
            EventCompositeFactory(
                altitude=AltitudeCompositeFactory(alt_min=50, alt_max=300)
            ),
        ]
        lvl = LevelCompositeFactory(level=0, events=events, logical_op_list=["or"])

        localisation = RiskLocalisationFactory(
            parent=RiskComponentCompositeFactory(levels=[lvl])
        )
        assert localisation.alt_min == 10
        assert localisation.alt_max == 300

        # Test with max_level=2 (lvl1=2, lvl1=1, lvl3=2)
        lvl1 = LevelCompositeFactory(
            level=2,
            events=[
                EventCompositeFactory(
                    altitude=AltitudeCompositeFactory(alt_min=10, alt_max=200)
                ),
                EventCompositeFactory(
                    altitude=AltitudeCompositeFactory(alt_min=50, alt_max=300)
                ),
            ],
        )
        lvl2 = LevelCompositeFactory(
            level=1,
            events=[
                EventCompositeFactory(
                    altitude=AltitudeCompositeFactory(alt_min=0, alt_max=1000)
                )
            ],
        )
        lvl3 = LevelCompositeFactory(
            level=2,
            events=[
                EventCompositeFactory(
                    altitude=AltitudeCompositeFactory(alt_min=20, alt_max=200)
                ),
                EventCompositeFactory(
                    altitude=AltitudeCompositeFactory(alt_min=50, alt_max=400)
                ),
            ],
        )

        valid_time = [Datetime(2023, 3, 1, i).as_np_dt64 for i in range(3)]
        risk_component = RiskComponentCompositeFactory(
            data=xr.Dataset(
                {"A": ("B", [1])}, coords={"B": [1]}  # we force to have non-empty risk
            ),
            final_risk_da_factory=xr.DataArray(
                [[2, 1, 2]], coords={"id": ["geo_id"], "valid_time": valid_time}
            ),
            levels=[lvl1, lvl2, lvl3],
        )

        localisation = RiskLocalisationFactory(parent=risk_component)
        assert localisation.alt_min == 10
        assert localisation.alt_max == 400

    @pytest.mark.parametrize(
        "table,default_localisation,expected",
        [
            (None, True, False),
            (None, False, False),
            ({"A": "B"}, True, True),
            ({"A": "B"}, False, False),
            ({"A": "B", "C": "D"}, False, True),
            ({"A": "B", "C": "D"}, True, True),
        ],
    )
    def test_is_multizone(self, table, default_localisation, expected):
        table_localisation = (
            TableLocalisationFactory(table=table) if table is not None else None
        )
        assert (
            RiskLocalisationFactory(
                table_localisation=table_localisation,
                spatial_localisation=SpatialLocalisationFactory(
                    default_localisation=default_localisation
                ),
            ).is_multizone
            == expected
        )

    def test_periods_name(self):
        periods_name = ["20190727T06_to_20190727T09", "20190727T14_to_20190727T17"]
        assert (
            RiskLocalisationFactory(
                table_localisation=TableLocalisationFactory(
                    infos=xr.DataArray(coords={"period": periods_name}, dims=["period"])
                )
            ).periods_name
            == periods_name
        )

    def test_unique_name(self):
        assert (
            RiskLocalisationFactory(
                table_localisation=TableLocalisationFactory(name_factory="table_name")
            ).unique_name
            == "table_name"
        )

    @pytest.mark.parametrize(
        "raw,expected",
        [
            # Test with 2 zones
            (["0", "1"], "Zone2"),
            (["1", "2"], "Zone1 et Zone2"),
            # Test with 3 zones
            (["1", "2", "3"], "Zone1, Zone2 et Zone3"),
            (["0", "1", "2"], "Zone2 et Zone3"),
        ],
    )
    def test_all_name(self, raw, expected):
        assert (
            RiskLocalisationFactory(
                table_localisation=TableLocalisationFactory(
                    infos=xr.DataArray(coords={"raw": raw}, dims=["raw"]),
                    table={
                        "zone2": "Zone2",
                        "zone1_2": "Zone1 et Zone2",
                        "zone2_3": "Zone2 et Zone3",
                        "zone1_2_3": "Zone1, Zone2 et Zone3",
                    },
                )
            ).all_name
            == expected
        )
