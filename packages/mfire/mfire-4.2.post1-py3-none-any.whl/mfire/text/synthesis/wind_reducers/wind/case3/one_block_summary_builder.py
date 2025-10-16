from __future__ import annotations

from mfire.settings import get_logger

from .block_summary_builder import BlockSummaryBuilder
from .wind_block import WindBlock

LOGGER = get_logger(name=__name__, bind="one_block_summary_builder")


class OneBlockSummaryBuilder(BlockSummaryBuilder):
    """OneBlockSummaryBuilder class."""

    def _process_pcd(self) -> None:
        self._counters["pcd"] = len(self._pcd)

    def _preprocess(self, blocks: list[WindBlock]) -> None:
        # Compute pci and pcd periods and set the case.
        self._pci = blocks[0].pci.copy()
        self._pcd = blocks[0].pcd.copy()

        self._process_pci()
        self._process_pcd()

        # Build the case and add it into the summary
        self._build_and_set_case(
            self._get_extra_condition(),
            "3_1B",
            ">2" if self.pci_cnt > 2 else str(self.pci_cnt),
            str(self.pcd_cnt),
        )
