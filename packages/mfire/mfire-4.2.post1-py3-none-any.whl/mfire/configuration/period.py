from abc import abstractmethod
from typing import Annotated, List, Literal, Optional, Tuple

from pydantic import (
    BaseModel,
    Discriminator,
    Field,
    Tag,
    conlist,
    field_validator,
    model_validator,
)

from mfire.composite.period import PeriodComposite as CompositePeriod
from mfire.composite.period import PeriodsComposite as CompositePeriodCollection
from mfire.composite.serialized_types import s_datetime
from mfire.settings import get_logger
from mfire.utils.date import Datetime, Timedelta

LOGGER = get_logger(name=__name__)


class PeriodBase(BaseModel):
    id: str
    name: Optional[str] = None

    @abstractmethod
    def processed_period(self, production_datetime: Datetime) -> CompositePeriod:
        """
        Returns the processed period corresponding to the given production datetime.

        Args:
            production_datetime: The current production datetime.

        Returns:
            Period: A Period object with concrete start and stop datetimes.
        """


class PeriodSingleBase(BaseModel):
    """PeriodSingle class : Period without a list of periodElements"""

    start: Optional[int] = None
    delta_start: Optional[int] = Field(None, alias="deltaStart")
    absolu_start: Optional[s_datetime] = Field(None, alias="absoluStart")
    stop: Optional[int] = None
    delta_stop: Optional[int] = Field(None, alias="deltaStop")
    absolu_stop: Optional[s_datetime] = Field(None, alias="absoluStop")
    production_time_until: int = Field(24, ge=0, le=24, alias="productionTime_until")

    @field_validator("production_time_until", mode="before")
    def init_production_time_until(cls, val: Optional[int]) -> int:
        # absolutely test versus None because 0 is also False
        if val is None:
            return 24
        return val

    @model_validator(mode="before")
    def init_start_stop(cls, values: dict) -> dict:
        """
        Validates the consistency of start and stop keys in a period element
        configuration.

        This validator ensures that exactly one 'start' and one 'stop' key is present in
        the provided dictionary. It also handles potential typos ("Start" instead of
        "start") and converts "absoluStart" and "absoluStop" values to `Datetime`
        objects.

        Args:
            values: The dictionary containing period element configuration data.

        Returns:
            The validated dictionary with potential corrections applied.

        Raises:
            ValueError: If there are not exactly one 'start' and one 'stop' key found.
        """

        # Handle potential typos ("Start"/"Stop" instead of "start"/"stop")
        if "Start" in values:
            values["start"] = values.pop("Start")
        if "Stop" in values:
            values["stop"] = values.pop("Stop")

        # Define valid start and stop keys (case-insensitive)
        start_keys = ("start", "deltaStart", "absoluStart")
        stop_keys = ("stop", "deltaStop", "absoluStop")

        # Count occurrences of start and stop keys
        start_count = sum(values.get(k) is not None for k in start_keys)
        stop_count = sum(values.get(k) is not None for k in stop_keys)

        # Validate that there's exactly one start and stop key
        if start_count != 1:
            raise ValueError(f"Exactly one 'start' key expected. {start_count} given.")
        if stop_count != 1:
            raise ValueError(f"Exactly one 'stop' key expected. {stop_count} given.")

        # Convert "absoluStart"/"absoluStop" values to Datetime objects (if present)
        if "absoluStart" in values:
            values["absoluStart"] = Datetime(values["absoluStart"])
        if "absoluStop" in values:
            values["absoluStop"] = Datetime(values["absoluStop"])

        return values

    def bound(
        self, production_datetime: Datetime, name: Literal["start", "stop"]
    ) -> Datetime:
        """
        Calculates the datetime corresponding to a specific bound ("start" or "stop")
        within a period element configuration, based on a reference datetime.

        This method allows resolving the actual start or stop datetime for a period
        element given its configuration and the reference datetime. It handles different
        bound types:

        - Absolute ("absoluStart"): Uses the provided value directly.
        - Delta ("deltaStart"): Adds the delta value as hours to the reference datetime.
        - Relative ("start", "stop"): Calculates the datetime based on the reference
            date's midnight, considering the element's `production_time_until` and
            potential need to shift to the next day.

        Args:
            production_datetime: The reference datetime.
            name: The name of the bound to calculate.

        Returns:
            The calculated datetime corresponding to the specified bound and reference.

        Examples:
        >>> el = PeriodSingleBase(deltaStart=1, stop=32, productionTime_until=16)
        >>> ref_dt = Datetime(2021, 11, 3, 10)
        >>> el.bound(ref_dt, "start")
        Datetime(2021, 11, 3, 11)
        >>> el.bound(ref_dt, "stop")
        Datetime(2021, 11, 4, 8)
        >>> el.bound(Datetime(2021, 11, 3, 17), "stop")
        Datetime(2021, 11, 5, 8)

        >>> el = PeriodSingleBase(
        >>>    start=1, absoluStop=Datetime(2021, 1, 1), productionTime_until=16
        >>> )
        >>> el.bound(ref_dt, "stop")
        Datetime(2021, 1, 1)
        """

        # Extract bound key and value based on the name (e.g., "deltaStart")
        bound_key, bound_value = next(
            (field, getattr(self, field))
            for field in self.model_fields
            if name in field and getattr(self, field) is not None
        )

        # Determine datetime based on bound type
        if bound_key.startswith("absolu"):
            result = Datetime(bound_value)
        elif bound_key.startswith("delta"):
            result = production_datetime + Timedelta(hours=bound_value)
        else:
            # if the production_datetime is 00h and the production goes until 00h,
            # we produce the bulletin for the next period since we're somewhere
            # between 00h and 01h and we don't want to produce bulletin in the past
            nb_days_shift = int(production_datetime.hour >= self.production_time_until)
            result = production_datetime.midnight + Timedelta(
                days=nb_days_shift, hours=bound_value
            )

        # Handle potential warnings for datetime before reference
        if result < production_datetime:
            LOGGER.warning(
                f"Configured '{name}' datetime ({result}) is before the reference "
                f"datetime ({production_datetime})."
            )
        return result

    def start_stop(self, production_datetime: Datetime) -> Tuple[Datetime, Datetime]:
        """Returns the start and stop datetime corresponding to
        the self configuration and a given reference datetime.

        Args:
            production_datetime: Reference datetime

        Returns:
            Tuple of start and stop datetime.
        """
        start = self.bound(production_datetime, "start")
        stop = self.bound(production_datetime, "stop")

        if start > stop:
            LOGGER.warning(
                f"Configured start datetime ({start}) is after the "
                f"configured stop datetime ({stop})."
            )
        return start, stop


