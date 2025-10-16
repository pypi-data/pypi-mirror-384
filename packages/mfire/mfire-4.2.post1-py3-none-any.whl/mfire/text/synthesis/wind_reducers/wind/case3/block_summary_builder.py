from abc import ABC, abstractmethod
from collections import defaultdict
from itertools import pairwise

import numpy as np
import xarray as xr

from mfire.text.synthesis.wind_reducers.mixins import BaseSummaryBuilderMixin
from mfire.text.synthesis.wind_reducers.wind.case3.wind_direction import Pcd
from mfire.text.synthesis.wind_reducers.wind.helpers import SummaryKeysMixin
from mfire.text.synthesis.wind_reducers.wind.wind_intensity import Pci, WindIntensity
from mfire.utils.date import Datetime

from .wind_block import WindBlock


class BlockSummaryBuilder(BaseSummaryBuilderMixin, SummaryKeysMixin, ABC):
    LOW_INTENSITY_PERCENT_MIN: float = 20.0
    reference_datetime: Datetime
    dataset: xr.Dataset

    def __init__(self, blocks: list[WindBlock], **kwargs):
        super().__init__(**kwargs)
        self._pci: list[Pci] = []  # Period with Common wind Intensity
        self._pcd: list[Pcd] = []  # Period with Common wind Direction
        self._counters: defaultdict = defaultdict(int)

        self._preprocess(blocks)

    @property
    def pci(self) -> list[Pci]:
        return self._pci

    @property
    def pcd(self) -> list[Pcd]:
        return self._pcd

    @property
    def counters(self) -> defaultdict:
        return self._counters

    @property
    def init_pci_cnt(self) -> int:
        return self._counters["init_pci"]

    @property
    def pci_cnt(self) -> int:
        return self._counters["pci"]

    @property
    def pcd_cnt(self) -> int:
        return self._counters["pcd"]

    @property
    def extra_condition(self) -> str:
        return "simultaneous_change"

    def _get_extra_condition(self) -> str:
        if (
            self.pci_cnt == 2
            and self.pcd_cnt == 2
            and self._pci[1].begin_time == self._pcd[1].begin_time
        ):
            return self.extra_condition
        return ""

    @classmethod
    def pci_sorted_key(cls, period: Pci):
        return period.wi.interval[0], period.begin_time

    def _process_pci(self) -> None:
        # Set PCI counters
        self._counters["pci"] = self._counters["init_pci"] = len(self._pci)

        if self.pci_cnt > 2:
            interval_upper_bounds: list[int] = [pci.wi.interval[0] for pci in self._pci]

            # If self.pci is not sorted along wind_intensity, then do it
            if not all(x < y for x, y in pairwise(interval_upper_bounds)) and not all(
                x > y for x, y in pairwise(interval_upper_bounds)
            ):
                self._pci.sort(key=self.pci_sorted_key)
            # Else, it's like if there are only 2 periods
            else:
                # Keep only the 1st and the last period
                self._pci = [self._pci[i] for i in (0, -1)]
                self._counters["pci"] = 2

        if self.pci_cnt == 2 and self._pci[0].has_same_intensity_than(self._pci[1]):
            self._pci[0].update(self._pci[1])
            self._pci = [self._pci[0]]
            self._counters["pci"] = 1

    @abstractmethod
    def _process_pcd(self) -> None:
        pass

    @abstractmethod
    def _preprocess(self, blocks: list[WindBlock]) -> None:
        """
        Compute pci and pcd periods and set the case.

        Args:
            blocks: Blocks to consider.
        """

    def _build_and_set_case(self, extra_condition: str, *elts) -> None:
        if extra_condition != "":
            elts += (extra_condition,)
        case: str = "_".join(elts)
        self._set_summary_case(case)

    def _check_wi_cover_percent(self, wi: WindIntensity, dataset: xr.Dataset) -> bool:
        # Check if there are more than 20% of terms with the wi wind intensity.

        # Compute the percent of terms contained in the WIndIntensity's interval
        q95: xr.DataArray = dataset.wind_q95
        cnt = q95.where((wi.interval[0] <= q95) & (q95 < wi.interval[1])).count(
            dim="valid_time"
        )
        percent: float = float((cnt * 100 / q95.valid_time.count()).values)
        return percent >= self.LOW_INTENSITY_PERCENT_MIN

    def _attenuate_wind_intensity(
        self, wi_min: WindIntensity, wi_max: WindIntensity, dataset: xr.Dataset
    ) -> bool:
        if wi_min > wi_max:
            raise ValueError(f"wi_min '{wi_min}' has to be < wi_max '{wi_max}' !")
        return (
            wi_min.has_attenuable_interval()
            and wi_max.has_attenuable_interval()
            and wi_min.is_juxtaposed_with(wi_max)
            and self._check_wi_cover_percent(wi_min, dataset) is False
        )

    def _wind_intensities_describer(self, dataset: xr.Dataset) -> list[str]:
        res: list[str] = self.pci_cnt * ["normal"]

        # If there is 1 PCI, and if its wind intensity is attenuable, then
        # we just attenuate this by adding a prefix
        if self.pci_cnt == 1:
            if self._pci[
                0
            ].wi.has_attenuable_interval() is True and not self._check_wi_cover_percent(
                self._pci[0].wi, dataset
            ):
                return ["attenuate_with_prefix"]
            return res

        # Here, we are sure that remains exactly 2 PCI
        # Then, we get the index of the PCI with the min wind intensity
        wi_min_index: np.int64 = np.argmin(
            [wi.interval[0] for wi in [self._pci[0].wi, self._pci[1].wi]]
        )
        wi_min: WindIntensity = self._pci[wi_min_index].wi

        # If there are 2 PCI from the initialization, if the lowest wind intensity is
        # attenuable and if the 2 intensities are juxtaposed, then we attenuate the
        # lowest one by replacement
        if self.init_pci_cnt == 2:
            # Get the index of the PCI with the max wind intensity
            wi_max: WindIntensity = self._pci[1 if wi_min_index == 0 else 0].wi

            if self._attenuate_wind_intensity(wi_min, wi_max, dataset):
                res[wi_min_index] = "attenuate_with_prefix"

        # If there was initially more than 3 PCI, if the lowest wind intensity is
        # attenuable and if it is juxtaposed with the greatest, then we attenuate the
        # lowest one  by replacing it with the previous one in the wind intensity order
        else:
            # Get the indexes of the PCI with the max wind intensity
            wi_max: WindIntensity = self._pci[
                self.pci_cnt - 1 if wi_min_index == 0 else 0
            ].wi

            if self._attenuate_wind_intensity(wi_min, wi_max, dataset):
                res[wi_min_index] = "attenuate_by_replacement"

        return res

    def compute(self) -> dict:
        wi_describers: list[str] = self._wind_intensities_describer(self.dataset)

        # Update the summary with the pci and pcd summarizes
        self.summary.update(
            {
                # If more than 2 PCI, get only the summary of the 1st and the last PCI
                # Else,
                self.PCI_K: [
                    self._pci[i].summarize(self.reference_datetime, wi_describers[i])
                    for i in range(0, -min(self.pci_cnt, 2), -1)
                ],
                # Get summary of all PCD
                self.PCD_K: [p.summarize(self.reference_datetime) for p in self._pcd],
            }
        )

        return self.summary
