import copy
import json
from pathlib import Path
from typing import Annotated, Any, ClassVar, Optional

import numpy as np
from pydantic import BaseModel, SkipValidation

from mfire.composite.component import RiskComponentComposite
from mfire.composite.operator import ComparisonOperator
from mfire.text.risk.builder import (
    RiskBuilder,
    RiskBuilderStrategy,
    RiskBuilderStrategyME,
    RiskBuilderStrategyRain,
    RiskBuilderStrategySnow,
)
from mfire.text.risk.reducer import (
    RiskReducer,
    RiskReducerStrategy,
    RiskReducerStrategyME,
    RiskReducerStrategyMonozone,
    RiskReducerStrategyRain,
    RiskReducerStrategySnow,
)
from mfire.text.risk.rep_value import (
    AccumulationRepValueReducer,
    AltitudeRepValueBuilder,
    AltitudeRepValueReducer,
    FFRafRepValueBuilder,
    FFRafRepValueReducer,
    FFRepValueBuilder,
    FFRepValueReducer,
    LpnRepValueBuilder,
    LpnRepValueReducer,
    PrecipitationRepValueBuilder,
    PrecipitationRepValueReducer,
    RainRepValueBuilder,
    RainRepValueReducer,
    RepValueBuilder,
    RepValueReducer,
    SnowRepValueBuilder,
    SnowRepValueReducer,
    TemperatureRepValueBuilder,
    TemperatureRepValueReducer,
)
from tests.composite.factories import (
    BaseCompositeFactory,
    RiskComponentCompositeFactory,
)
from tests.factories import Factory
from tests.localisation.factories import RiskLocalisationFactory


class RiskReducerFactory(RiskReducer, BaseCompositeFactory):
    geo_id: str = "geo_id"
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )
    localisation: Optional[RiskLocalisationFactory] = RiskLocalisationFactory()


class RiskReducerStrategyFactory(RiskReducerStrategy, Factory):
    parent: RiskReducer = RiskReducerFactory()

    def compute(self):
        pass

    def process_period(self):
        pass


class RiskReducerStrategySnowFactory(RiskReducerStrategySnow, Factory):
    parent: RiskReducer = RiskReducerFactory()


class RiskReducerStrategyRainFactory(RiskReducerStrategyRain, Factory):
    parent: RiskReducer = RiskReducerFactory()


class RiskReducerStrategyMEFactory(RiskReducerStrategyME, Factory):
    parent: RiskReducer = RiskReducerFactory()


class RiskReducerStrategyMonozoneFactory(RiskReducerStrategyMonozone, Factory):
    parent: RiskReducer = RiskReducerFactory()


class RiskBuilderFactory(RiskBuilder, BaseCompositeFactory):
    geo_id: str = "geo_id"
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )
    reducer_class: type = RiskReducerFactory


class RiskBuilderStrategyFactory(RiskBuilderStrategy, Factory):

    parent: RiskBuilder = RiskBuilderFactory()

    @property
    def template_name(self) -> str:
        return ""

    @property
    def template_key(self) -> str | np.ndarray:
        return ""


class RiskBuilderStrategyMEFactory(RiskBuilderStrategyME, Factory):
    parent: RiskBuilder = RiskBuilderFactory()


class RiskBuilderStrategyRainFactory(RiskBuilderStrategyRain, Factory):
    parent: RiskBuilder = RiskBuilderFactory()


class RiskBuilderStrategySnowFactory(RiskBuilderStrategySnow, Factory):
    parent: RiskBuilder = RiskBuilderFactory()


class _RepValueReducerBaseFactory(BaseCompositeFactory):
    geo_id: str = "geo_id"
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )

    def __init__(
        self,
        infos: Optional[dict] = None,
        var_name: Optional[str] = None,
        **kwargs: Any
    ):
        if infos is None:
            infos = {}
        if var_name is None and self.test_var_name is not None:
            var_name = self.test_var_name
        if var_name is not None:
            infos |= {"var_name": var_name}
        super().__init__(infos=infos, **kwargs)


class RepValueReducerFactory(_RepValueReducerBaseFactory, RepValueReducer):
    test_var_name: ClassVar[str] = "TEST__VARNAME"


class RepValueBuilderFactory(RepValueBuilder, BaseCompositeFactory):
    geo_id: str = "geo_id"
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )
    reducer_class: type = lambda **kwargs: RepValueReducerFactory(
        phenomenon_factory="phen", **kwargs
    )

    def __init__(
        self,
        infos: Optional[dict] = None,
        var_name: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        if infos is None:
            infos = {}

        super().__init__(infos=infos, **kwargs)

        if var_name is None and self.reducer_class().test_var_name is not None:
            var_name = self.reducer_class().test_var_name
        if var_name is not None:
            self.infos |= {"var_name": var_name}


class FFRepValueReducerFactory(FFRepValueReducer, BaseCompositeFactory):
    geo_id: str = "geo_id"
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )

    def __init__(self, **kwargs: Any):
        kwargs["infos"] = kwargs.get("infos", {}) | {"var_name": "FF__HAUTEUR10"}
        super().__init__(**kwargs)


