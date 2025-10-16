import random
from typing import Optional

import mfire.utils.mfxarray as xr
from mfire.composite.serialized_types import s_slice
from mfire.utils.date import Datetime
from mfire.utils.lpn import Lpn
from mfire.utils.period import Period, PeriodDescriber
from mfire.utils.selection import Selection
from tests.composite.factories import BaseCompositeFactory
from tests.factories import Factory


class SelectionFactory(Selection):
    sel: Optional[dict] = {"id": random.randint(0, 42)}
    islice: Optional[dict[str, s_slice | float]] = {
        "valid_time": slice(random.randint(0, 42), random.randint(0, 42))
    }
    isel: Optional[dict] = {"latitude": random.randint(0, 42)}
    slice: Optional[dict[str, s_slice]] = {
        "longitude": slice(random.randint(0, 42), random.randint(0, 42))
    }


class PeriodDescriberFactory(PeriodDescriber, BaseCompositeFactory):
    cover_period: Period = Period(
        begin_time=Datetime(2023, 3, 1), end_time=Datetime(2023, 3, 3)
    )
    request_time: Datetime = Datetime(2023, 3, 1, 2)


class LpnFactory(Factory, Lpn):
    da: xr.DataArray = None
    period_describer: PeriodDescriberFactory = PeriodDescriberFactory()
