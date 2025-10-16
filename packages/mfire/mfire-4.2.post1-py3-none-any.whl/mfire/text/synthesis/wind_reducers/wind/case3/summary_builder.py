from __future__ import annotations

from datetime import timedelta
from typing import Optional

import mfire.utils.mfxarray as xr
from mfire.settings import get_logger
from mfire.text.synthesis.wind_reducers.exceptions import (
    WindSynthesisError,
    WindSynthesisNotImplemented,
)
from mfire.text.synthesis.wind_reducers.mixins import BaseSummaryBuilderMixin
from mfire.utils.date import Datetime, Timedelta

from .block_summary_builder import BlockSummaryBuilder
from .blocks_builder import BlocksBuilder
from .one_block_summary_builder import OneBlockSummaryBuilder
from .two_blocks_summary_builder import TwoBlocksSummaryBuilder

LOGGER = get_logger(name=__name__, bind="case3_summary_builder")


class Case3SummaryBuilder(BaseSummaryBuilderMixin):
    """Case3SummaryBuilder class."""

    BLOCKS_MERGE_TRIES: int = 5
    TIME_SLICE_12H: timedelta = Timedelta(hours=12)
    MAX_WIND_BLOCK_NBR: int = 2

    blocks_builder: BlocksBuilder = BlocksBuilder()
    block_summary_builder: Optional[BlockSummaryBuilder] = None

    def run(self, dataset: xr.Dataset, reference_datetime: Datetime) -> dict:
        # Build WindBlocks
        self.blocks_builder.run(dataset, self.MAX_WIND_BLOCK_NBR)

        # Get and check the counter of WindBlocks
        blocks_cnt: int = len(self.blocks_builder.blocks)

        # If there is no WindBlock
        if blocks_cnt == 0:
            raise WindSynthesisError("No WindBlock found !")

        summary_builder_class: BlockSummaryBuilder.__class__

        # If there is 1 WindBlock
        if blocks_cnt == 1:
            summary_builder_class = OneBlockSummaryBuilder

        # If there is 2 WindBlocks
        elif blocks_cnt == 2:
            summary_builder_class = TwoBlocksSummaryBuilder

        # If there is more than 2 WindBlocks
        else:
            raise WindSynthesisNotImplemented("More than 2 WindBlocks have been found")

        self.block_summary_builder = summary_builder_class(
            self.blocks_builder.blocks,
            reference_datetime=reference_datetime,
            dataset=dataset,
        )
        self.summary.update(self.block_summary_builder.compute())

        return self.summary
