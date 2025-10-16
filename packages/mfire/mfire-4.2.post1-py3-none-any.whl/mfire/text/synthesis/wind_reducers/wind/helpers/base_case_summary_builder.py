from abc import ABC, abstractmethod

from mfire.text.synthesis.wind_reducers.mixins import BaseSummaryBuilderMixin


class BaseCaseSummaryBuilder(BaseSummaryBuilderMixin, ABC):
    """Abstract class BaseCaseSummaryBuilder."""

    @abstractmethod
    def run(self, *args, **kwargs):
        pass
