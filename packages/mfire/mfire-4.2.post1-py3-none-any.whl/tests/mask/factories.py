from typing import List

from shapely import box

from mfire.mask.processor import GridProcessor, Processor
from tests.composite.factories import BaseCompositeFactory


class ProcessorFactory(BaseCompositeFactory, Processor):
    config: dict = {"config_language": "fr"}


class GridProcessorFactory(GridProcessor, BaseCompositeFactory):
    features: List[dict] = [
        {
            "id": "id1",
            "properties": {"name": "area_name1"},
            "geometry": box(-4.04, 47.04, -4, 47),
        }
    ]
    grid_name: str = "franxl1s100"
    parent: ProcessorFactory = ProcessorFactory()
