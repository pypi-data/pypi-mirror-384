from abc import ABC, abstractmethod
from datetime import timedelta

from mfire.composite.component import (
    RiskComponentComposite,
    SynthesisComponentComposite,
    TypeComponent,
)
from mfire.production.base import BaseCDPAdapter
from mfire.production.component import CDPComponents, CDPRisk, CDPText
from mfire.production.production import CDPProduction
from mfire.settings import get_logger
from mfire.utils.date import Datetime

LOGGER = get_logger(name="output_adapter.mod", bind="output_adapter")


class CDPAdapter(BaseCDPAdapter):
    """Class to be used for the implementation of an adapter taking a risk or text
    risk_component
    """

    def compute(self) -> CDPProduction:
        """Computes the adapted components.

        Returns:
            A list of CDPComponents, one for each geo_id.
        """
        adapter_class = (
            CDPTextAdapter
            if self.component.type == TypeComponent.SYNTHESIS
            else CDPRiskAdapter
        )
        return adapter_class(component=self.component, texts=self.texts).compute()


class AbstractCDPSynthesisAdapter(BaseCDPAdapter, ABC):
    @property
    @abstractmethod
    def adapted_components(self) -> CDPComponents:
        """Returns a list of CDPComponents."""

    def compute(self) -> CDPProduction:
        now = Datetime.now()

        # we round the production time do the previous half-hour
        date_prod = now.replace(tzinfo=None) - timedelta(
            minutes=now.minute % 30, seconds=now.second, microseconds=now.microsecond
        )

        return CDPProduction(
            ProductionId=self.component.production_id,
            ProductionName=self.component.production_name,
            CustomerId=self.component.customer_id,
            CustomerName=self.component.customer_name,
            DateBulletin=self.component.production_datetime,
            DateProduction=date_prod,
            DateConfiguration=self.component.configuration_datetime,
            Components=self.adapted_components,
        )


class CDPRiskAdapter(AbstractCDPSynthesisAdapter):
    component: RiskComponentComposite

    @property
    def adapted_components(self) -> CDPComponents:
        return CDPComponents(
            Aleas=[
                CDPRisk.from_composite(
                    component=self.component, geo_id=geo_id, text=self.texts[geo_id]
                )
                for geo_id in self.texts
            ]
        )


class CDPTextAdapter(AbstractCDPSynthesisAdapter):
    component: SynthesisComponentComposite

    @property
    def adapted_components(self) -> CDPComponents:
        return CDPComponents(
            Text=[
                CDPText.from_composite(
                    component=self.component, geo_id=geo_id, text=self.texts[geo_id]
                )
                for geo_id in self.texts
            ]
        )
