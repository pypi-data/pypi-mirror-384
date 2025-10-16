from __future__ import annotations

from functools import reduce
from typing import Optional

import numpy as np
import xarray as xr

from mfire.settings import get_logger
from mfire.text.synthesis.wind_reducers.wind.helpers import BaseWindPeriod
from mfire.utils.date import Datetime, Timedelta
from mfire.utils.geo import CompassRose8
from mfire.utils.period import Period

# Logging
LOGGER = get_logger(name=__name__, bind="wind_direction")


class WindDirection:
    """WindDirection class.

    This class defines an angle sector. Its angle cannot be >= 180°. This limitation
    can be accentuated with the class attribute ANGLE_MAX.
    """

    ANGLE_MAX: Optional[float] = None
    ROSE_NUM: int = 8
    SECTOR_ANGLE: float = 360.0 / ROSE_NUM
    HALF_ROSE_NUM: int = ROSE_NUM / 2

    def __init__(self, start: float, angle: Optional[float] = 0.0):
        self.start: float = start % 360.0
        self.angle: float = angle
        self.end: float = start

        if self.check_angle() is False:
            raise ValueError("Bad angle found !")

        self.end = (self.start + self.angle) % 360

    @classmethod
    def try_to_create(
        cls, start: float, angle: Optional[float] = 0.0
    ) -> Optional[WindDirection]:
        # Try to create a WindDirection of WindDirection. If an error is raised, it
        # returns None.
        try:
            return cls(start, angle)
        except ValueError:
            return None

    @property
    def middle(self) -> float:
        # Get the middle of the direction's angle.
        return round((self.end - self.angle / 2) % 360, 2)

    @property
    def code(self) -> int:
        # Get the code of the WindDirection.
        sector_num: float = self.middle // self.SECTOR_ANGLE
        codes: tuple[float, float] = sector_num, sector_num + 1

        if self.middle - codes[0] * 45 <= codes[1] * 45 - self.middle:
            code = codes[0]
        else:
            code = codes[1]
        return int(code % self.ROSE_NUM)

    @property
    def as_text(self) -> str:
        # Get the textual direction from the code attribute value.
        code: int = self.code
        return list(CompassRose8)[code].description("fr") if code is not None else ""

    def is_opposite_to(self, other: WindDirection) -> bool:
        """
        Checks if the WindDirection is the opposite of another WindDirection.

        This check is based on the code attribute. For example, WindDirections with
        code 0 and 4 are opposite but WindDirections with code 0 and 3 are not.

        Args:
            other: Another WindDirection to compare.

        Returns:
            True if given other is opposite to self, False otherwise.
        """
        return (
            self.code != other.code
            and (self.code - other.code) % self.HALF_ROSE_NUM == 0
        )

    def check_angle(self) -> bool:
        # Check if the angle is valid.
        if self.angle >= 180.0:
            return False
        if self.ANGLE_MAX is not None and self.angle > self.ANGLE_MAX:
            return False
        return True

    def compare(self, other: WindDirection) -> bool:
        # Compare the attributes of self and another WindDirection.
        return (
            isinstance(other, WindDirection)
            and self.start == other.start
            and self.angle == other.angle
        )

    def normalize(self, inplace: bool = True) -> WindDirection:
        start: float = self.code * self.SECTOR_ANGLE
        if inplace is True:
            self.__init__(start)  # pylint: disable=C2801
            return self
        return WindDirection(start)

    def __hash__(self):
        return hash(self.code)

    def __eq__(self, other: WindDirection) -> bool:
        return self.code == other.code

    def __add__(self, other: Optional[WindDirection]) -> Optional[WindDirection]:
        """
        Define the builtin add method.

        It returns the direction with the smallest angle sector covered by those of the
        2 input WindDirections.

        Args:
            other: Another WindDirection to add.

        Returns:
            Summed WindDirection.
        """
        if isinstance(other, WindDirection) is False:
            return None

        dirs: list[WindDirection] = [self, other]
        dirs.sort(key=lambda a: a.start)

        # Build the angle sector starting par dirs[0].start
        start: float = dirs[0].start
        end: float = max(dirs[0].start + dirs[0].angle, dirs[1].start + dirs[1].angle)

        # Build the angle sector starting par dirs[1].start
        alt_start: float = dirs[1].start
        alt_end: float = max(
            dirs[0].start + dirs[0].angle + 360, dirs[1].start + dirs[1].angle
        )

        # Kept the smallest angle sector
        if (alt_end - alt_start) < (end - start):
            start = alt_start
            end = alt_end

        return self.try_to_create(start, (end - start) % 360)

    def __repr__(self):
        return (
            f"WindDirection(start={self.start}, end={self.end}, angle={self.angle})"
            f", code={self.code}, text='{self.as_text}')"
        )


