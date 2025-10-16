from __future__ import annotations

from itertools import product
from typing import Any, Generator, Iterable, Optional
from zoneinfo import ZoneInfo

import numpy as np
from pydantic import field_validator, model_validator

from mfire.composite.base import BaseComposite, BaseModel
from mfire.composite.serialized_types import s_datetime
from mfire.utils.calc import round_to_next_multiple
from mfire.utils.date import Datetime, Timedelta
from mfire.utils.template import TemplateRetriever


class Period(BaseModel):
    """
    Class describing periods objects defined by :
    - a beginning (self.begin_time)
    - an end (self.end_time)
    """

    begin_time: s_datetime
    end_time: Optional[s_datetime] = None

    @field_validator("begin_time", "end_time", mode="before")
    def init_times(cls, v: str) -> Datetime:
        """
        Validator function to initialize the datetimes.

        Args:
            v: Value of the beginning or end time

        Returns:
            Datetime: Validated and initialized datetime value.
        """
        return Datetime(v)

    @model_validator(mode="after")
    def init_end_time(self) -> Period:
        if self.end_time is None:
            self.end_time = self.begin_time
        return self

    def __eq__(self, obj: Period) -> bool:
        return self.begin_time == obj.begin_time and self.end_time == obj.end_time

    @property
    def total_hours(self) -> int:
        return self.duration.total_hours

    @property
    def days(self) -> int:
        return round_to_next_multiple(self.duration.total_seconds() / 86400, 1)

    @property
    def duration(self) -> Timedelta:
        return self.end_time - self.begin_time

    def table(self, language: str) -> Any:
        return TemplateRetriever.get_by_name("period", language, force_centroid=True)

    def date_table(self, language: str) -> Any:
        return self.begin_time.table(language)

    def basic_union(self, period: Period) -> Period:
        """
        Creates the basic union of self and a given period.
        Example:
        >>> p1 = Period(Datetime(2021, 1, 1), Datetime(2021, 1, 2))
        >>> p2 = Period(Datetime(2021, 1, 3), Datetime(2021, 1, 4))
        >>> p1.basic_union(p2)
        Period(Datetime(2021, 1, 1), Datetime(2021, 1, 4))

        Args:
            period: given period to unite with self.

        Returns:
            Basic union of periods.
        """
        return self.__class__(
            begin_time=min(self.begin_time, period.begin_time),
            end_time=max(self.end_time, period.end_time),
        )

    def union(self, period: Period) -> Periods:
        """
        Creates the union of self and a given period.
        Example:
        >>> p1 = Period(Datetime(2021, 1, 1, 10), Datetime(2021, 1, 1, 15))
        >>> p2 = Period(Datetime(2021, 1, 1, 16), Datetime(2021, 1, 1, 18))
        >>> p3 = Period(Datetime(2021, 1, 1, 12), Datetime(2021, 1, 1, 17))
        >>> p1.basic_union(p2)
        Periods([p1, p2])
        >>> p1.basic_union(p3)
        Periods([Period(Datetime(2021, 1, 1, 10), Datetime(2021, 1, 1, 17))])

        Args:
            period: given period to unite with self.

        Returns:
            Union of the period (length 1 if intersection 2 otherwise)
        """
        if self.intersects(period):
            return Periods([self.basic_union(period)])
        if self.begin_time < period.begin_time:
            return Periods([self, period])
        return Periods([period, self])

    def intersects(self, period: Period) -> bool:
        """
        Checks whether a given period intersects with self.
        Example:
        >>> p1 = Period(Datetime(2021, 1, 1), Datetime(2021, 1, 2))
        >>> p2 = Period(Datetime(2021, 1, 3), Datetime(2021, 1, 4))
        >>> p3 = Period(Datetime(2021, 1, 1, 23), Datetime(2021, 1, 2, 23))
        >>> p1.intersects(p2)
        False
        >>> p1.intersects(p3)
        >>> p1.intersects(p3)
        True
        >>> p2.intersects(p3)
        False

        Args:
            period: given period to check whether it intersects self.

        Returns:
            bool: Whether period intersects with self.
        """
        return (
            period.begin_time <= self.begin_time <= period.end_time
            or self.begin_time <= period.begin_time <= self.end_time
        )

    def intersection(self, period: Period) -> Timedelta:
        """
        Gives the TimeDelta of the intersection a given period intersects and self
        Example:
        >>> p1 = Period(Datetime(2021, 1, 1, 10), Datetime(2021, 1, 1, 12))
        >>> p2 = Period(Datetime(2021, 1, 1, 11), Datetime(2021, 1, 1, 15))
        >>> p3 = Period(Datetime(2021, 1, 1, 12), Datetime(2021, 1, 1, 16))
        >>> p1.intersects(p2)
        Timedelta(hours=1)
        >>> p1.intersects(p3)
        Timedelta(hours=0)
        >>> p2.intersects(p3)
        Timedelta(hours=3)

        Args:
            period: given period to do the intersection

        Returns:
            The Timedelta of the intersection between self and period or None if no
            intersection.
        """
        if not self.intersects(period):
            return Timedelta(0)
        return Timedelta(
            min(self.end_time, period.end_time)
            - max(self.begin_time, period.begin_time)
        )

    def extends(
        self, period: Period, language: str, request_time: Optional[Datetime] = None
    ) -> bool:
        """
        Checks whether a given period is an extension of self. We consider that a period
        p1 extends another period p2 if the period (p1 +/- 3H) intersects the period
        (p2 +/- 3H) or if the jonctions have the same textual descriptions.
        Example:
        >>> p1 = Period(Datetime(2021, 1, 1), Datetime(2021, 1, 2))
        >>> p2 = Period(Datetime(2021, 1, 3), Datetime(2021, 1, 4))
        >>> p3 = Period(Datetime(2021, 1, 1, 23), Datetime(2021, 1, 2, 23))
        >>> p1.extends(p2)
        False
        >>> p1.extends(p3)
        True
        >>> p2.extends(p3)
        True

        Args:
            period: period to check whether it extends self.
            language: Selected language.
            request_time: Point of view for textual descriptions. Defaults to None.

        Returns:
            Whether the given period and self extend themselves.
        """
        return (
            period.begin_time - Timedelta(hours=3)
            <= self.begin_time
            <= period.end_time + Timedelta(hours=3)
            or self.begin_time - Timedelta(hours=3)
            <= period.begin_time
            <= self.end_time + Timedelta(hours=3)
            or (
                request_time is not None
                and (
                    self.begin_time.describe(request_time, language)
                    == period.end_time.describe(request_time, language)
                    or self.end_time.describe(request_time, language)
                    == period.begin_time.describe(request_time, language)
                )
            )
        )

    def describe(self, request_time: Datetime, time_zone: str, language: str) -> str:
        """
        Provides a textual description of the self period
        according to a given request_time (point of view).

        Args:
            request_time: Point of view used for describing self.
            time_zone: Expected time zone.
            language: Selected language.

        Returns:
            Textual description of self.
        """
        time_zone = ZoneInfo(time_zone)
        request_time = Datetime(request_time).astimezone(time_zone)
        begin_time = self.begin_time.astimezone(time_zone)
        end_time = self.end_time.astimezone(time_zone)

        if self.total_hours <= 24:
            begin_diff = Timedelta(begin_time - request_time.midnight).total_hours

            if 0 <= begin_diff <= 31:
                tpl, key = self.table(language).get(
                    [
                        0,
                        request_time.hour,
                        begin_diff,
                        Timedelta(end_time - request_time.midnight).total_hours,
                    ],
                    return_centroid=True,
                )
                begin_time = request_time.midnight + Timedelta(hours=int(key[2]))
            else:
                tpl, key = self.table(language).get(
                    [
                        32 if begin_diff < 72 else 72,
                        request_time.hour,
                        begin_time.hour,
                        Timedelta(end_time - begin_time.midnight).total_hours,
                    ],
                    return_centroid=True,
                )
                begin_time = begin_time.replace(hour=int(key[2]))

            if "{weekday" in tpl:
                weekday_p1 = Datetime(begin_time + Timedelta(hours=24))
                weekday_p2 = Datetime(begin_time + Timedelta(hours=48))
                weekday_m1 = Datetime(begin_time - Timedelta(hours=24))

                tpl = tpl.format(
                    weekday=begin_time.weekday_name(language),
                    weekday_p1=weekday_p1.weekday_name(language),
                    weekday_p2=weekday_p2.weekday_name(language),
                    weekday_m1=weekday_m1.weekday_name(language),
                )
            return tpl

        return self.date_table(language)["literal_period"].format(
            date_1=begin_time.describe(request_time, language),
            date_2=end_time.describe(request_time, language),
        )

    def __repr__(self):
        return f"Period(begin_time={self.begin_time}, end_time={self.end_time})"

    def __str__(self):
        return self.__repr__()


