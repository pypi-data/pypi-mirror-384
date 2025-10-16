from __future__ import annotations

from typing import Optional

from jinja2 import Environment, Template

from mfire.settings import get_logger

LOGGER = get_logger(name="jinja_template_creator", bind="jinja_template_creator")


class JinjaTemplateCreator:
    def __init__(self):
        self._environment: Environment
        self._reset()

    def _reset(self):
        self._environment = Environment(autoescape=True)

    def _add_filters_to_jinja_environment(self, filters_list: list, force: bool = True):
        for func_name, func in filters_list:
            if func_name in self._environment.filters:
                LOGGER.warning(
                    f"A jinja template filter called '{func_name}' already exists"
                )
                if force is False:
                    continue
            self._environment.filters[func_name] = func

    def run(
        self, template_string: str, filters: Optional[list] = None, force: bool = True
    ) -> Template:
        self._reset()

        if filters:
            self._add_filters_to_jinja_environment(filters, force)

        # create jinja template
        template: Template = self._environment.from_string(template_string)

        return template