class Pcd(BaseWindPeriod):
    """Period with common Direction (Pcd) class."""

    wd: WindDirection

    def __eq__(self, other: Optional[Pcd]) -> bool:
        return super().__eq__(other) and self.wd == other.wd

    def __add__(self, other: Pcd) -> Optional[Pcd]:
        self.check_dates_before_adding(other)

        wd: Optional[WindDirection] = self.wd + other.wd
        if wd is None:  # noqa: S2583   We have to clean the code since sonar considers
            # that it is unreachable
            return None

        return Pcd(begin_time=self.begin_time, end_time=other.end_time, wd=wd)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.wd))

    def __repr__(self):
        s = (
            f"{self.__class__.__name__}(begin_time={self.begin_time}, "
            f"end_time={self.end_time}, duration={self.duration}, "
            f"wd={self.wd})"
        )
        return s

    @property
    def code(self) -> int:
        return self.wd.code

    def update(self, other: Pcd) -> bool:
        # Try to update the period with another period.
        try:
            period: Optional[Pcd] = self + other
        except ValueError:
            return False

        if period is None:
            return False

        self.end_time = period.end_time
        self.wd = period.wd
        return True

    def normalize_wd(self) -> Pcd:
        self.wd.normalize(inplace=True)
        return self

    def summarize(self, reference_datetime: Datetime) -> dict:
        summary: dict = super().summarize(reference_datetime)
        summary[self.WD_K] = self.wd.as_text

        return summary


def set_and_check_class_size(class_size: float) -> float:
    if 360.0 % class_size != 0.0:
        raise ValueError("class_size has to divide 360 !")
    return class_size


