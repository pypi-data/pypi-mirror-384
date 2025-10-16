from __future__ import annotations

from mfire.settings import get_logger
from mfire.text.synthesis.wind_reducers.wind.case3.wind_direction import Pcd

from .block_summary_builder import BlockSummaryBuilder
from .wind_block import WindBlock

LOGGER = get_logger(name=__name__, bind="two_blocks_summary_builder")


class TwoBlocksSummaryBuilder(BlockSummaryBuilder):
    """TwoBlocksSummaryBuilder class."""

    pcd_g0: list[Pcd]
    pcd_g1: list[Pcd]

    def __init__(self, blocks: list[WindBlock], **kwargs):
        super().__init__(
            blocks, pcd_g0=blocks[0].pcd.copy(), pcd_g1=blocks[1].pcd.copy(), **kwargs
        )

    @property
    def pcd_g0_cnt(self) -> int:
        return self._counters["pcd_g0"]

    @property
    def pcd_g1_cnt(self) -> int:
        return self._counters["pcd_g1"]

    @staticmethod
    def _check_periods(p0: Pcd, p1: Pcd) -> bool:
        return p0.wd != p1.wd and p0.wd.is_opposite_to(p1.wd) is False

    def _update_pcd_counters(self) -> None:
        self._counters.update(
            {
                "pcd": len(self._pcd),
                "pcd_g0": len(self.pcd_g0),
                "pcd_g1": len(self.pcd_g1),
            }
        )

    def _remove_pcd(self) -> None:
        self._pcd = []
        self.pcd_g0, self.pcd_g1 = [], []
        self._update_pcd_counters()

    def _reduce_pcd_groups(self):
        self._pcd = [self.pcd_g0[0] + self.pcd_g1[0]]
        self._update_pcd_counters()

    def _initialize_pcd(self) -> None:
        self._update_pcd_counters()

        if self.pcd_g0_cnt >= 1 and self.pcd_g1_cnt >= 1:
            if self.pcd_g0[-1].wd == self.pcd_g1[0].wd:
                if self.pcd_g0_cnt == self.pcd_g1_cnt == 1:
                    self._reduce_pcd_groups()
                    return
                self.pcd_g0[-1].update(self.pcd_g1[0])
                self.pcd_g1.pop(0)

        self._pcd = self.pcd_g0 + self.pcd_g1
        self._update_pcd_counters()

    @property
    def has_to_clean_pcd(self) -> bool:
        return self.pcd_cnt >= 4 or (
            self.pci_cnt == 1
            and self.pcd_cnt == 3
            and self._pcd[self.pcd_g0_cnt - 1].wd.is_opposite_to(
                self._pcd[self.pcd_g0_cnt].wd
            )
        )

    def _process_pcd(self) -> None:
        # Update counters just in case
        self._update_pcd_counters()

        # Clean pcd if there are 4 periods with common direction (meaning 2 periods for
        # each group)
        # Remove some pcd of WindBlocks if necessary when there is 1 pci and are 3 pcd
        if self.has_to_clean_pcd:
            self._remove_pcd()

        elif self.pci_cnt >= 2 and self.pcd_cnt == 3:
            if self._pcd[0].wd.is_opposite_to(self._pcd[-1].wd):
                self._remove_pcd()
            elif self._pcd[0].wd == self._pcd[-1].wd:
                self._pcd = [self._pcd[0] + self._pcd[-1]]
                if self.pcd_g0_cnt == 1:
                    self.pcd_g1.pop(0)
                else:
                    self.pcd_g0.pop(1)

                self._update_pcd_counters()
                return

        else:
            # Update pcd
            self._pcd = self.pcd_g0 + self.pcd_g1
            self._update_pcd_counters()

        # If there is 1 pcd on each group (meaning 1 pcd for each WindBlock) and if they
        # have the same wind direction, we merge those and keep the result in pcd
        if self.pcd_g0_cnt == self.pcd_g1_cnt == 1:
            if self.pcd_g0[0].wd == self.pcd_g1[0].wd:
                self._reduce_pcd_groups()
            elif self._pcd[0].wd.is_opposite_to(self.pcd_g1[0].wd):
                self._remove_pcd()
                self._update_pcd_counters()

    def _preprocess(self, blocks: list[WindBlock]):
        # Initialize pci and pcd
        self._pci = [pci.model_copy() for pci in blocks[0].pci] + blocks[1].pci
        self._initialize_pcd()

        # Process pci and pcd
        self._process_pci()
        self._process_pcd()

        # Build the case and add it into the summary
        self._build_and_set_case(
            self._get_extra_condition(),
            "3_2B",
            ">2" if self.pci_cnt > 2 else str(self.pci_cnt),
            str(self.pcd_cnt),
            str(self.pcd_g0_cnt),
            str(self.pcd_g1_cnt),
        )
