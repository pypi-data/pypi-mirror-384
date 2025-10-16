from __future__ import annotations

from typing import List, Optional

from mfire.composite.base import BaseModel
from mfire.composite.component import (
    RiskComponentComposite,
    SynthesisComponentComposite,
)
from mfire.production.base import BaseCDPComponent
from mfire.production.dataset import CDPDataset


class CDPRisk(BaseCDPComponent):
    """This class creates an object containing the configuration of an alea.

    The `HazardId` attribute is the unique identifier of the alea.
    The `HazardName` attribute is the name of the alea.
    The `Dataset` attribute is the dataset that contains the alea data.
    The `DetailComment` attribute is a free-text comment that can be used to provide
        additional information about the alea.
    """

    HazardId: str
    HazardName: str
    Dataset: CDPDataset
    DetailComment: str

    @classmethod
    def from_composite(
        cls, component: RiskComponentComposite, geo_id: str, **kwargs
    ) -> CDPRisk:
        """Creates a `CDPRisk` object from a `RiskComponentComposite` object.

        Args:
            component: The risk_component to be converted.
            geo_id: The unique identifier for the geographic area.
            **kwargs: Keyword arguments.

        Returns:
            CDPRisk: The converted risk_component.
        """
        base_dict = (
            super().from_composite(component=component, geo_id=geo_id).model_dump()
        )
        return CDPRisk(
            HazardId=component.hazard_id,
            HazardName=component.hazard_name,
            Dataset=CDPDataset.from_composite(component=component, geo_id=geo_id),
            DetailComment=kwargs.get("text"),
            **base_dict,
        )


class CDPText(BaseCDPComponent):
    """This class creates an object containing the configuration of a text-type
    risk_component.

    The `SyntText` attribute is the text string of the risk_component.
    """

    SyntText: str

    @classmethod
    def from_composite(
        cls, component: SynthesisComponentComposite, geo_id: str, **kwargs
    ) -> CDPText:
        """Creates a `CDPText` object from a `SynthesisComponentComposite` object.

        Args:
            component: The risk_component to be converted.
            geo_id: The unique identifier for the geographic area.
            **kwargs: Keyword arguments.

        Returns:
            CDPText: The converted risk_component.
        """
        base_dict = (
            super().from_composite(component=component, geo_id=geo_id).model_dump()
        )
        return CDPText(SyntText=kwargs.get("text"), **base_dict)


class CDPComponents(BaseModel):
    """
    Creates an object containing the configuration of a text-type or risk-type
    risk_component.

    The `Aleas` attribute is an optional list of `CDPRisk` objects.
    The `Text` attribute is an optional list of `CDPText` objects.
    """

    Aleas: Optional[List[CDPRisk]] = None
    Text: Optional[List[CDPText]] = None

    def __add__(self, other: CDPComponents) -> CDPComponents:
        """Appends the components of the given `CDPComponents` object to this object.

        Args:
            other: The `CDPComponents` object whose components should be appended.

        Returns:
            CDPComponents: The updated `CDPComponents` object.
        """

        risks = (self.Aleas or []) + (other.Aleas or [])
        text = (self.Text or []) + (other.Text or [])

        return CDPComponents(Aleas=risks, Text=text)
