import mfire.utils.mfxarray as xr
from mfire.production.adapter import CDPAdapter
from mfire.production.period import CDPPeriod
from mfire.utils.date import Datetime
from tests.composite.factories import (
    RiskComponentCompositeFactory,
    SynthesisComponentCompositeFactory,
)


class TestCDPAdapter:
    def test_text_adapter(self):
        ds = xr.Dataset(
            {"A": (["id"], [1, 2])},
            coords={
                "id": ["geo_id_1", "geo_id_2"],
                "areaName": (["id"], ["area_1_name", "area_2_name"]),
            },
        )
        text_compo = SynthesisComponentCompositeFactory(compute_factory=lambda: ds)

        texts = {"geo_id_1": "texte_1", "geo_id_2": "texte_2"}
        adapter = CDPAdapter(component=text_compo, texts=texts)

        result = adapter.compute()

        assert result.ProductionId == "production_id"
        assert result.ProductionName == "production_name"
        assert result.CustomerId == "customer_id"
        assert result.CustomerName == "customer_name"
        assert result.DateBulletin == Datetime(2023, 3, 1, 6)

        assert len(result.Components.Text) == 2
        assert result.Components.Aleas is None

        # Test of the first text
        cdp_text = result.Components.Text[0]
        assert cdp_text.ComponentId == "text_component_id"
        assert cdp_text.ComponentName == "text_component_name"
        assert cdp_text.Period == CDPPeriod(
            PeriodId="period_id",
            PeriodName="period_name",
            DateDebutPeriode=Datetime(2023, 3, 1),
            DateFinPeriode=Datetime(2023, 3, 5),
        )
        assert cdp_text.GeoId == "geo_id_1"
        assert cdp_text.GeoName == "area_1_name"
        assert cdp_text.SyntText == "texte_1"

        # Test of the second text
        cdp_text = result.Components.Text[1]
        assert cdp_text.ComponentId == "text_component_id"
        assert cdp_text.ComponentName == "text_component_name"
        assert cdp_text.Period == CDPPeriod(
            PeriodId="period_id",
            PeriodName="period_name",
            DateDebutPeriode=Datetime(2023, 3, 1),
            DateFinPeriode=Datetime(2023, 3, 5),
        )
        assert cdp_text.GeoId == "geo_id_2"
        assert cdp_text.GeoName == "area_2_name"
        assert cdp_text.SyntText == "texte_2"

    def test_risk_adapter(self):
        ds = xr.Dataset(
            {"A": (["id"], [1, 2])}, coords={"id": ["geo_id_1", "geo_id_2"]}
        )
        risk_compo = RiskComponentCompositeFactory(data=ds, is_risks_empty_factory=True)

        texts = {"geo_id_1": "texte_1", "geo_id_2": "texte_2"}
        adapter = CDPAdapter(component=risk_compo, texts=texts)

        result = adapter.compute()

        assert result.ProductionId == "production_id"
        assert result.ProductionName == "production_name"
        assert result.CustomerId == "customer_id"
        assert result.CustomerName == "customer_name"
        assert result.DateBulletin == Datetime(2023, 3, 1, 6)

        assert len(result.Components.Aleas) == 2
        assert result.Components.Text is None

        # Test of the first text
        cdp_risk = result.Components.Aleas[0]
        assert cdp_risk.ComponentId == "risk_component_id"
        assert cdp_risk.ComponentName == "risk_component_name"
        assert cdp_risk.Period == CDPPeriod(
            PeriodId="period_id",
            PeriodName="period_name",
            DateDebutPeriode=Datetime(2023, 3, 1),
            DateFinPeriode=Datetime(2023, 3, 5),
        )
        assert cdp_risk.GeoId == "geo_id_1"
        assert cdp_risk.GeoName == "N.A"
        assert cdp_risk.DetailComment == "texte_1"

        # Test of the second text
        cdp_risk = result.Components.Aleas[1]
        assert cdp_risk.ComponentId == "risk_component_id"
        assert cdp_risk.ComponentName == "risk_component_name"
        assert cdp_risk.Period == CDPPeriod(
            PeriodId="period_id",
            PeriodName="period_name",
            DateDebutPeriode=Datetime(2023, 3, 1),
            DateFinPeriode=Datetime(2023, 3, 5),
        )
        assert cdp_risk.GeoId == "geo_id_2"
        assert cdp_risk.GeoName == "N.A"
        assert cdp_risk.DetailComment == "texte_2"
