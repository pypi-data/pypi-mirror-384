from __future__ import annotations

from typing import ClassVar, Optional

from mfire.composite.base import BaseComposite
from mfire.settings import get_logger

LOGGER = get_logger(name=__name__, bind="reducer_mixins")


class BaseSummaryBuilderMixin(BaseComposite):
    """SummaryBuilderMixin class."""

    TEMPLATE_KEY: ClassVar[str] = "case"
    summary: dict = {}

    @property
    def case(self) -> Optional[str]:
        # Get the case value stored in the summary.
        return self.summary.get(self.TEMPLATE_KEY)

    def _set_summary_case(self, case: str) -> None:
        # Set the wind case in the summary.
        self.summary[self.TEMPLATE_KEY] = case
