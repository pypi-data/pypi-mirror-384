from __future__ import annotations

from abc import abstractmethod
from functools import cached_property
from typing import Annotated, Optional

import numpy as np
from pydantic import SkipValidation

from mfire.composite.base import BaseComposite
from mfire.composite.component import RiskComponentComposite
from mfire.composite.event import EventComposite
from mfire.settings import get_logger
from mfire.text.base.builder import BaseBuilder
from mfire.text.risk.reducer import RiskReducer
from mfire.text.risk.rep_value import RepValueBuilder
from mfire.utils.wwmf import Wwmf

# Logging
LOGGER = get_logger(name="text.risk.builder.mod", bind="risk.builder")


class RiskBuilder(BaseBuilder):
    """
    This class enables to manage all text for representative values. It chooses which
    class needs to be used for each case.
    """

    reducer_class: type = RiskReducer
    reducer: Optional[RiskReducer] = None
    parent: Annotated[RiskComponentComposite, SkipValidation]

    module_name: str = "risk"

    @property
    def hazard_name(self) -> str:
        return self.parent.hazard_name

    @cached_property
    def strategy(self) -> RiskBuilderStrategy:
        """
        Decides which comment generation module to use between ME, snow, monozone or
        multizone.

        Returns:
            Specific strategy according to the hazard_name (like snow or ME) or case
            (like monozone or multizone).
        """
        if self.hazard_name.startswith("ME_"):
            return RiskBuilderStrategyME(parent=self)
        if self.hazard_name == "Neige":
            return RiskBuilderStrategySnow(parent=self)
        if self.hazard_name == "Pluies":
            return RiskBuilderStrategyRain(parent=self)

        if self.is_multizone:
            return RiskBuilderStrategyMultizone(parent=self)
        return RiskBuilderStrategyMonozone(parent=self)

    @property
    def template_key(self) -> str | np.ndarray:
        return self.strategy.template_key

    @property
    def template_name(self) -> str | np.ndarray:
        return self.strategy.template_name

    @property
    def is_multizone(self) -> bool:
        return self.reducer.is_multizone

    @cached_property
    def _gusts_under_thunderstorm_event(self) -> Optional[EventComposite]:
        for lvl in self.parent.levels_of_risk(1):
            for event in lvl.events:
                if "WWMF__SOL" not in event.field.name:
                    continue

                thresholds = []
                if event.plain is not None:
                    thresholds += event.plain.threshold
                if event.mountain is not None:
                    thresholds += event.mountain.threshold
                if all(Wwmf.is_thunderstorm(ts) for ts in thresholds):
                    return event
        return None

    @property
    def is_gusts_under_thunderstorm(self) -> bool:
        return (
            self.hazard_name in ["Rafales", "Vent"]
            and self._gusts_under_thunderstorm_event is not None
        )

    def post_process_gusts_under_thunderstorm(self):
        if self.reducer.final_risk_max_level == 0:
            return

        event = self._gusts_under_thunderstorm_event
        if event.values_ds["occurrence_event"].any():
            self.text += "\n" + self._("Rafales plus fortes sous orage.")

    def post_process(self):
        """Make a post-process operation on the text."""
        self.strategy.post_process()
        if self.is_gusts_under_thunderstorm:
            self.post_process_gusts_under_thunderstorm()

        super().post_process()


class RiskBuilderStrategy(BaseComposite):

    parent: RiskBuilder

    @property
    def reducer(self) -> RiskReducer:
        return self.parent.reducer

    @property
    def reduction(self) -> Optional[dict]:
        return self.parent.reduction

    @property
    def text(self):
        return self.parent.text

    @text.setter
    def text(self, value: str):
        self.parent.text = value

    @property
    @abstractmethod
    def template_name(self) -> str:
        pass

    @property
    @abstractmethod
    def template_key(self) -> str | np.ndarray:
        pass

    def post_process(self):
        """Post-process method called by parent"""


class RiskBuilderStrategyMonozone(RiskBuilderStrategy):
    @property
    def template_name(self) -> str:
        return "monozone"

    @property
    def template_key(self) -> str | np.ndarray:
        return self.reducer.strategy.norm_risk

    def post_process(self):
        """Processes the representative values for the monozone comment."""
        rep_value_table = {}
        for bloc, data in self.reduction.items():
            if isinstance(data, dict):
                data_dict = {
                    k: v
                    for k, v in data.items()
                    if k not in ["start", "stop", "centroid", "period"]
                }
                if data_dict:
                    rep_value_table[f"{bloc}_val"] = data_dict

        final_rep_value = {
            key: RepValueBuilder.compute_all(
                self.parent, {k: v for k, v in value.items() if k != "level"}
            )
            for key, value in rep_value_table.items()
            if value
        }
        self.text = self.text.format(**final_rep_value)


class RiskBuilderStrategyMultizone(RiskBuilderStrategy):

    @property
    def template_name(self) -> str:
        return "multizone"

    @property
    def template_key(self) -> str | np.ndarray:
        return self.reducer.localisation.unique_name

    def post_process(self):
        """Processes the representative values for the multizone comment."""
        self.text += " " + RepValueBuilder.compute_all(
            self.parent, self.reducer.get_critical_values()
        )
        super().post_process()


class RiskBuilderStrategyME(RiskBuilderStrategy):
    @property
    def template_name(self) -> str:
        return "ME"

    @property
    def template_key(self) -> str | np.ndarray:
        parts = []
        if "temporality" in self.reduction and not self.parent.hazard_name.endswith(
            "_bis"
        ):
            parts.append("temp")
        if "value" in self.reduction:
            parts.append("val")
        if "localisation" in self.reduction:
            parts.append("loc")
        return "+".join(parts) if parts else "RAS"


class RiskBuilderStrategyRain(RiskBuilderStrategyMultizone):
    @property
    def template_name(self) -> str:
        return "rain"

    @property
    def template_key(self) -> str | np.ndarray:
        return self.reduction["key"]


class RiskBuilderStrategySnow(RiskBuilderStrategyMultizone):

    @property
    def template_name(self) -> str:
        return "snow"

    @property
    def template_key(self) -> str | np.ndarray:
        return self.reduction["key"]

    def post_process(self):
        """Processes the representative values for the snow comment."""
        super().post_process()

        # Append the LPN (if present) at the 2nd line (#41905)
        if "LPN__SOL" in self.reducer.get_critical_values():
            text = self.text.split("\n")
            self.text = "\n".join([text[0], text[-1]] + text[1:-1])

        self.parent.clean_text()
