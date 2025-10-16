from __future__ import annotations

import datetime
import re
from typing import Any, Optional

import dateutil.parser
import numpy as np

import mfire.utils.mfxarray as xr
from mfire.utils.template import TemplateRetriever

LOCAL_TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo


class Datetime(datetime.datetime):
    """
    This class inherits from `datetime.datetime` and provides additional methods and
    functionalities for manipulating and formatting dates and times."""

    @staticmethod
    def _ldt_tzkw_1_arg(*args, **kwargs):
        top = args[0]
        tz_kw = kwargs.get("tzinfo", datetime.timezone.utc)
        ndt = None
        ldt = []
        if top is NotImplemented:
            return NotImplemented
        if isinstance(top, bytes):
            top = datetime.datetime(top)
        if isinstance(top, xr.DataArray):
            top = top.values
        if isinstance(top, datetime.datetime):
            if top.tzinfo:
                tz_kw = top.tzinfo
            ldt = [
                top.year,
                top.month,
                top.day,
                top.hour,
                top.minute,
                top.second,
                top.microsecond,
            ]
        elif isinstance(top, str):
            ndt = dateutil.parser.parse(top)
        elif isinstance(top, (int, float)):
            ndt = datetime.datetime.fromtimestamp(top, datetime.timezone.utc)
        elif isinstance(top, np.datetime64):
            timestamp = (top - np.datetime64("1970-01-01T00:00:00")) / np.timedelta64(
                1, "s"
            )
            ndt = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)

        if isinstance(ndt, datetime.datetime):
            if ndt.tzinfo:
                tz_kw = ndt.tzinfo
            ldt = [
                ndt.year,
                ndt.month,
                ndt.day,
                ndt.hour,
                ndt.minute,
                ndt.second,
                ndt.microsecond,
            ]
        return ldt, tz_kw

    @staticmethod
    def _ldt_tzkw_several_args(*args, **kwargs):
        ldt = [int(x) if isinstance(x, (int, float)) else x for x in args]
        tz_kw = kwargs.get("tzinfo", datetime.timezone.utc)
        if len(ldt) == 8:
            tz_kw = ldt.pop()
            if tz_kw is None:
                tz_kw = datetime.timezone.utc
        return ldt, tz_kw

    def __new__(cls, *args, **kwargs):
        if kwargs and not args:
            args = (datetime.datetime(**kwargs),)
        if not args:
            return Datetime.now(
                datetime.timezone.utc
            )  # https://rules.sonarsource.com/python/RSPEC-6903/

        func = cls._ldt_tzkw_1_arg if len(args) == 1 else cls._ldt_tzkw_several_args
        ldt, tz_kw = func(*args, **kwargs)
        if not ldt:
            raise ValueError("Datetime value unknown")
        return datetime.datetime.__new__(cls, *ldt, tzinfo=tz_kw)

    def __str__(self) -> str:
        return self.isoformat()

    def __add__(self, delta: Timedelta) -> Datetime:
        """
        Add to a Datetime object the specified delta

        Args:
            delta: Delta to add

        Returns:
            Added new datetime
        """
        return Datetime(super().__add__(delta))

    def __radd__(self, delta: Timedelta) -> Datetime:
        return self.__add__(delta)

    def __sub__(self, delta: Timedelta | Datetime) -> Datetime | Timedelta:
        """
        Subtract to a Date object the specified delta

        Args:
            delta: Delta to subtract
                - if a Datetime, returns a Timedelta
                - if a Timedelta, returns a Datetime

        Returns:
            Subtracted value
        """
        subtract = super().__sub__(delta)
        if isinstance(delta, Datetime):
            return Timedelta(subtract)
        return Datetime(subtract)

    def __rsub__(self, delta: Datetime) -> Timedelta:
        return Timedelta(delta.__sub__(self))

    def astimezone(self, tz: datetime.tzinfo = LOCAL_TIMEZONE) -> Datetime:
        """
        Convert to local time in new timezone tz

        Args:
            tz: Timezone object. Defaults to LOCAL_TIMEZONE.

        Returns:
            New datetime
        """
        return Datetime(super().astimezone(tz=tz))

    @classmethod
    def now(cls, tz: datetime.tzinfo = LOCAL_TIMEZONE) -> Datetime:
        """
        Returns the current local datetime.

        Args:
            tz: Timezone object. Defaults to LOCAL_TIMEZONE.

        Returns:
            Current local datetime
        """
        return Datetime(datetime.datetime.now(tz))

    @property
    def utc(self) -> Datetime:
        """convert local time in utc timezone

        Returns:
            Datetime: Utc datetime
        """
        return self.astimezone(tz=datetime.timezone.utc)

    @property
    def rounded(self) -> Datetime:
        """rounded : returns the actual datetime o'clock

        Returns:
            Datetime : Actual Datetime o'clock
        """
        return Datetime(self.year, self.month, self.day, self.hour, tzinfo=self.tzinfo)

    @property
    def midnight(self) -> Datetime:
        """midnight : returns midnight's time of the self date

        Returns:
            Datetime: midnight time of self date
        """
        return Datetime(self.year, self.month, self.day, tzinfo=self.tzinfo)

    @property
    def calendar_date(self) -> Datetime:
        """calendar_date: returns the calendar date of the given self.
        Example : Datetime(2021, 6, 28, 9, 4) calendar date is Datetime(2021, 6, 28)

        Returns:
            Datetime: calendar date
        """
        return Datetime(self.year, self.month, self.day, tzinfo=self.tzinfo)

    def is_same_day(self, other_datetime: Datetime) -> bool:
        """is_same_day: returns True if the self datetime and the given
        other datetime share the same calendar date.

        Args:
            other_datetime: Other datetime to compare

        Returns:
            bool: True if the self datetime and the given other datetime
                share the same calendar date.
        """
        return self.calendar_date == Datetime(other_datetime).calendar_date

    @property
    def as_datetime(self) -> datetime.datetime:
        """return the datetime to the datetime.datetime format

        Returns:
            datetime.datetime: datetime object
        """
        return datetime.datetime(
            self.year,
            self.month,
            self.day,
            self.hour,
            self.minute,
            self.second,
            self.microsecond,
            self.tzinfo,
        )

    @property
    def without_tzinfo(self) -> Datetime:
        return self.utc.replace(tzinfo=None)

    @property
    def as_np_dt64(self) -> np.datetime64:
        """Return the self datetime to the np.datetime64 format.
        Made for preventing np.datetime64 warning of conversion
        of timezone-aware datetimes.

        Returns:
            np.datetime64: self with a np.datetime64 format.
        """
        return np.datetime64(self.without_tzinfo).astype("datetime64[ns]")

    def is_synoptic(self) -> bool:
        return self.hour in (0, 6, 12, 18)

    def table(self, language: str) -> Any:
        return TemplateRetriever.table_by_name("date", language)

    def weekday_name(self, language: str) -> str:
        """
        Returns a Day type object corresponding to the actual weekday of the date.

        Args:
            language: Selected language.

        Returns:
            Actual weekday's name
        """
        return self.table(language)["weekdays"][self.weekday()]

    def month_name(self, language: str) -> str:
        """
        Returns a Month type object corresponding to the actual month of the date.

        Args:
            language: Selected language.

        Returns:
            Actual month's name
        """
        return self.table(language)["months"][self.month - 1]

    def literal_day(self, language: str, display_year: Optional[bool] = True) -> str:
        """literal_day : returns the actual date's day literal description

        Args:
            language: Selected language.
            display_year: Whether to display the year or not. Defaults to True.

        Returns:
            Day literal description
        """
        numday = str(self.day)
        numday += self.table(language)["numdays"].get(
            numday, self.table(language)["numdays"].get("*", "")
        )

        year = ""
        if display_year:
            year = str(self.year)

        return (
            self.table(language)["literal_date"]
            .format(
                weekday=self.weekday_name(language),
                numday=numday,
                month=self.month_name(language),
                year=year,
            )
            .strip()
        )

    def moment(self, language: str) -> dict:
        """
        Returns a Moment type object corresponding to the corresponding moment in the
        day.

        Args:
            language: Selected language.

        Returns:
            Corresponding Moment type object.
        """
        moments = sorted(
            [
                (moment, dico["start"])
                for moment, dico in self.table(language)["moments"].items()
            ],
            key=lambda x: x[1],
            reverse=True,
        )
        moment = next(
            (moment for moment, start in moments if self.hour >= start), moments[0][0]
        )
        return self.table(language)["moments"][moment]

    def format_bracket_str(self, bracket_str: Any) -> str:
        """Replace date tags in brackets like, '[date]' or
        '[date-1]' in a str by the self formatted datetime.

        Args:
            bracket_str: String containing '[date]', '[date+n]' or '[date-m]' patterns
                with 'n' and 'm' being natural integers.

        Returns:
            Formatted string
        """
        if not isinstance(bracket_str, str):
            return bracket_str
        return re.sub(
            r"\[date(|[-+]\d*)\]",
            lambda x: str((self + Timedelta(days=int(x.group(1) or "0"))).midnight),
            bracket_str,
        )

    def describe_day(self, request_time: Datetime, language: str) -> str:
        """
        Describes textually the self.day with the point of view of a given requested
        datetime.
        >>> d0 = Datetime(1996, 4, 17, 12)
        >>> print(d0.describe(d0, "fr"))
        "aujourd'hui"
        >>> d0.describe(Datetime(1996, 4, 16), "fr")
        "demain"
        >>> d0.describe(Datetime(1996, 4, 18), "fr")
        "hier"
        >>> d0.describe(Datetime(1996, 4, 15), "fr")
        "mercredi"
        >>> d0.describe(Datetime.now(), "fr")
        "mercredi 17 avril 1996"

        Args:
            request_time: Point of view to describe the day.
            language: Selected language

        Returns:
            str: Textual description.
        """
        days_delta = (self.midnight - request_time.midnight).days
        day_name = self.weekday_name(language)

        if days_delta < -1 or days_delta > 6:
            display_year = self.year != request_time.year
            day_name = self.literal_day(language, display_year=display_year)
            usage = self.table(language)["week_shifts"]["usage"]
            if days_delta == 7:
                day_name = usage.format(
                    day=self.weekday_name(language),
                    shift=self.table(language)["week_shifts"]["next"],
                )
            elif -8 < days_delta < -1:
                day_name = usage.format(
                    day=self.weekday_name(language),
                    shift=self.table(language)["week_shifts"]["last"],
                )
        return day_name

    def describe_moment(self, request_time: Datetime, language: str) -> str:
        """
        Describes textually the moment with the point of view of a given requested
        datetime.
        >>> d0 = Datetime(2021, 4, 15, 10)
        >>> print(d0.describe_moment(d0, "fr"))
        "ce matin"
        >>> d0.describe_moment(Datetime(2021, 4, 11))
        "matin"
        >>> d1 = Datetime(2021, 4, 15, 19)
        >>> d1.describe_moment(Datetime(2021, 4, 15))
        "ce soir"
        >>> d1.describe_moment(Datetime(2021, 4, 18))
        "soir"

        Args:
            request_time: Point of view to describe the moment.
            language: Selected language

        Returns:
            str: Textual description.
        """
        days_delta = (self.midnight - request_time.midnight).days
        start_min = np.min(
            [moment["start"] for moment in self.table(language)["moments"].values()]
        )
        if days_delta == 0:
            start_max = np.max(
                [moment["start"] for moment in self.table(language)["moments"].values()]
            )
            # exclude evening night if morning night possible
            if self.hour < start_max or request_time.hour > start_min:
                return self.moment(language)["demo"]
        if days_delta == 1 and self.hour < start_min < request_time.hour:
            return self.moment(language)["demo"]

        if days_delta < -1 or days_delta > 6:
            return self.moment(language)["circ"]["all"]

        return self.moment(language)["name"]

    def describe(self, request_time: Datetime, language: str) -> str:
        """
        Returns a descriptions of self from the requested perspective.
        Exemple :
        >>> reference_time = Datetime(2021, 2, 12)
        >>> begin_time = Datetime(2021, 2, 13, 9)
        >>> end_time = Datetime(2021, 2, 14, 21)
        >>> begin_time.describe(reference_time, "fr")
        "demain matin"
        >>> end_time.describe(reference_time, "fr")
        "dimanche soir"

        Args:
            request_time: reference datetime from which perspective the description must
                be done
            language: Selected language

        Returns:
            Textual description of the datetime
        """
        moment_name = self.describe_moment(request_time, language)
        if moment_name == self.moment(language)["demo"]:
            return moment_name

        day_name = self.describe_day(request_time, language)
        if self.moment(language) != self.table(language)["moments"]["night"]:
            return f"{day_name} {moment_name}"

        # Handle night datetime
        if self.hour < 12:
            return self.table(language)["overnight"].format(
                weekday=Datetime(self - Timedelta(days=1)).weekday_name(language),
                weekday_p1=self.weekday_name(language),
            )

        return self.table(language)["overnight"].format(
            weekday=day_name,
            weekday_p1=Datetime(self + Timedelta(days=1)).describe_day(
                request_time, language
            ),
        )


