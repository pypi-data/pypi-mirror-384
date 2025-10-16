from typing import Dict, List, Optional

from mfire.composite.component import SynthesisModule
from mfire.text.synthesis.reducer import SynthesisReducer
from mfire.text.synthesis.temperature import TemperatureBuilder, TemperatureReducer
from mfire.text.synthesis.weather import WeatherBuilder, WeatherReducer
from tests.composite.factories import BaseCompositeFactory, SynthesisModuleFactory


class SynthesisReducerFactory(SynthesisReducer, BaseCompositeFactory):
    parent: SynthesisModuleFactory = SynthesisModuleFactory()
    geo_id: str = "geo_id"

    def _compute(self, **_kwargs) -> Dict | List[Dict]:
        pass


class TemperatureReducerFactory(TemperatureReducer, BaseCompositeFactory):
    parent: SynthesisModuleFactory = SynthesisModuleFactory()
    geo_id: str = "geo_id"


class WeatherReducerFactory(WeatherReducer, BaseCompositeFactory):
    parent: SynthesisModule = SynthesisModuleFactory()
    geo_id: Optional[str] = "geo_id"


class WeatherBuilderFactory(WeatherBuilder, BaseCompositeFactory):
    parent: SynthesisModuleFactory = SynthesisModuleFactory()
    reducer_class: type = WeatherReducerFactory
    geo_id: Optional[str] = "geo_id"


class TemperatureBuilderFactory(TemperatureBuilder, BaseCompositeFactory):
    parent: SynthesisModuleFactory = SynthesisModuleFactory()
    geo_id: str = "geo_id"