class Periods(list[Period]):
    def __init__(self, iterable: Optional[Iterable] = None):
        if iterable is None:
            iterable = []
        super().__init__(iterable)

    def reduce(self, n: Optional[int] = None) -> Periods:
        """
        Reduces a Periods element. If n is given, at most n elements are kept.

        Args:
            n: Maximal number of period to keep, defaults to None.

        Returns:
            Reduced periods.
        """
        if len(self) == 0:
            return self

        new_periods = Periods()
        sorted_periods = sorted(self, key=lambda x: x.begin_time)
        begin = sorted_periods[0].begin_time
        end = sorted_periods[0].end_time

        for period in sorted_periods:
            if period.begin_time > end:
                new_periods.append(Period(begin_time=begin, end_time=end))
                begin = period.begin_time
            end = max(end, period.end_time)
        new_periods.append(Period(begin_time=begin, end_time=end))

        if n is not None:
            while len(new_periods) > n:
                basic_unions = [
                    new_periods[i].basic_union(new_periods[i + 1])
                    for i in range(len(new_periods) - 1)
                ]
                idx = np.argmin([union.total_hours for union in basic_unions])
                new_periods = Periods(
                    new_periods[:idx] + [basic_unions[idx]] + new_periods[idx + 2 :]
                )

        return new_periods

    def __iadd__(self, other):
        new_periods = self + other
        self[:] = new_periods
        return self

    def __add__(self, other) -> Periods:
        if len(self) == 0:
            return other
        if len(other) == 0:
            return self

        new_periods = Periods(super().__add__(other))
        return new_periods.reduce()

    @property
    def begin_time(self):
        return self[0].begin_time

    @property
    def end_time(self):
        return self[-1].end_time

    def intersects(self, periods: Periods) -> bool:
        return any(p1.intersects(p2) for p1, p2 in product(self, periods))

    def all_intersections(self, periods: Periods) -> Generator[Timedelta]:
        for p1, p2 in product(self, periods):
            inter = p1.intersection(p2)
            if inter:
                yield inter

    @property
    def total_hours(self) -> int:
        return sum(time_delta.total_hours for time_delta in self.all_timedelta)

    @property
    def total_days(self) -> int:
        if len(self) == 0:
            return 0

        min_start_time = min(p.begin_time for p in self)
        max_end_time = min(p.end_time for p in self)
        return 1 + (max_end_time - min_start_time).days

    @property
    def all_timedelta(self) -> Generator[Timedelta]:
        for p in self:
            yield Timedelta(p.end_time - p.begin_time)

    def hours_of_intersection(self, periods: Periods) -> int:
        """
        Gives the number of hours of intersection with another periods.

        Args:
            periods: Another periods.

        Returns:
            Number of hours of intersection.
        """
        summed_time = Timedelta(0)
        for intersection in self.all_intersections(periods):
            summed_time += intersection
        return summed_time.total_hours

    def hours_of_union(self, periods: Periods) -> int:
        """
        Gives the number of hours of union with another periods

        Args:
            periods: Another periods to make the union.

        Returns:
            Number of hours of the union.
        """
        hours_inter = self.hours_of_intersection(periods)
        return self.total_hours + periods.total_hours - hours_inter


