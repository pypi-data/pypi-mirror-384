from __future__ import annotations

import gettext
import os
from copy import deepcopy
from functools import cached_property
from typing import Annotated, Any, Iterable, List, Optional, Set, Tuple

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field, SkipValidation, model_validator

from mfire.settings import get_logger
from mfire.settings.constants import LOCALE_DIR

# Logging
LOGGER = get_logger(name="composite.base.mod", bind="composite.base")


class precached_property(cached_property, property):
    pass


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True, ignored_types=(cached_property,)
    )

    @property
    def attrs(self):
        for cls in self.__class__.mro():
            for name, attr in cls.__dict__.items():
                yield name, attr

    def __init__(self, **data):
        super().__init__(**data)

        if not os.environ.get("MFIRE_DISABLE_PRECACHING", False):
            for name, attr in self.attrs:
                if isinstance(attr, precached_property):
                    getattr(self, name)


class BaseComposite(BaseModel):
    """This abstract class implements the Composite design pattern,
    i.e. a tree-like structure of objects to be produced.

    Example: I have a hazard_id, which contains multiple levels of risks;
    each level contains elementary events; each event is defined by fields
    and masks. To produce each of the mentioned elements, we need to produce
    the child elements.

    This class gathers the attributes and methods common to Field, Geo, Element,
    Level, Component, etc.
    """

    parent: Annotated[
        Optional[BaseComposite], Field(exclude=True, repr=False), SkipValidation
    ] = None

    # Shared configuration dictionary to store global information like timezone,
    # language, ...
    _shared_config: Optional[dict] = None

    @property
    def shared_config(self) -> Optional[dict]:
        return (
            self.parent.shared_config
            if self.parent is not None
            else self._shared_config
        )

    def make_copy(self) -> BaseComposite:
        model_dumping = deepcopy(self.model_dump())
        model_dumping["_shared_config"] = self.shared_config
        return self.model_validate(model_dumping).init_parent_for_children()

    @model_validator(mode="after")
    def handle_children(self) -> BaseComposite:
        return self.init_parent_for_children()

    def init_parent_for_children(self) -> BaseComposite:
        for name in self.model_fields:
            if name == "parent":
                continue
            attr = getattr(self, name)
            if isinstance(attr, BaseComposite) and attr.parent is None:
                attr.parent = self
            # we don't use isinstance(attr, Iterable) because
            # we don't want to iterate on every letter of every string
            elif isinstance(attr, (List, Tuple, Set)):
                for obj in attr:
                    if isinstance(obj, BaseComposite) and obj.parent is None:
                        obj.parent = self
        return self

    @property
    def time_zone(self) -> str:
        return self.shared_config["time_zone"]

    @property
    def language(self) -> str:
        return self.shared_config["language"]

    def set_language(self, language: str):
        self.reset()
        self.shared_config["language"] = language
        self.shared_config.pop("translation", None)

    def _(self, text: str):
        if "translation" not in self.shared_config:
            self.shared_config["translation"] = gettext.translation(
                "mfire", localedir=LOCALE_DIR, languages=[self.language]
            )
        return self.shared_config["translation"].gettext(text)

    def compute(self) -> Any:
        """
        Generic compute method created to provide computed composite's data.
        If the self._data already exists or if the composite's data has already been
        cached, we use what has already been computed.
        Otherwise, we use the private _compute method to compute the composite's data.

        Returns:
            Computed data.
        """
        return None

    def _reset_children(self):
        # Children reset
        for name in self.model_fields:
            if name == "parent":
                continue
            attr = getattr(self, name)
            if isinstance(attr, BaseComposite):
                attr.reset()
            elif isinstance(attr, Iterable):
                for obj in attr:
                    if isinstance(obj, BaseComposite):
                        obj.reset()

    def reset(self) -> BaseComposite:
        """
        Clean the cache and reset the object. Use this when attributes are changed on
        the fly.

        Returns:
            The reinitialized object.
        """
        self._reset_children()

        # Reset cached and pre-cached properties
        for name, attr in self.attrs:
            if isinstance(attr, (cached_property, precached_property)):
                self.__dict__.pop(name, None)
        return self
