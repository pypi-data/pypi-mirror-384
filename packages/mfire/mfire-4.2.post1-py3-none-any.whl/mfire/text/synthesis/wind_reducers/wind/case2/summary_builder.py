from __future__ import annotations

import mfire.utils.mfxarray as xr
from mfire.settings import get_logger
from mfire.text.synthesis.wind_reducers.mixins import BaseSummaryBuilderMixin
from mfire.text.synthesis.wind_reducers.wind.helpers import SummaryKeysMixin
from mfire.text.synthesis.wind_reducers.wind.wind_enum import WindCase, WindType

LOGGER = get_logger(name=__name__, bind="case2_summary_builder")


class Case2SummaryBuilder(BaseSummaryBuilderMixin, SummaryKeysMixin):
    def run(self, dataset: xr.Dataset) -> dict:
        self.summary = {
            self.WI_K: (
                self._("faible à modéré")
                if WindType.TYPE_1.value in dataset.wind_type.values
                else self._("modéré")
            )
        }
        self._set_summary_case(WindCase.CASE_2.value)

        return self.summary
