from __future__ import annotations

from collections import OrderedDict
from functools import cached_property
from typing import ClassVar, Optional

import numpy as np

import mfire.utils.mfxarray as xr
from mfire.composite.base import BaseComposite
from mfire.settings import get_logger
from mfire.text.synthesis.wind_reducers.wind.helpers import BaseWindPeriod
from mfire.utils.date import Datetime

# Logging
LOGGER = get_logger(name=__name__, bind="wind_intensity")


class WindIntensity(BaseComposite):
    """WindIntensity class."""

    PERCENTILE_NUM: ClassVar[int] = 95

    def __init__(self, wind_force: float, **data) -> None:
        super().__init__(**data)
        self._interval: tuple[int, int] = (0, 0)
        self._interval_from_wind_force(wind_force)
        self._context: str = "normal"

    @property
    def interval_to_text(self) -> dict[str, dict[tuple, str]]:
        # We shall declare this attribute as a class attribute, but we don't in order to
        # have the translation in the unit tests of tests/text/test_manager.py
        return {
            "normal": OrderedDict(
                {
                    (25, 35): self._("assez fort"),
                    (35, 50): self._("fort"),
                    (50, 70): self._("très fort"),
                    (70, None): self._("tempétueux"),
                }
            ),
            "attenuate_with_prefix": OrderedDict(
                {
                    (25, 35): self._("modéré à assez fort"),
                    (35, 50): self._("assez fort à fort"),
                }
            ),
            "attenuate_by_replacement": OrderedDict(
                {(25, 35): self._("modéré"), (35, 50): self._("assez fort")}
            ),
        }

    @property
    def interval(self) -> tuple[int, int]:
        return self._interval

    def as_text(self, describer: str = "normal") -> str:
        return self.interval_to_text[describer][self._interval]

    @cached_property
    def speed_min(self) -> float:
        wi_interval: list = list(self.interval_to_text["normal"].keys())
        wi_interval.sort()
        return float(wi_interval[0][0])

    @classmethod
    def data_array_to_value(cls, data_array: xr.DataArray) -> float:
        # Find the value which represents the input DataArray.
        return round(np.nanpercentile(data_array.values, cls.PERCENTILE_NUM), 2)

    def has_attenuable_interval(self) -> bool:
        for context in ["attenuate_with_prefix", "attenuate_by_replacement"]:
            if self.interval in self.interval_to_text[context].keys():
                return True
        return False

    def is_juxtaposed_with(self, other: WindIntensity) -> bool:
        # Check if 2 WindIntensity have juxtaposed intervals.
        normal_interval: list[tuple] = list(self.interval_to_text["normal"].keys())
        for i, interval in enumerate(normal_interval):
            if self.interval == interval:
                if i - 1 >= 0 and normal_interval[i - 1] == other.interval:
                    return True
                if (
                    i + 1 < len(normal_interval)
                    and normal_interval[i + 1] == other.interval
                ):
                    return True
        return False

    def _interval_from_wind_force(self, wind_force: float) -> None:
        for bound_inf, bound_sup in self.interval_to_text["normal"]:
            if (bound_inf <= wind_force) and (
                bound_sup is None or wind_force < bound_sup
            ):
                self._interval = bound_inf, bound_sup
                return

        raise ValueError(f"Wind intensity not found for wind force {wind_force} !")

    def __eq__(self, other: WindIntensity) -> bool:
        return isinstance(other, WindIntensity) and self.interval == other.interval

    def __le__(self, other: WindIntensity) -> bool:
        return self.interval[0] <= other.interval[0]

    def __lt__(self, other: WindIntensity) -> bool:
        return self.interval[0] < other.interval[0]

    def __ge__(self, other: WindIntensity) -> bool:
        return self.interval[0] >= other.interval[0]

    def __gt__(self, other: WindIntensity) -> bool:
        return self.interval[0] > other.interval[0]

    def __hash__(self) -> int:
        return hash(self.interval)

    def __repr__(self):
        return f"WindIntensity(interval={self._interval})"


class Pci(BaseWindPeriod):
    """Period with common Intensity (Pci) class."""

    wi: WindIntensity

    def __eq__(self, other: Pci) -> bool:
        return super().__eq__(other) and self.wi == other.wi

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.wi))

    def has_same_intensity_than(self, other: Pci) -> bool:
        return self.wi == other.wi

    def update(self, other: Pci) -> bool:
        # Try to update the period with another period.
        if self.has_same_intensity_than(other) and self.end_time <= other.begin_time:
            self.end_time = other.end_time
            return True

        return False

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(begin_time={self.begin_time}, "
            f"end_time={self.end_time}), wi={self.wi}"
        )

    def summarize(
        self, reference_datetime: Datetime, wi_describer: str = "normal"
    ) -> dict:
        summary: dict = super().summarize(reference_datetime)
        summary[self.WI_K] = self.wi.as_text(wi_describer)

        return summary


class PciFinder(BaseComposite):
    initial_periods: list[Pci]

    @classmethod
    def from_dataset(cls, dataset: xr.Dataset, parent: BaseComposite) -> PciFinder:
        # Initialize a period finder from its term-periods.

        term_periods: list[Pci] = []

        for valid_time in dataset.valid_time:
            term_dataset: xr.Dataset = dataset.sel(valid_time=valid_time)

            term_periods.append(
                Pci(
                    begin_time=Datetime(term_dataset.previous_time.values),
                    end_time=Datetime(term_dataset.valid_time.values),
                    wi=WindIntensity(term_dataset.wind_q95.values, parent=parent),
                )
            )

        return cls(initial_periods=term_periods)

    def run(self) -> list[Pci]:
        # Find all periods as a list.
        periods: list[Pci] = []
        cnt: int = len(self.initial_periods)
        period: Optional[Pci]
        period = self.initial_periods[0] if cnt else None

        for i in range(1, cnt):
            period_cur: Pci = self.initial_periods[i]
            res: bool = period.update(period_cur)

            # If res is True, period has been updated with period_cur times
            if res is False:
                periods.append(period)
                period = period_cur

        if period is not None:
            periods.append(period)

        return periods