class PeriodSingle(PeriodBase, PeriodSingleBase):
    def processed_period(self, production_datetime: Datetime) -> CompositePeriod:
        start, stop = self.start_stop(production_datetime)
        return CompositePeriod(id=self.id, name=self.name, start=start, stop=stop)


class PeriodMultiple(PeriodBase):
    """PeriodMultiple: class Period with multiple periodElements"""

    id: str
    name: Optional[str] = None

    period_elements: Annotated[
        conlist(PeriodSingleBase, min_length=1), Field(alias="periodElements")
    ]

    @field_validator("period_elements")
    def sort_elements(cls, elements: List[PeriodBase]) -> List[PeriodBase]:
        return sorted(elements, key=lambda element: element.production_time_until)

    def processed_period(self, production_datetime: Datetime) -> CompositePeriod:
        # As soon as production_datetime == pt_until, we want to pick the next period
        # because it means that the current hour as already started, and we don't want
        # to describe past events
        element = next(
            (
                el
                for el in self.period_elements
                if production_datetime.hour < el.production_time_until
            ),
            self.period_elements[0],
        )
        start, stop = element.start_stop(production_datetime)
        return CompositePeriod(id=self.id, name=self.name, start=start, stop=stop)


Period = Annotated[
    Annotated[PeriodSingle, Tag("PeriodSingle")]
    | Annotated[PeriodMultiple, Tag("PeriodMultiple")],
    Discriminator(
        lambda x: (
            "PeriodMultiple"
            if "periodElements" in x or isinstance(x, PeriodMultiple)
            else "PeriodSingle"
        )
    ),
]


class PeriodCollection(BaseModel):
    periods: List[Period]

    def __getitem__(self, period_id: str) -> Period:
        try:
            return next(period for period in self.periods if period.id == period_id)
        except StopIteration as excpt:
            raise KeyError(f"'{period_id}'") from excpt

    def processed_periods(
        self, production_datetime: Datetime
    ) -> CompositePeriodCollection:
        return CompositePeriodCollection(
            periods=[
                period.processed_period(production_datetime) for period in self.periods
            ]
        )