class Timedelta(datetime.timedelta):
    """
    Overlayer of the built-in datetime.timedelta class for more versatility, and for
    custom Datetime compatibility
    """

    def __new__(cls, *args, **kwargs):
        if kwargs:
            args = (datetime.timedelta(**kwargs),)
        if not args:
            raise ValueError("No initial value provided for Timedelta")
        top = args[0]
        ld = []
        if top is NotImplemented:
            return NotImplemented
        if isinstance(top, datetime.timedelta):
            ld = [top.days, top.seconds, top.microseconds]
        elif len(args) >= 1:
            ld = list(args)
        return datetime.timedelta.__new__(cls, *ld)

    def __add__(self, delta: Timedelta) -> Timedelta:
        return Timedelta(super().__add__(delta))

    def __sub__(self, delta: Timedelta) -> Timedelta:
        return Timedelta(super().__sub__(delta))

    def __rsub__(self, delta: Timedelta) -> Timedelta:
        return Timedelta(delta.__sub__(self))

    def __mul__(self, factor: int | float) -> Timedelta:
        return Timedelta(super().__mul__(factor))

    def __rmul__(self, factor: int | float) -> Timedelta:
        return self * factor

    def __neg__(self) -> Timedelta:
        return Timedelta(0) - self

    @property
    def total_hours(self) -> int:
        """Get the number of hours like self.total_seconds of `datetime.datetime`

        Returns:
            int: Number of total hours
        """
        return int(self.total_seconds() // 3600)