def set_and_check_class_nbr(shift: float) -> int:
    if 360.0 % shift != 0.0:
        raise ValueError("shift has to divide 360 !")
    return int(360 // shift)


class WindDirection120(WindDirection):
    """WindDirection120 class.

    This class defines an angle sector. Its angle has to be <= 120°. If not, a
    ValueError exception is raised during the initialization.
    """

    ANGLE_MAX: Optional[float] = 120  # 3 x 40


class PcdFinder:
    """PcdFinder class."""

    SHIFT: float = 10.0
    CLASS_SIZE: float = set_and_check_class_size(40.0)
    CLASSES_NBR: int = set_and_check_class_nbr(SHIFT)
    CLASS_PERCENT_MIN: float = 20.0
    WIND_DIRECTION_CLASS: type = WindDirection120
    KEEP_PCD_PERCENT_MIN: float = 50.0
    PERIOD_DURATION_MIN: Timedelta = Timedelta(hours=3)

    def __init__(self, dataset: xr.Dataset):
        self.monitoring_period: Optional[Period] = None
        self._term_periods: list[Pcd] = []
        self._pcd: list[Pcd] = []
        self._pcd_filtered: bool = False

        self._initialize_term_periods(dataset)

    def _initialize_term_periods(self, dataset: xr.Dataset) -> None:
        for valid_time in dataset.valid_time:
            term_dataset: xr.Dataset = dataset.sel(valid_time=valid_time)

            # Get term period
            term_period: Optional[Pcd] = self._get_term_period(term_dataset)

            self._term_periods.append(term_period)

        if self._term_periods:
            self.monitoring_period = Period(
                begin_time=Datetime(dataset.previous_time.values[0]),
                end_time=Datetime(dataset.valid_time.values[-1]),
            )

    @property
    def pcd(self) -> list[Pcd]:
        return self._pcd

    def _reset_pcd(self):
        self._pcd = []

    @staticmethod
    def _try_to_add_periods(p1: Optional[Pcd], p2: Optional[Pcd]) -> Optional[Pcd]:
        if p1 is None or p2 is None:
            return None
        return p1 + p2

    @classmethod
    def _get_term_period_loop(cls, class_nbr, class_cur, value) -> Optional[tuple]:
        if class_nbr > 0:
            upper_bound: float = class_cur[1] + cls.SHIFT
            if upper_bound > 360.0:
                upper_bound = upper_bound % 360.0
            class_cur = (class_cur[0] + cls.SHIFT, upper_bound)

        if class_cur[1] < cls.CLASS_SIZE:
            cnt = np.count_nonzero((value >= class_cur[0]) & (value <= 360.0))
            cnt += np.count_nonzero((value >= 0.0) & (value <= class_cur[1]))
        elif class_cur[0] == 0.0:
            cnt = np.count_nonzero((value == 360.0))
            cnt += np.count_nonzero((value >= 0.0) & (value <= class_cur[1]))
        elif class_cur[1] == 360.0:
            cnt = np.count_nonzero((value == 0.0))
            cnt += np.count_nonzero((value >= class_cur[0]) & (value <= 360.0))
        else:
            cnt = np.count_nonzero((value >= class_cur[0]) & (value <= class_cur[1]))

        return class_cur, cnt

    @classmethod
    def _get_term_period(cls, term_dataset: xr.Dataset) -> Optional[Pcd]:
        # Compute the Pcd of the input term data.

        # Get direction classes
        value: np.ndarray = term_dataset.direction.values
        counters_list = []

        class_cur: tuple[float, float] = 0, cls.CLASS_SIZE

        for class_nbr in range(cls.CLASSES_NBR):
            class_cur, cnt = cls._get_term_period_loop(class_nbr, class_cur, value)
            if (
                cnt * 100.0 / term_dataset.attrs["points_nbr"]
            ) >= cls.CLASS_PERCENT_MIN:
                counters_list.append((class_cur[0], cnt))

        if not counters_list:
            return None

        # Sort counters_list
        cnt_max: int = max(cnt for _, cnt in counters_list)
        c_max_list: list[tuple] = list(filter(lambda c: c[1] == cnt_max, counters_list))

        # Build the list of the direction of all c_max
        directions: list[WindDirection] = [
            cls.WIND_DIRECTION_CLASS(c_max[0], cls.CLASS_SIZE) for c_max in c_max_list
        ]

        # Get the representative directions
        direction: Optional[WindDirection] = reduce(
            lambda x, y: x + y if x is not None else None, directions
        )

        if direction is not None:
            return Pcd(
                begin_time=Datetime(term_dataset.previous_time.values),
                end_time=Datetime(term_dataset.valid_time.values),
                wd=direction,
            )

        return None

    def _find_periods(self) -> None:
        """Find all PCD."""
        # Initialize the index
        period_prev: Optional[Pcd] = None

        for period_cur in self._term_periods:
            if period_prev is None:
                period_prev = period_cur
            elif period_cur is None:
                self._pcd.append(period_prev)
                period_prev = None
            else:
                period_updated: bool = period_prev.update(period_cur)

                # If the update failed, then keep period_prev
                if period_updated is False:
                    self._pcd.append(period_prev)
                    period_prev = period_cur

        if period_prev is not None:
            self._pcd.append(period_prev)

        # Normalize all PCD
        self._pcd = [pcd.normalize_wd() for pcd in self._pcd]

    def _check_pcd_coverage(
        self, percent: Optional[float] = KEEP_PCD_PERCENT_MIN
    ) -> bool:
        # Compute the percent of the PCD coverage over the monitoring period duration
        pcd_cov: Timedelta = self._pcd[-1].end_time - self._pcd[0].begin_time
        pcd_coverage_percent: float = pcd_cov * 100 / self.monitoring_period.duration
        return pcd_coverage_percent >= percent

    def _check_pcd_duration(self, p: Pcd) -> bool:
        return p.duration >= self.PERIOD_DURATION_MIN

    def _post_process_found_periods(self) -> None:
        """Post process found periods."""
        pcd_len: int = len(self._pcd)

        if pcd_len == 0:
            self._reset_pcd()

        elif pcd_len == 1:
            # If the PCD is < 3h or the PCD does not covered enough the monitoring
            # period, then keep not it
            if (
                not self._pcd_filtered and not self._check_pcd_duration(self._pcd[0])
            ) or not self._check_pcd_coverage():
                self._reset_pcd()

        else:
            # Keep only periods with at least a 3 hours duration
            if self._pcd_filtered is False:
                self._pcd = list(filter(self._check_pcd_duration, self._pcd))
                self._pcd = [
                    self._pcd[i] for i in range(0, -min(len(self._pcd), 2), -1)
                ]
                self._pcd_filtered = True
                self._post_process_found_periods()
                return

            # Here, we know that self._pcd has exactly 2 elements
            if self._check_pcd_coverage() is False:
                self._reset_pcd()

            # If the 1st and the last direction are the same, then merge those
            elif self._pcd[0].wd == self._pcd[-1].wd:
                self._pcd = [self._pcd[0] + self._pcd[-1]]
                self._post_process_found_periods()

            # If they are opposite, then don't keep these too
            elif self._pcd[0].wd.is_opposite_to(self._pcd[-1].wd):
                self._reset_pcd()

    def run(self) -> list[Pcd]:
        self._reset_pcd()
        self._pcd_filtered = False

        if self._term_periods:
            self._find_periods()
            self._post_process_found_periods()

        return self._pcd