class FFRepValueBuilderFactory(FFRepValueBuilder, BaseCompositeFactory):
    reducer_class: type = FFRepValueReducerFactory
    geo_id: str = "geo_id"
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.infos |= {"var_name": "FF__HAUTEUR10"}


class TemperatureRepValueReducerFactory(
    _RepValueReducerBaseFactory, TemperatureRepValueReducer
):
    test_var_name: ClassVar[str] = "T__HAUTEUR2"


class TemperatureRepValueBuilderFactory(
    TemperatureRepValueBuilder, BaseCompositeFactory
):
    reducer_class: type = TemperatureRepValueReducerFactory
    geo_id: str = "geo_id"
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.infos |= {"var_name": "T__HAUTEUR2"}


class FFRafRepValueReducerFactory(FFRafRepValueReducer, BaseCompositeFactory):
    geo_id: str = "geo_id"
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )

    def __init__(self, **kwargs: Any):
        kwargs["infos"] = kwargs.get("infos", {}) | {"var_name": "RAF__HAUTEUR10"}
        super().__init__(**kwargs)


class FFRafRepValueBuilderFactory(FFRafRepValueBuilder, BaseCompositeFactory):
    reducer_class: type = FFRafRepValueReducerFactory
    geo_id: str = "geo_id"
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.infos |= {"var_name": "RAF__HAUTEUR10"}


class AccumulationRepValueReducerFactory(
    _RepValueReducerBaseFactory, AccumulationRepValueReducer
):
    test_var_name: ClassVar[str] = "TEST1__VARNAME"
    bounds: list = []
    last_bound_size: int = 10


class SnowRepValueReducerFactory(_RepValueReducerBaseFactory, SnowRepValueReducer):
    test_var_name: ClassVar[str] = "NEIPOT1__SOL"


class SnowRepValueBuilderFactory(SnowRepValueBuilder, BaseCompositeFactory):
    reducer_class: type = SnowRepValueReducerFactory
    geo_id: str = "geo_id"
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.infos |= {"var_name": "NEIPOT1__SOL"}


class PrecipitationRepValueReducerFactory(
    _RepValueReducerBaseFactory, PrecipitationRepValueReducer
):
    test_var_name: ClassVar[str] = "PRECIP3__SOL"


class PrecipitationRepValueBuilderFactory(
    PrecipitationRepValueBuilder, BaseCompositeFactory
):
    reducer_class: type = PrecipitationRepValueReducerFactory
    geo_id: str = "geo_id"
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.infos |= {"var_name": "PRECIP3__SOL"}


class RainRepValueReducerFactory(_RepValueReducerBaseFactory, RainRepValueReducer):
    test_var_name: ClassVar[str] = "EAU24__SOL"


class RainRepValueBuilderFactory(RainRepValueBuilder, BaseCompositeFactory):
    reducer_class: type = RainRepValueReducerFactory
    geo_id: str = "geo_id"
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.infos |= {"var_name": "EAU24__SOL"}


class LpnRepValueReducerFactory(_RepValueReducerBaseFactory, LpnRepValueReducer):
    test_var_name: ClassVar[str] = "LPN__SOL"


class LpnRepValueBuilderFactory(LpnRepValueBuilder, BaseCompositeFactory):
    reducer_class: type = LpnRepValueReducerFactory
    geo_id: str = "geo_id"
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )


class AltitudeRepValueReducerFactory(AltitudeRepValueReducer, BaseCompositeFactory):
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )
    geo_id: str = "geo_id"


class AltitudeRepValueBuilderFactory(AltitudeRepValueBuilder, BaseCompositeFactory):
    reducer_class: type = AltitudeRepValueReducerFactory
    parent: Annotated[RiskComponentComposite, SkipValidation] = (
        RiskComponentCompositeFactory()
    )
    geo_id: str = "geo_id"


class DataFactory(BaseModel):
    units: Optional[str] = "cm"
    operator: Optional[ComparisonOperator] = ComparisonOperator.SUPEGAL
    value: Optional[float] = None
    next_critical: Optional[float] = None
    threshold: Optional[float] = None
    occurrence: Optional[bool] = False


def infos_factory(**kwargs) -> dict:
    return DataFactory(**kwargs).model_dump()


