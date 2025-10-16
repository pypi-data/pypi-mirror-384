from __future__ import annotations

from datetime import timedelta
from typing import ClassVar, Optional

import numpy as np

import mfire.utils.mfxarray as xr
from mfire.composite.base import BaseComposite
from mfire.settings import get_logger
from mfire.text.synthesis.wind_reducers.exceptions import WindSynthesisError
from mfire.text.synthesis.wind_reducers.wind.utils import filter_dataset_from_wind_type
from mfire.text.synthesis.wind_reducers.wind.wind_enum import WindType
from mfire.text.synthesis.wind_reducers.wind.wind_intensity import (
    PciFinder,
    WindIntensity,
)
from mfire.utils.date import Datetime, Timedelta

from .wind_block import WindBlock
from .wind_direction import PcdFinder

LOGGER = get_logger(name=__name__, bind="block_builder")


class BlocksBuilder(BaseComposite):
    """BlocksBuilder class."""

    BLOCKS_MERGE_TRIES: ClassVar[int] = 1
    TIME_SLICE_12H: ClassVar[Timedelta] = Timedelta(hours=12)

    def __init__(self, **data):
        super().__init__(**data)

        self._blocks: list[WindBlock] = []
        self._ind: int = 0
        self._ind_max: int = 0

        self._blocks_nbr_max: int = 0
        self._period_between_t3_blocks_bound: Timedelta = Timedelta(hours=0)
        self._t3_block_duration_min: Timedelta = Timedelta(hours=0)

    @property
    def blocks(self) -> list[WindBlock]:
        # Get all blocks even low typed blocks.
        return self._blocks

    def _reset(self, dataset: xr.Dataset, blocks_nbr_max: Optional[int] = None):
        # Reset parameters
        self._compute_parameters(dataset, blocks_nbr_max)

        # Reset blocks
        self._blocks: list[WindBlock] = self._initialize_wind_blocks(dataset)
        self._ind_max = len(self._blocks) - 1

    def _reset_ind(self, start: int = 0):
        self._ind = start

    @staticmethod
    def _get_monitoring_period_duration(dataset: xr.Dataset) -> Timedelta:
        time_start: Datetime = Datetime(dataset.valid_time.values[0])
        time_stop: Datetime = Datetime(dataset.valid_time.values[-1])

        if time_start == time_stop:
            LOGGER.warning(
                f"time_start = time_stop = {time_start} => period_duration forced to"
                f"Timedelta(hours=1) !"
            )
            return Timedelta(hours=1)

        period_duration: Timedelta = Timedelta(time_stop - time_start)
        return period_duration

    def _compute_parameters(
        self, dataset: xr.Dataset, blocks_nbr_max: Optional[int] = None
    ):
        # Get duration period
        period_duration: timedelta = self._get_monitoring_period_duration(dataset)

        # Set parameters
        self._blocks_nbr_max: int = int(np.ceil(period_duration / self.TIME_SLICE_12H))
        if blocks_nbr_max is not None:
            self._blocks_nbr_max = min(self._blocks_nbr_max, blocks_nbr_max)
        self._period_between_t3_blocks_bound: Timedelta = Timedelta(period_duration / 6)
        self._t3_block_duration_min: Timedelta = self._period_between_t3_blocks_bound

    def _remove_block_from_ind(self, ind: int):
        # Remove block from index in self._blocks.
        self._blocks.pop(ind)
        self._ind_max -= 1

    @staticmethod
    def _create_block(
        term_times: list[np.datetime64], dataset: xr.Dataset
    ) -> WindBlock:
        start_time: Datetime = Datetime(
            dataset.previous_time.sel(valid_time=term_times[0]).values
        )
        end_time: Datetime = Datetime(term_times[-1])
        return WindBlock(begin_time=start_time, end_time=end_time)

    def _keep_block(self, block: WindBlock, dataset: xr.Dataset) -> bool:
        """
        Check if WindBlock can be kept or not.

        It can be kept if:
        - its duration is >= _t3_block_duration_min
        - or if it contains the term with the wind force max

        Args:
            block: Wind block to consider.
            dataset: Associated dataset to consider.

        Returns:
            True if it can be kept, False otherwise.
        """
        if block.duration >= self._t3_block_duration_min:
            return True

        # Filter dataset: keep data with previous_time >= block.begin_time and a
        # valid_time <= block.end_time
        data_previous_time: xr.DataArray = dataset.previous_time.where(
            dataset.previous_time >= block.begin_time.as_np_dt64
        ).dropna(dim="valid_time")
        dataset_block = dataset.sel(
            valid_time=slice(
                data_previous_time.valid_time[0], block.end_time.as_np_dt64
            )
        )

        # Get wind Q95 max of the block
        wfq_max: float = float(dataset_block.wind_q95.max())
        if wfq_max == dataset.attrs["wind_q95_max"]:
            return True

        return False

    def _initialize_wind_blocks(self, dataset: xr.Dataset) -> list[WindBlock]:
        blocks = []

        # Check if there are at least 1 type 3 term
        if WindType.TYPE_3.value not in dataset.wind_type.values:
            raise WindSynthesisError("No wind type 3 terms found !")

        valid_times: list[np.datetime64] = []

        wind_type_prev: WindType = WindType(
            dataset.wind_type.sel(valid_time=dataset.valid_time[0])
        )

        # Get wind blocks
        for valid_time in dataset.valid_time.values:
            wind_type_cur: WindType = WindType(
                dataset.wind_type.sel(valid_time=valid_time)
            )

            if wind_type_cur != wind_type_prev:
                if wind_type_prev == WindType.TYPE_3 and valid_times:
                    blocks.append(self._create_block(valid_times, dataset))

                wind_type_prev = wind_type_cur
                valid_times = []

            valid_times.append(valid_time)

            # If last terms not in a block, then we create one
            if (
                valid_time == dataset.valid_time.values[-1]
                and wind_type_prev == WindType.TYPE_3
            ):
                blocks.append(self._create_block(valid_times, dataset))

        return blocks

    @staticmethod
    def _compute_data_wf_terms_q95(dataset: xr.Dataset) -> None:
        """
        Compute the Q95 of each type 3 terms as well as their maximum value, stored in a
        new variable called `wind_q95`.

        Args:
            dataset: Dataset to consider.
        """
        wind_q95: list[float] = []

        for valid_time in dataset.valid_time:
            dataset_cur: xr.Dataset = dataset.sel(valid_time=valid_time)

            if WindType(dataset_cur.wind_type.values) != WindType.TYPE_3:
                wind_q95.append(np.nan)
            else:
                wind_q95.append(WindIntensity.data_array_to_value(dataset_cur.wind))

        # Add the `wind_q95` variable
        dataset["wind_q95"] = xr.DataArray(
            data=wind_q95, coords=[dataset.valid_time], dims=["valid_time"]
        )

        # Keep the max of wind_q95 as an attribute
        dataset.attrs["wind_q95_max"] = (
            np.nan if np.isnan(wind_q95).all() else np.nanmax(np.array(wind_q95))
        )

    def _try_to_merge_current_block_with_previous(self) -> bool:
        """
        Try to merge the current WindBlock with the previous one.

        The merge is performed if the duration between those WindBlocks
        is <= _period_between_t3_blocks_bound.

        Returns:
            True if mergeable, False otherwise.
        """
        if self._ind - 1 < 0:
            return False

        time_between: Timedelta = (
            self._blocks[self._ind].begin_time - self._blocks[self._ind - 1].end_time
        )
        if time_between > self._period_between_t3_blocks_bound:
            return False

        self._blocks[self._ind] = self._blocks[self._ind].merge(
            self._blocks[self._ind - 1]
        )

        self._remove_block_from_ind(self._ind - 1)
        self._ind -= 1

        return True

    def _try_to_merge_current_block_with_next(self) -> bool:
        """
        Try to merge the current WindBlock with the next one.

        The merge is performed if the duration between those WindBlocks
        is <= _period_between_t3_blocks_bound.

        Returns:
            True if mergeable, False otherwise.
        """
        if self._ind + 1 > self._ind_max:
            return False

        time_between: Timedelta = (
            self._blocks[self._ind + 1].begin_time - self._blocks[self._ind].end_time
        )
        if time_between >= self._period_between_t3_blocks_bound:
            return False

        self._blocks[self._ind] = self._blocks[self._ind].merge(
            self._blocks[self._ind + 1]
        )

        self._remove_block_from_ind(self._ind + 1)

        return True

    def _try_to_merge_blocs(self):
        # try to merge the current WindBlock with the previous one
        while True:
            if not self._try_to_merge_current_block_with_previous():
                break

        # try to merge the current WindBlock with the next one
        while True:
            if not self._try_to_merge_current_block_with_next():
                break

    def _merge_blocks(self, dataset: xr.Dataset):
        # Merge all mergeable WindBlocks.
        self._reset_ind()

        while self._ind <= self._ind_max:
            # Get next kept WindBlock
            while (
                self._ind <= self._ind_max
                and self._keep_block(self._blocks[self._ind], dataset) is False
            ):
                self._ind += 1

            # If ind max reached, stop the process
            if self._ind > self._ind_max:
                break

            self._try_to_merge_blocs()
            self._ind += 1

        # Post-processing
        self._blocks_merging_post_process(dataset)

    def _reduce_blocks_number(self) -> bool:
        # Reduce blocks list by merging the 2 closest blocks.
        blocks_nbr: int = len(self.blocks)
        space_min: Optional[Timedelta] = None
        ind: Optional[tuple[int, int]] = None

        for i in range(blocks_nbr - 1):
            j: int = i + 1

            space = self.blocks[j].begin_time - self.blocks[i].end_time
            if space_min is None or space < space_min:
                space_min = space
                ind = i, j

        # If a min space between 2 blocks has been found, then we merge those and keep
        # only the resulting block
        if ind is not None:
            i, j = ind
            self.blocks[j] = self.blocks[i].merge(self.blocks[j])

            for i in range(i, j):
                self._remove_block_from_ind(i)

            return True

        return False

    def _blocks_merging_post_process(self, dataset: xr.Dataset) -> None:
        # Remove short WindBlocks
        self._reset_ind()
        while self._ind <= self._ind_max:
            if self._keep_block(self.blocks[self._ind], dataset) is False:
                self._remove_block_from_ind(self._ind)
            self._ind += 1

        blocks_cnt: int = len(self.blocks)

        if blocks_cnt == 0:
            raise WindSynthesisError("No WindBlocks have been found")

        if blocks_cnt <= self._blocks_nbr_max:
            return

        # Reduce the number of WindBlocks if they are so much
        LOGGER.warning("A reduction of the WindBlocks list is needed")

        while blocks_cnt > self._blocks_nbr_max:
            reduce_res: bool = self._reduce_blocks_number()

            if reduce_res is False:
                raise WindSynthesisError(
                    f"Failed to reduce the number of WindBlocks "
                    f"to {self._blocks_nbr_max}"
                )

            blocks_cnt: int = len(self.blocks)

    def _compute_periods(self, dataset: xr.Dataset) -> None:
        """
        Computes wind PCD and PCI periods of blocks.

        Args:
            dataset: Dataset to consider.
        """
        speed_min: float = WindIntensity(70, parent=self).speed_min

        for i, block in enumerate(self._blocks):
            # Filter dataset: keep only terms with previous_time >=
            # block_cur.begin_time and a valid_time <= block_cur.end_time
            data_previous_time: xr.DataArray = dataset.previous_time.where(
                dataset.previous_time >= block.begin_time.as_np_dt64
            ).dropna(dim="valid_time")

            dataset_block: xr.Dataset = dataset.sel(
                valid_time=slice(
                    data_previous_time.valid_time[0], block.end_time.as_np_dt64
                )
            )

            # Filter terms: keep only type 3 terms
            dataset_block = filter_dataset_from_wind_type(
                dataset_block, WindType.TYPE_3
            )

            # If the Q95 is < 20, then replace it by 20 km/h
            dataset_block["wind_q95"] = dataset_block.wind_q95.where(
                dataset_block.wind_q95 > speed_min, speed_min
            )

            # Get wind force periods of the current block
            pci_finder = PciFinder.from_dataset(dataset_block, parent=self)
            self._blocks[i].set_pci(pci_finder.run())

            # Get wind direction periods of the current block
            pcd_finder = PcdFinder(dataset_block)
            self._blocks[i].set_pcd(pcd_finder.run())

    def run(
        self, dataset: xr.Dataset, blocks_nbr_max: Optional[int] = None
    ) -> list[WindBlock]:
        # Reset blocks attributes
        self._reset(dataset, blocks_nbr_max)

        self._compute_data_wf_terms_q95(dataset)
        self._merge_blocks(dataset)
        self._compute_periods(dataset)

        return self.blocks
