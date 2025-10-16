"""Module for manipulating names of areas defined by their altitude.

It considers areas as a given type of Intervals, and it is then possible
to combine them (union, intersection, difference) as you can expect from any interval.

There is also functions and methods to combine altitude-defined areas with other
areas.
"""

from __future__ import annotations

import re
from numbers import Real
from operator import itemgetter
from typing import Iterable, Optional, Tuple

import numpy as np

from mfire.settings import ALT_MAX, ALT_MIN

# defining useable class function outside the module
__all__ = ["AltitudeInterval"]

from mfire.utils.string import _, concatenate_string


class Segment(tuple):
    def __new__(cls, inf: Real, sup: Real):
        if np.isnan(inf) or np.isnan(sup):
            return tuple.__new__(cls, (-np.inf, +np.inf))
        return tuple.__new__(cls, (inf, sup))

    @property
    def inf(self):
        return self[0]

    @property
    def sup(self):
        return self[1]


class AltitudeInterval(tuple):
    """Class implementing an Altitude Interval in order to apply interval
    arithmetic to altitude's names fusion.
    We extend the class in order to bring some basic algebra of sets to intervals
    (because we, in our case, tend to consider intervals as sets).
    """

    units: str = "m"

    def __new__(cls, *args):
        if len(args) == 1 and isinstance(args[0], cls):
            return args[0]

        def make_segment(x, y=None):
            return cls.cast(x) if y is None else cls.hull((cls.cast(x), cls.cast(y)))

        return cls.union(
            make_segment(*x if hasattr(x, "__iter__") else (x,)) for x in args
        )

    @classmethod
    def new(cls, segments):
        return tuple.__new__(cls, segments)

    @classmethod
    def cast(cls, x: Real) -> tuple:
        """
        Cast a scalar to an interval. If the argument is an interval, it is returned
        unchanged.

        Args:
            x: Real to cast.

        Returns:
            Interval or argument if it's already an interval.
        """
        if isinstance(x, cls):
            return x
        return cls.new((Segment(x, x),))

    @classmethod
    def _canonical(cls, segments):
        segments = [c for c in segments if c.inf <= c.sup]
        segments.sort(key=itemgetter(0))
        new_segments = []
        for c in segments:
            if not new_segments or c.inf > new_segments[-1].sup:
                new_segments.append(c)
            elif c.sup > new_segments[-1].sup:
                new_segments[-1] = Segment(new_segments[-1].inf, c.sup)
        return cls.new(new_segments)

    @classmethod
    def union(cls, intervals: Iterable[AltitudeInterval]) -> AltitudeInterval:
        """
        Returns the union of the specified intervals.
        This class method is equivalent to the repeated use of the | operator.
            >>> AltitudeInterval.union([AltitudeInterval([1, 3], [4, 6]),
            >>>                         AltitudeInterval([2, 5], 9)])
            AltitudeInterval([1.0, 6.0], [9.0])
            >>> AltitudeInterval([1, 3], [4, 6]) | AltitudeInterval([2, 5], 9)
            AltitudeInterval([1.0, 6.0], [9.0])

        Args:
            intervals: Intervals to make the union

        Returns:
            Union of given intervals.
        """
        return cls._canonical(c for i in intervals for c in i)

    @classmethod
    def hull(cls, intervals: Iterable[AltitudeInterval]) -> AltitudeInterval:
        """
        Returns the hull of the specified intervals.
        The hull of a set of intervals is the smallest connected
        interval enclosing all the intervals.
            >>> AltitudeInterval.hull((AltitudeInterval([1, 3]),
            >>>                        AltitudeInterval([10, 15])))
            AltitudeInterval([1.0, 15.0])
            >>> AltitudeInterval.hull([AltitudeInterval((1, 2))])
            AltitudeInterval([1.0, 2.0])

        Args:
            intervals: Iteration of intervals to make the hull

        Returns:
            The hull of all intervals
        """
        segments = [c for i in intervals for c in i]
        return cls.new(
            (Segment(min(c.inf for c in segments), max(c.sup for c in segments)),)
        )

    def __repr__(self):
        return self.format("%r")

    def __str__(self):
        return self.__repr__()

    def format(self, fs: str) -> str:
        """
        Formats into a string using fs as format for the interval bounds.
        The argument fs can be any string format valid with floats:
            >>> interval[-2.1, 3.4].format("%+g")
            'interval([-2.1, +3.4])'

        Args:
            fs: Expected format string.

        Returns:
            Formatted string.
        """
        return (
            type(self).__name__
            + "("
            + ", ".join(
                "[" + ", ".join(fs % x for x in sorted(set(c))) + "]" for c in self
            )
            + ")"
        )

    def __neg__(self):
        return self.new(Segment(-x.sup, -x.inf) for x in self)

    def __and__(self, other):
        return self._canonical(
            Segment(max(x.inf, y.inf), min(x.sup, y.sup))
            for x in self
            for y in self.cast(other)
        )

    def __or__(self, other):
        return self.union((self, self.cast(other)))

    def __contains__(self, other):
        return all(
            any(x.inf <= y.inf and y.sup <= x.sup for x in self)
            for y in self.cast(other)
        )

    def __invert__(self) -> AltitudeInterval:
        """Implementation of the unary operator '~' used to invert an interval.
        We define the "inverse" of an interval I as:
        * I | ~I == [-inf, inf] (i.e. union(I, ~I) = everything)
        * I & ~I == singleton(min(I)), singleton(max(I))
            if min(I) != -inf and max(I) != inf

        For example:
        >>> ~AltitudeInterval([-inf, 0])
        AltitudeInterval([0, inf])
        >>> ~AltitudeInterval([0, 100])
        AltitudeInterval([-inf, 0], [100, inf])
        >>> ~AltitudeInterval([0])
        AltitudeInterval([-inf, inf])
        >>> ~AltitudeInterval([-inf, 0], [100, 200], [300], [400, inf])
        AltitudeInterval([0, 100], [200, 400])

        Returns:
            AltitudeInterval: Inverted (or complementary) of self
        """
        bounds = [-np.inf] + [b for comp in self for b in comp] + [np.inf]
        return self.__class__(
            *(
                (bounds[i], bounds[i + 1])
                for i in range(0, len(bounds), 2)
                if bounds[i] != np.inf and bounds[i + 1] != -np.inf
            )
        )

    def difference(self, other: AltitudeInterval) -> AltitudeInterval:
        """Implementation of the "set's" corresponding difference.
        It returns a new AltitudeInterval with segments of self that are not in other.

        For instance:
        >>> AltitudeInterval([0, 1000]).difference([500, inf])
        AltitudeInterval([0, 500])

        !Warning: Do not use the operator '-' for this difference. Indeed, the
        __sub__ dunder method is already used for applying the arithmetic subtraction.

        Args:
            other:: Other interval to apply difference to

        Returns:
            New subtracted AltitudeInterval
        """
        return self & (~self.__class__(other))

    def __xor__(self, other: AltitudeInterval) -> AltitudeInterval:
        """Implementation of the "set's" corresponding symmetric_difference.
        It returns a new AltitudeInterval with segments in either the self
        or other but not both.

        Args:
            other: Other interval to apply the difference to.

        Returns:
            AltitudeInterval: New symmetrically subtracted AltitudeInterval
        """
        return self.difference(other) | self.__class__(other).difference(self)

    def symmetric_difference(self, other: AltitudeInterval) -> AltitudeInterval:
        """Implementation of the "set's" corresponding symmetric_difference.
        It returns a new AltitudeInterval with segments in either the self
        or other but not both.

        Args:
            other: Other interval to apply the difference to.

        Returns:
            AltitudeInterval: New symmetrically subtracted AltitudeInterval
        """
        return self ^ other

    def is_sub_interval(self, other: AltitudeInterval) -> bool:
        """Test whether the self interval is a sub interval of the other interval,
        i.e. self is a subset of the other set.

        Args:
            other: Other set to test the inclusion with.

        Returns:
            bool: True if self is a sub-interval of other, else False
        """
        return (self & self.__class__(other)) == self

    def is_super_interval(self, other: AltitudeInterval) -> bool:
        """Test whether the self interval is a super interval of the other interval,
        i.e. other is a subset of the self set.

        Args:
            other: Other set to test the inclusion with.

        Returns:
            bool: True if self is a super-interval of other, else False
        """
        other_interval = self.__class__(other)
        return (self & other_interval) == other_interval

    @classmethod
    def name_segment(
        cls,
        segment: Tuple[Optional[float], Optional[float]],
        language: str,
        alt_min: Optional[int] = ALT_MIN,
        alt_max: Optional[int] = ALT_MAX,
    ) -> str:
        """Method used for naming a single segment of an interval.

        Examples:
        >>> AltitudeInterval.name_segment((-np.inf, 1000), "fr")
        "en dessous de 1000 m"
        >>> AltitudeInterval.name_segment((1000, np.inf), "fr")
        "au-dessus de 1000 m"
        >>> AltitudeInterval.name_segment((1000, 2000), "fr")
        "entre 1000 m et 2000 m"
        >>> AltitudeInterval.name_segment((1000, 2000), "fr", alt_max=2000)
        "au-dessus de 1000 m"
        >>> AltitudeInterval.name_segment((1000, 1000), "fr")
        "à 1000 m"

        Args:
            segment: Tuple of (low, high) altitude values to name.
            language: Selected language.
            alt_min: Alt min boundary. Defaults to ALT_MIN.
            alt_max: Alt max boundary. Defaults to ALT_MAX.

        Returns:
            Name of the given segment.
        """
        alt_min = int(alt_min) if alt_min is not None else ALT_MIN
        alt_max = int(alt_max) if alt_max is not None else ALT_MAX
        low, high = (int(v) if abs(v) != np.inf else v for v in segment)

        if low == high and low > alt_min and high < alt_max:
            return f"{_('à', language)} {low} {cls.units}"
        if alt_min < low < alt_max <= high:
            return f"{_('au-dessus de', language)} {low} {cls.units}"
        if low <= alt_min < high < alt_max:
            return f"{_('en dessous de', language)} {high} {cls.units}"
        if alt_min < low < high < alt_max:
            return (
                f"{_('entre', language)} {low} {cls.units} {_('et', language)} {high}"
                f" {cls.units}"
            )
        return ""

    def name(
        self,
        language: str,
        alt_min: Optional[int] = ALT_MIN,
        alt_max: Optional[int] = ALT_MAX,
    ) -> str:
        """Method for naming self interval. It basically concatenates the names
        of each of its segments.

        Examples:
        >>> inter = AltitudeInterval((-inf, 100), (200, 300), (400), (500, 1000))
        >>> inter.name()
        "en dessous de 100 m, entre 200 m et 300 m, à 400 m et entre 500 m et 1000 m"
        >>> inter.name(alt_max=1000)
        "en dessous de 100 m, entre 200 m et 300 m, à 400 m et au-dessus de 500 m"
        >>> inter.name(alt_min=400, alt_max=800)
        "au-dessus de 500 m"

        Args:
            language: Selected language.
            alt_min: Alt min boundary. Defaults to ALT_MIN.
            alt_max: Alt max boundary. Defaults to ALT_MAX.

        Returns:
            Name of the self interval.
        """
        new_self = self & self.__class__((alt_min, alt_max))
        segments = [
            self.name_segment((low, high), language, alt_min=alt_min, alt_max=alt_max)
            for low, high in new_self
            if not (low == high and (low <= alt_min or high >= alt_max))
        ]  # we exclude singletons that are equals to alt_min or alt_max
        if len(segments) == 0:
            return ""

        return concatenate_string(segments, last_delimiter=f" {_('et', language)} ")

    @classmethod
    def rename(
        cls,
        name: str,
        language: str,
        alt_min: Optional[int] = ALT_MIN,
        alt_max: Optional[int] = ALT_MAX,
    ):
        interval = cls.from_name(name, language)
        if bool(interval):
            return interval.name(language, alt_min=alt_min, alt_max=alt_max)
        return name

    @classmethod
    def from_name(cls, name: str, language: str) -> AltitudeInterval:
        """Class method that interpret a given 'my_str' into an AltitudeInterval.

        For instance,
        >>> AltitudeInterval.from_name("au-dessus de 800 m")
        AltitudeInterval([800.0, inf])
        >>> AltitudeInterval.from_name("entre 1000 m et 2000 m")
        AltitudeInterval([1000.0, 2000.0])
        >>> AltitudeInterval.from_name("à 200 m")
        AltitudeInterval([200.0, 200.0])
        >>> AltitudeInterval.from_name("en dessous de 450 m")
        AltitudeInterval([-inf, 450])
        >>> AltitudeInterval.from_name(
        ...     "en dessous de 100 m, entre 800 m et 900 m et au-dessus de 1000 m"
        ... )
        AltitudeInterval([-inf, 100], [800, 900], [1000, inf])
        >>>  AltitudeInterval.from_name("à Toulouse")
        AltitudeInterval()

        Args:
            name: String to convert as an AltitudeInterval
            language: Selected language.

        Returns:
            New AltitudeInterval built from given name.
        """
        alt_inter = cls()

        under_w = _("en dessous de", language)
        between_w = _("entre", language)
        and_w = _("et", language)
        to_w = _("à", language)
        over_w = _("au-dessus de", language)
        pattern = re.compile(
            rf"(?:{under_w} (\d+) m)"
            rf"|(?:{between_w} (\d+) m {and_w} (\d+) m)"
            rf"|(?:{to_w} (\d+) m)"
            rf"|(?:{over_w} (\d+) m)"
        )
        for match in pattern.finditer(str(name)):
            match_name = match.group(0)
            values = [int(v) for v in match.groups() if v is not None]
            if under_w in match_name:
                alt_inter |= cls([-np.inf, values[0]])
            elif over_w in match_name:
                alt_inter |= cls([values[0], np.inf])
            elif between_w in match_name or to_w in match_name:
                alt_inter |= cls(values)
        return alt_inter