class RepValueTestFactory:
    """Create test infos of representative values."""

    DATA_NO_VALUE: dict = infos_factory()
    DATA_REP_PLAIN_ONLY_10: dict = infos_factory(value=10.0)
    DATA_REP_PLAIN_ONLY_15: dict = infos_factory(value=15.0)
    DATA_ACC_REP_LOCAL_ONLY_2: dict = infos_factory(
        value=1e-7, threshold=2.0, occurrence=True
    )
    DATA_ACC_REP_LOCAL_ONLY_10: dict = infos_factory(
        value=1e-7, threshold=10.0, occurrence=True
    )
    # rep plain < rep local
    DATA_REP_PLAIN_AND_LOCAL_10_15: dict = infos_factory(
        value=10.0, threshold=15.0, occurrence=True
    )
    DATA_REP_PLAIN_AND_LOCAL_15_20: dict = infos_factory(
        value=15.0, threshold=20.0, occurrence=True
    )
    # rep plain > rep local
    DATA_REP_PLAIN_AND_LOCAL_20_10: dict = infos_factory(
        value=20.0, threshold=10.0, occurrence=True, operator=ComparisonOperator.INFEGAL
    )
    DATA_REP_PLAIN_AND_LOCAL_40_30: dict = infos_factory(
        value=40.0, threshold=30.0, occurrence=True, operator=ComparisonOperator.SUPEGAL
    )
    # rep plain = rep local
    DATA_REP_PLAIN_AND_LOCAL_12_12: dict = infos_factory(
        value=12.0, threshold=12.0, occurrence=True
    )
    DATA_REP_PLAIN_AND_LOCAL_20_20: dict = infos_factory(
        value=20.0, threshold=20.0, occurrence=True
    )

    def __init__(self):
        self.infos: list[dict] = []

    def _add_case_infos(self, case_infos: dict):
        self.infos.append(case_infos)

    def _create_mixed_case(self, plain_infos: dict, mountain_infos: dict):
        self._add_case_infos({"plain": plain_infos, "mountain": mountain_infos})

    def _create_simple_cases(self, infos_name) -> None:
        for infos in [
            self.DATA_NO_VALUE,
            self.DATA_REP_PLAIN_ONLY_10,
            self.DATA_ACC_REP_LOCAL_ONLY_2,
            self.DATA_REP_PLAIN_AND_LOCAL_10_15,
            self.DATA_REP_PLAIN_AND_LOCAL_20_10,
            self.DATA_REP_PLAIN_AND_LOCAL_12_12,
        ]:
            self._add_case_infos({infos_name: infos})

    def _create_mixed_cases(self):
        infos_1: list[dict] = [
            self.DATA_NO_VALUE,
            self.DATA_REP_PLAIN_ONLY_10,
            self.DATA_ACC_REP_LOCAL_ONLY_2,
            self.DATA_REP_PLAIN_AND_LOCAL_10_15,
        ]

        infos_2: list[dict] = [
            self.DATA_NO_VALUE,
            self.DATA_REP_PLAIN_ONLY_15,
            self.DATA_ACC_REP_LOCAL_ONLY_10,
            self.DATA_REP_PLAIN_AND_LOCAL_15_20,
        ]

        for plain_infos in infos_1:
            for mountain_infos in infos_2:
                self._create_mixed_case(plain_infos, mountain_infos)

        # rep plain > rep mountain
        self._create_mixed_case(
            self.DATA_REP_PLAIN_ONLY_15, self.DATA_REP_PLAIN_ONLY_10
        )

        # rep plain = rep mountain, no rep local
        self._create_mixed_case(
            self.DATA_REP_PLAIN_ONLY_10, self.DATA_REP_PLAIN_ONLY_10
        )

        # no rep plain, local plain = local mountain (only for accumulated variable)
        self._create_mixed_case(
            self.DATA_ACC_REP_LOCAL_ONLY_10, self.DATA_ACC_REP_LOCAL_ONLY_10
        )

        # rep plain (without local rep) = rep mountain < rep local mountain
        self._create_mixed_case(
            self.DATA_REP_PLAIN_ONLY_10, self.DATA_REP_PLAIN_AND_LOCAL_10_15
        )

    def run(self, file_path: Optional[Path | str] = None) -> list[dict]:
        # Generate empty case
        self._add_case_infos({})

        # Generate plain cases
        self._create_simple_cases("plain")

        # Generate mountain cases
        self._create_simple_cases("mountain")

        # Generate plain/mountain mixed-cases
        self._create_mixed_cases()

        if file_path is not None:
            with open(Path(file_path), "w") as f:
                json.dump(self.infos, f, indent=4)

        return self.infos


def create_rep_value_test_infos_altitude(
    test_infos: list, file_path: Optional[Path | str] = None
) -> list[dict]:
    # Create test infos of representative values with altitude.
    test_infos_altitude: list = copy.deepcopy(test_infos)

    for dico in test_infos_altitude:
        dico["mountain_altitude"] = 1500

    if file_path is not None:
        with open("infos_altitude.json", "w") as f:
            json.dump(test_infos_altitude, f, indent=4)

    return test_infos_altitude
