import mfire.utils.mfxarray as xr
from mfire.production.component import CDPRisk, CDPText
from mfire.production.period import CDPPeriod
from mfire.utils.date import Datetime
from tests.composite.factories import (
    RiskComponentCompositeFactory,
    SynthesisComponentCompositeFactory,
)
from tests.production.factories import (
    CDPComponentsFactory,
    CDPRiskFactory,
    CDPTextFactory,
)


class TestCDPRisk:
    def test_from_composite(self):
        risk_compo = RiskComponentCompositeFactory()
        cdp_risk = CDPRisk.from_composite(
            risk_compo, geo_id="geo_id", text="text_risk_compo"
        )

        assert cdp_risk.ComponentId == "risk_component_id"
        assert cdp_risk.ComponentName == "risk_component_name"
        assert cdp_risk.Period == CDPPeriod(
            PeriodId="period_id",
            PeriodName="period_name",
            DateDebutPeriode=Datetime(2023, 3, 1),
            DateFinPeriode=Datetime(2023, 3, 5),
        )
        assert cdp_risk.GeoId == "geo_id"
        assert cdp_risk.GeoName == "N.A"

        assert cdp_risk.HazardId == "hazard_id"
        assert cdp_risk.HazardName == "hazard_name"
        assert cdp_risk.DetailComment == "text_risk_compo"


class TestCDPText:
    def test_from_composite(self):
        ds = xr.Dataset(
            {"A": (["id"], [1])},
            coords={"id": ["geo_id"], "areaName": (["id"], ["area_1_name"])},
        )
        text_compo = SynthesisComponentCompositeFactory(compute_factory=lambda: ds)
        cdp_text = CDPText.from_composite(
            text_compo, geo_id="geo_id", text="text_risk_compo"
        )

        assert cdp_text.ComponentId == "text_component_id"
        assert cdp_text.ComponentName == "text_component_name"
        assert cdp_text.Period == CDPPeriod(
            PeriodId="period_id",
            PeriodName="period_name",
            DateDebutPeriode=Datetime(2023, 3, 1),
            DateFinPeriode=Datetime(2023, 3, 5),
        )
        assert cdp_text.GeoId == "geo_id"
        assert cdp_text.GeoName == "area_1_name"

        assert cdp_text.SyntText == "text_risk_compo"


class TestCDPComponents:
    def test_add(self):
        risk, text = CDPRiskFactory(), CDPTextFactory()
        cdp1 = CDPComponentsFactory(Aleas=[risk], Text=None)
        cdp2 = CDPComponentsFactory(Text=[text], Aleas=None)

        result = cdp1 + cdp2
        assert result.Aleas == [risk]
        assert result.Text == [text]