class PeriodDescriber(BaseComposite):
    """
    Class for describing periods or sequences of periods.
    If a single period is given, the class will simply use the period.describe
    method.
    Else, if a sequence of periods is given, the period describer will first
    try to reduce the number of periods by merging those which extends themselves,
    and then will use the period.describe method on all the reduced periods.
    """

    cover_period: Period
    request_time: Datetime

    def __eq__(self, other):
        return (
            self.cover_period == other.cover_period
            and self.request_time == other.request_time
        )

    def reduce(self, periods: Periods, n: Optional[int] = None) -> Periods:
        """Reduces a sequence of periods to another sequence of periods, where those
        new periods are a merging of previous periods that extends themselves.

        Args:
            periods: Sequence of periods to reduce.
            n: number of periods that we want to keep

        Returns:
            Reduced periods.
        """
        new_periods = Periods()
        if len(periods) == 0:
            return new_periods

        is_me = (
            Timedelta(periods.begin_time - self.request_time.midnight).total_hours >= 72
        )
        current_period = periods[0]
        for period in periods[1:]:
            if period.extends(
                current_period, language=self.language, request_time=self.request_time
            ) or (
                is_me
                and period.begin_time <= current_period.end_time + Timedelta(hours=6)
            ):
                current_period = current_period.basic_union(period)
            else:
                new_periods += [current_period]
                current_period = period
        new_periods += [current_period]
        return new_periods.reduce(n)

    def describe(self, periods: Periods | Period) -> str:
        """
        Method for describing periods or sequences of periods. If a single period is
        given, the method will simply use the period.describe
        method. Else, if a sequence of periods is given, the period describer will first
        try to reduce the number of periods by merging those which extends themselves,
        and then will use the period.describe method on all the reduced periods.

        Args:
            periods: Periods to describe.

        Returns:
            Textual description of given period(s)
        """
        if isinstance(periods, Period):
            periods = Periods([periods])

        periods = self.reduce(periods)
        if periods.end_time < self.cover_period.begin_time + Timedelta(hours=3):
            return self._("en début de période")
        if periods.begin_time > self.cover_period.end_time - Timedelta(hours=3):
            return self._("en fin de période")
        if (
            len(periods) == 2
            and periods.begin_time < self.cover_period.begin_time + Timedelta(hours=3)
            and periods.end_time > self.cover_period.end_time - Timedelta(hours=3)
        ):
            if periods[0].end_time >= self.cover_period.begin_time + Timedelta(hours=3):
                temp1 = (
                    self._("jusqu'à")
                    + " "
                    + periods[0].end_time.describe(self.request_time, self.language)
                )
            else:
                temp1 = self._("en début de période")
            if periods[1].begin_time <= self.cover_period.end_time - Timedelta(hours=3):
                temp2 = (
                    self._("à partir de")
                    + " "
                    + periods[1].begin_time.describe(self.request_time, self.language)
                )
            else:
                temp2 = self._("en fin de période")

            return self._("{temp1} puis à nouveau {temp2}").format(
                temp1=temp1, temp2=temp2
            )

        return (
            self._describe_several(periods)
            if len(periods) > 1
            else self._describe_one(periods)
        )

    def _describe_one(self, periods: Periods):
        if (
            periods.begin_time <= self.cover_period.begin_time
            and periods.end_time >= self.cover_period.end_time
        ):
            return self._("sur toute la période")

        return periods[0].describe(
            self.request_time, time_zone=self.time_zone, language=self.language
        )

    def _describe_several_can_grouped(self, period: Period, first_moment: str) -> bool:
        mid_time = period.begin_time + (period.end_time - period.begin_time) / 2
        begin_time = min(period.begin_time + Timedelta(hours=3), mid_time)
        end_time = max(period.end_time - Timedelta(hours=3), mid_time)

        return (
            begin_time.moment(self.language)["name"] == first_moment
            and end_time.moment(self.language)["name"] == first_moment
        )

    def _describe_several(self, periods: Periods):
        first_moment = Datetime(periods[0].begin_time).moment(self.language)["name"]
        if 1 < self.cover_period.days <= len(
            {p.begin_time.midnight for p in periods}
        ) and all(self._describe_several_can_grouped(p, first_moment) for p in periods):
            return Datetime(periods[0].begin_time).moment(self.language)["all_names"]

        from mfire.utils.string import concatenate_string

        return concatenate_string(
            (
                p.describe(
                    self.request_time, time_zone=self.time_zone, language=self.language
                )
                for p in periods
            ),
            last_delimiter=f" {self._('puis')} ",
        )
