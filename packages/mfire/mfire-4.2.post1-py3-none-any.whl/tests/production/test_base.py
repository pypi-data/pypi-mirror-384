import mfire.utils.mfxarray as xr
from mfire.production.base import BaseCDPComponent
from mfire.production.period import CDPPeriod
from mfire.utils.date import Datetime
from tests.composite.factories import (
    RiskComponentCompositeFactory,
    SynthesisComponentCompositeFactory,
)


class TestBaseCDPComponent:
    def test_from_composite(self):
        ds = xr.Dataset(
            {"A": (["id"], [1])},
            coords={"id": ["geo_id"], "areaName": (["id"], ["area_1_name"])},
        )

        # Test with SynthesisComponentComposite
        compo = SynthesisComponentCompositeFactory(compute_factory=lambda: ds)
        base_compo = BaseCDPComponent.from_composite(compo, geo_id="geo_id")

        assert base_compo.ComponentId == "text_component_id"
        assert base_compo.ComponentName == "text_component_name"
        assert base_compo.Period == CDPPeriod(
            PeriodId="period_id",
            PeriodName="period_name",
            DateDebutPeriode=Datetime(2023, 3, 1),
            DateFinPeriode=Datetime(2023, 3, 5),
        )
        assert base_compo.GeoId == "geo_id"
        assert base_compo.GeoName == "area_1_name"

        # Test with RiskComponentComposite
        compo = RiskComponentCompositeFactory()
        base_compo = BaseCDPComponent.from_composite(compo, geo_id="geo_id")

        assert base_compo.ComponentId == "risk_component_id"
        assert base_compo.ComponentName == "risk_component_name"
        assert base_compo.Period == CDPPeriod(
            PeriodId="period_id",
            PeriodName="period_name",
            DateDebutPeriode=Datetime(2023, 3, 1),
            DateFinPeriode=Datetime(2023, 3, 5),
        )
        assert base_compo.GeoId == "geo_id"
        assert base_compo.GeoName == "N.A"

        compo = RiskComponentCompositeFactory(data=ds)
        base_compo = BaseCDPComponent.from_composite(compo, geo_id="geo_id")
        assert base_compo.GeoName == "area_1_name"
