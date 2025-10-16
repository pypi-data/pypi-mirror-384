from mfire.text.manager import Manager
from tests.composite.factories import (
    BaseCompositeFactory,
    RiskComponentCompositeFactory,
    SynthesisComponentCompositeFactory,
)


class ManagerFactory(Manager, BaseCompositeFactory):
    parent: RiskComponentCompositeFactory | SynthesisComponentCompositeFactory = (
        RiskComponentCompositeFactory
    )
    geo_id: str = "geo_id"
