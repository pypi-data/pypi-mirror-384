from __future__ import annotations

from abc import abstractmethod
from typing import Annotated, Optional

import numpy as np
from pydantic import SkipValidation

from mfire.composite.component import SynthesisModule
from mfire.text.base.builder import BaseBuilder
from mfire.text.synthesis.reducer import SynthesisReducer


class SynthesisBuilder(BaseBuilder):
    """
    SynthesisBuilder class that must build synthesis texts
    """

    module_name: str = "synthesis"
    parent: Annotated[Optional[SynthesisModule], SkipValidation] = None

    reducer: Optional[SynthesisReducer] = None
    reducer_class: type = SynthesisReducer

    def compute(self) -> Optional[str]:
        """
        Generate the text according to the weather composite

        Returns:
            Built text.
        """
        return super().compute() if self.parent.check_condition(self.geo_id) else None

    @property
    @abstractmethod
    def template_name(self) -> str:
        """
        Get the template name.

        Returns:
            str: The template name.
        """

    @property
    @abstractmethod
    def template_key(self) -> Optional[str | np.ndarray]:
        """
        Get the template key.

        Returns:
            str | np.ndarray: The template key.
        """
