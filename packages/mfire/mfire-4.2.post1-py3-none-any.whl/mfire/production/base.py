from __future__ import annotations

from typing import Dict

from mfire.composite.base import BaseModel
from mfire.composite.component import AbstractComponentComposite
from mfire.production.period import CDPPeriod
from mfire.settings import get_logger

LOGGER = get_logger(name="output.base.mod", bind="output.base")


class BaseCDPAdapter(BaseModel):
    """This class returns the production type information to be provided for the CDP.

    The `risk_component` attribute is the risk_component that this adapter is associated
    with. The `texts` attribute is a dictionary of text strings that are used in the CDP
    production.
    """

    component: AbstractComponentComposite
    texts: Dict[str, str]


class BaseCDPComponent(BaseModel):
    """This class creates an object containing the configuration of the risk_component.

    The `ComponentId` attribute is the unique identifier for the risk_component.
    The `ComponentName` attribute is the name of the risk_component.
    The `Period` attribute is the period for which the risk_component data is relevant.
    The `GeoId` attribute is the unique identifier for the geographic area.
    The `GeoName` attribute is the name of the geographic area.
    """

    ComponentId: str
    ComponentName: str
    Period: CDPPeriod
    GeoId: str
    GeoName: str

    @classmethod
    def from_composite(
        cls, component: AbstractComponentComposite, geo_id: str, **_kwargs
    ) -> BaseCDPComponent:
        """
        Creates a `BaseCDPComponent` object from an `AbstractComponentComposite`
        object.

        Args:
            component: The risk_component to be converted.
            geo_id: The unique identifier for the geographic area.
            **_kwargs: Keyword arguments.

        Returns:
            The converted risk_component.
        """
        return BaseCDPComponent(
            ComponentId=component.id,
            ComponentName=component.name,
            Period=CDPPeriod.from_composite(component.period),
            GeoId=geo_id,
            GeoName=component.area_name(geo_id),
        )
