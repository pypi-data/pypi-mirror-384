from __future__ import annotations

from mfire.settings import get_logger
from mfire.text.synthesis.wind_reducers.mixins import BaseSummaryBuilderMixin
from mfire.text.synthesis.wind_reducers.wind.wind_enum import WindCase

LOGGER = get_logger(name=__name__, bind="case1_summary_builder")


class Case1SummaryBuilder(BaseSummaryBuilderMixin):
    """Case1SummaryBuilder class."""

    def run(self):
        self._set_summary_case(WindCase.CASE_1.value)
        return self.summary
