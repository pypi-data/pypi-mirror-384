from __future__ import annotations

from functools import cached_property
from typing import List, Optional

import numpy as np

from mfire.composite.base import BaseModel
from mfire.settings import SPACE_DIM
from mfire.utils import mfxarray as xr
from mfire.utils.calc import round_to_closest_multiple
from mfire.utils.period import Period, PeriodDescriber


class Lpn(BaseModel):
    da: xr.DataArray
    period_describer: PeriodDescriber

    @staticmethod
    def _compute_local_extremums(lpn_da: xr.DataArray) -> xr.DataArray:
        # Calculation of local extremums
        diffs = np.sign(lpn_da[1:].to_numpy() - lpn_da[:-1].to_numpy())
        extremums, idx_prev_extremum = [], -1
        for idx, diff in enumerate(diffs):
            if diff != 0:
                if idx_prev_extremum != -1 and diffs[idx_prev_extremum] == diff:
                    extremums[idx_prev_extremum] = False
                idx_prev_extremum = idx
                extremums.append(True)
            else:
                extremums.append(False)
        return lpn_da[[True] + extremums]

    @staticmethod
    def _drop_idx(lpn_da: xr.DataArray, idx: int) -> xr.DataArray:
        if idx == 0:
            lpn_da[0] = (lpn_da[0] + lpn_da[1]) / 2
            return lpn_da.drop_isel(valid_time=1)
        if idx == lpn_da.size - 2:
            lpn_da[-1] = (lpn_da[-1] + lpn_da[-2]) / 2
            return lpn_da.drop_isel(valid_time=-2)
        return lpn_da.drop_isel(valid_time=[idx, idx + 1])

    @staticmethod
    def _compute_variations(lpn_da: xr.DataArray) -> xr.DataArray:
        # Keep 3 variations maximally >= 200
        while (diffs := np.diff(lpn_da)).size > 0 and (
            diffs.size > 3 or min(abs(diffs)) < 200
        ):
            lpn_da = Lpn._drop_idx(lpn_da, np.argmin(abs(diffs)))
        return lpn_da

    def _compute_hours(self, lpn_da: xr.DataArray) -> xr.DataArray:
        # Keep 3 hours at least
        while (diffs := np.diff(lpn_da.valid_time)).size > 0 and (
            min(diffs).astype("timedelta64[h]") < 3
        ):
            lpn_da = Lpn._drop_idx(lpn_da, np.argmin(abs(diffs)))
        return lpn_da

    @cached_property
    def extremums_da(self) -> Optional[xr.DataArray]:
        """
        Returns the extremums DataArray of LPN values

        Returns:
            Optional[xr.DataArray]: DataArray containing only the extremums or None if
                no extremums were found
        """
        # Calculation of minimum values
        lpn_da = self.da.min(dim=SPACE_DIM)
        lpn_da = lpn_da.where(~np.isnan(lpn_da), drop=True)
        if lpn_da.size == 0:
            return None

        lpn_da = self._compute_local_extremums(lpn_da)
        lpn_da = self._compute_variations(lpn_da)
        lpn_da = self._compute_hours(lpn_da)
        return round_to_closest_multiple(lpn_da, 100, int)

    @property
    def extremums(self) -> List[int]:
        # Returns the list of extremum values.
        return self.extremums_da.values.tolist()

    @property
    def template_key(self) -> Optional[str]:
        """
        Returns the template key correspond to extremum values

        Returns:
            str: template key
        """
        extremums_da = self.extremums_da
        if extremums_da is None:
            return None
        if extremums_da.size == 1:
            return "1xlpn"

        return (
            f"{len(extremums_da)}xlpn+"
            if extremums_da[1] > extremums_da[0]
            else f"{len(extremums_da)}xlpn-"
        )

    @property
    def temporalities(self) -> List[str]:
        """
        Returns the description of temporalities of extremums values

        Returns:
            List[str]: List of the descriptions of extremums

        """
        return [
            self.period_describer.describe(Period(begin_time=x.valid_time))
            for x in self.extremums_da
        ]
