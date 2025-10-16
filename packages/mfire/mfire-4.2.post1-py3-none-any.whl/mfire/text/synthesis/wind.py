from __future__ import annotations

from functools import cached_property
from typing import Any, List, Optional

import xarray as xr

from mfire.settings import get_logger
from mfire.text.synthesis.builder import SynthesisBuilder
from mfire.text.synthesis.reducer import SynthesisReducer
from mfire.text.synthesis.wind_reducers.base_param_summary_builder import (
    BaseParamSummaryBuilder,
)
from mfire.text.synthesis.wind_reducers.wind import WindSummaryBuilder
from mfire.utils.jinja_template import JinjaTemplateCreator
from mfire.utils.template import Template

from .wind_reducers.gust_summary_builder import GustSummaryBuilder

# Logging
LOGGER = get_logger(name=__name__, bind="wind_synthesis")


class WindReducer(SynthesisReducer):
    """Reducer class for the wind force and the gust force."""

    def compute_reduction(self) -> dict:
        self.reduction = {}

        dataset: xr.Dataset = self.weather_data

        # Get Gust and Wind summary
        for summary_builder_class in [WindSummaryBuilder, GustSummaryBuilder]:
            builder: BaseParamSummaryBuilder = summary_builder_class(
                parent=self.parent, dataset=dataset
            )
            param_summary: dict = builder.compute(
                reference_datetime=self.parent.parent.production_datetime
            )
            self.reduction.update(param_summary)

        return self.reduction

    @property
    def has_thunderstorms(self) -> bool:
        return bool(
            (self.weather_data["wwmf"].isel(valid_time=slice(1, None)) >= 98).any()
        )


class WindBuilder(SynthesisBuilder):
    """WindBuilder class."""

    reducer: Optional[WindReducer] = None
    reducer_class: type = WindReducer

    @property
    def template_name(self) -> str:
        return "wind"

    @property
    def params(self) -> tuple[str, str]:
        return "wind", "gust"

    @cached_property
    def cases(self) -> dict:
        """Get the reduction case of the parameters.

        Returns:
            Reduced information.
        """
        cases: dict[str, Optional[str]] = {}
        for param in self.params:
            try:
                cases[param] = self.reduction[param]["case"]
            except KeyError:
                cases[param] = None
                LOGGER.error(f"Case not found for '{param}' param !")
        return cases

    @cached_property
    def template_key(self) -> list[tuple[str, str]]:
        return [(param, self.cases[param]) for param in self.params]

    @cached_property
    def template(self) -> Optional[str | List[str]]:
        """
        Retrieve the template from the file system.

        Returns:
            str: The template or None if the template name is not set or the template
                was not found.
        """
        if len(self.cases) != 2:
            return None

        for param, case in self.cases.items():
            if self.template_retriever.table[param].get(case) is None:
                LOGGER.error(f"WindBuilder do not found the template for '{case}' !")
                return None

        return [self.template_retriever.get(key) for key in self.template_key]

    def _template_format(self, template: str, formating_data) -> Template:
        jinja_template = JinjaTemplateCreator().run(template)
        return Template(jinja_template.render(**formating_data))

    def _generate_text(self, template: list[str], reduction: Any):
        """
        Generate the text from a list of templates and some formating data.

        If the wind is 'faible' (case 1) and there is gust (case > 0), then
        remove the wind summary in reduction

        Args:
            template: Templates to handle.
            reduction: Reduced information.
        """
        params: tuple = self.params
        if self.cases["wind"] == "1" and self.cases["gust"] != "0":
            params = ("gust",)
            template.pop(self.params.index("wind"))
            reduction.pop("wind")
        reduction = [reduction[param] for param in params]

        # Generate the text from template and formating_data
        self.text = " ".join(
            self._template_format(text, text_reduction)
            for text, text_reduction in zip(template, reduction)
        )

    def post_process(self):
        if self.reducer.has_thunderstorms:
            if self.cases["gust"] != "0":
                self.text += " " + self._("Rafales plus fortes sous orage.")
            else:
                self.text += " " + self._("Fortes rafales sous orage.")
        super().post_process()
