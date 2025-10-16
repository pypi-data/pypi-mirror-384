from __future__ import annotations

from abc import ABC
from typing import ClassVar, TypeVar

from pydantic import model_validator

from mfire.settings import get_logger
from mfire.utils.date import Datetime, Timedelta
from mfire.utils.period import Period

from .mixins import SummaryKeysMixin

# Logging
LOGGER = get_logger(name=__name__, bind="wind_period")

WindElement = TypeVar("WindElement")


class WindPeriod(Period):
    DURATION_LOWER_BOUND: ClassVar[Timedelta] = Timedelta(hours=1)

    @model_validator(mode="after")
    def check_times(self):
        if self.end_time < self.begin_time + self.DURATION_LOWER_BOUND:
            raise ValueError(
                f"end_time has to be >= begin_time + {self.DURATION_LOWER_BOUND}h and "
                f"this is not the case: begin_time: '{self.begin_time}', "
                f"end_time: '{self.end_time}' !"
            )
        return self


class BaseWindPeriod(SummaryKeysMixin, WindPeriod, ABC):
    """BaseWindPeriod abstract class."""

    def check_dates_before_adding(self, other: BaseWindPeriod):
        if self.end_time > other.begin_time:
            raise ValueError(
                f"Try to update a {self.__class__.__name__} with another which has a "
                f"too early begin_time: {self.end_time} > {other.begin_time} !"
            )

    def summarize(self, reference_datetime: Datetime) -> dict:
        return {
            self.START_K: Period(begin_time=self.begin_time).describe(
                reference_datetime, "Europe/Paris", "fr"
            ),
            self.STOP_K: Period(begin_time=self.end_time).describe(
                reference_datetime, "Europe/Paris", "fr"
            ),
        }
