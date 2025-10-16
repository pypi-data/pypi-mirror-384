from __future__ import annotations

import csv
import re
from ast import literal_eval
from enum import Enum
from functools import cached_property
from typing import Iterable, List, Optional, Set, Tuple

import mfire.utils.mfxarray as xr
from mfire.composite.base import BaseModel
from mfire.utils.string import _, concatenate_string, decapitalize
from mfire.utils.template import TemplateRetriever


class Wwmf(BaseModel):
    language: str
    ordered_keys: bool = False
    template_name: str = "wwmf_labels"

    @cached_property
    def labels(self):
        _labels = {}

        def _cast(elt):
            try:
                return literal_eval(elt)
            except ValueError:
                return Wwmf.Subgrp[elt]

        with open(
            TemplateRetriever.path_by_name(self.template_name, self.language)
        ) as fp:
            reader = csv.reader(fp)
            for row in reader:
                _labels[tuple(_cast(elt) for elt in row[:-1] if elt != "")] = row[-1]
        return _labels

    @staticmethod
    def is_severe(wwmf: int | xr.DataArray) -> bool | xr.DataArray:
        # Checks if the given WWMF code represents a severe weather phenomenon.
        return (wwmf == 49) | (wwmf == 59) | (wwmf == 85) | (wwmf == 98) | (wwmf == 99)

    @staticmethod
    def is_visibility(wwmf: int | xr.DataArray) -> bool | xr.DataArray:
        # Checks if the given WWMF code represents visibility.
        return (30 <= wwmf) & (wwmf <= 39)

    @staticmethod
    def is_precipitation(wwmf: int | xr.DataArray) -> bool | xr.DataArray:
        # Checks if the given WWMF codes represents precipitation.
        return (40 <= wwmf) & (wwmf <= 99)

    @staticmethod
    def is_snow(wwmf: int | xr.DataArray) -> bool | xr.DataArray:
        # Checks if the given WWMF code belongs to the snow family.
        return (wwmf == 58) | (60 <= wwmf) & (wwmf <= 63) | (77 <= wwmf) & (wwmf <= 83)

    @staticmethod
    def is_rain(wwmf: int | xr.DataArray) -> bool | xr.DataArray:
        # Checks if the given WWMF code belongs to the rain family.
        return (40 <= wwmf) & (wwmf <= 59) | (70 <= wwmf) & (wwmf <= 78) | (wwmf == 93)

    @staticmethod
    def is_shower(wwmf: int | xr.DataArray) -> bool | xr.DataArray:
        # Checks if the given WWMF code belongs to the shower family.
        return (70 <= wwmf) & (wwmf <= 85) | (wwmf == 92)

    @staticmethod
    def is_thunderstorm(wwmf: int | xr.DataArray) -> bool | xr.DataArray:
        # Checks if the given WWMF code belongs to the thunderstorm family.
        return (wwmf == 84) | (wwmf == 85) | (90 <= wwmf) & (wwmf <= 99)

    @staticmethod
    def is_ice(wwmf: int | xr.DataArray) -> bool | xr.DataArray:
        # Checks if the given WWMF code belongs to the ice family.
        return (wwmf == 49) | (wwmf == 59)

    class Family(Enum):
        """Enumeration of all families and subfamilies of weather phenomena."""

        VISIBILITY = 0
        RAIN = 1
        SNOW = 2
        SHOWER = 3
        THUNDERSTORM = 4

    class Subgrp(Enum):
        """Enumeration of some grouping of labels for weather phenomena."""

        A1 = (40, 50, 51, 52, 53)
        A2 = (58, 60, 61, 62, 63)
        A3 = (70, 71, 72, 73)
        A4 = (77, 78, 80, 81, 82, 83)
        A5 = (90, 91, 92, 93, 97)
        B1 = (49, 59)
        B2 = (84,)
        B3 = (85,)
        B4 = (98,)
        B5 = (99,)

        @classmethod
        def get_b_wwmf(cls) -> List[int]:
            return sum(
                (list(b.value) for b in [cls.B1, cls.B2, cls.B3, cls.B4, cls.B5]),
                start=[],
            )

        @classmethod
        def split_groups(cls, *wwmfs: int) -> Tuple[list, list]:
            group_a, group_b = [], []
            for wwmf in wwmfs:
                if wwmf in cls.get_b_wwmf():
                    group_b.append(wwmf)
                else:
                    group_a.append(wwmf)
            return group_a, group_b

    @staticmethod
    def families(*wwmfs: int | Wwmf.Subgrp) -> Set[Wwmf.Family]:
        """Identify the families of weather phenomena represented by the given WWMF
        codes.

        Args:
            *wwmfs: Variable number of WWMF codes to check.

        Returns:
            Tuple[Wwmf.Family, ...]: Tuple of WWMF families represented by the given
            codes.
        """
        families = set()
        funcs = {
            Wwmf.is_visibility: Wwmf.Family.VISIBILITY,
            Wwmf.is_rain: Wwmf.Family.RAIN,
            Wwmf.is_snow: Wwmf.Family.SNOW,
            Wwmf.is_shower: Wwmf.Family.SHOWER,
            Wwmf.is_thunderstorm: Wwmf.Family.THUNDERSTORM,
        }
        for func, family in funcs.items():
            for wwmf in wwmfs:
                if isinstance(wwmf, Wwmf.Subgrp):
                    families |= Wwmf.families(*wwmf.value)
                elif func(wwmf):
                    families.add(family)
                    break
        return families

    @staticmethod
    def subfamilies(*wwmfs: int) -> Tuple[Wwmf.Subgrp, ...]:
        """Identify the subfamilies of weather phenomena represented by the given WWMF
        codes.

        Args:
            *wwmfs: Variable number of WWMF codes to check.

        Returns:
            Tuple[Wwmf.Subgrp, ...]: Tuple of WWMF subfamilies represented by the given
            codes.
        """
        return tuple(
            subgroup for subgroup in Wwmf.Subgrp if set(subgroup.value) & set(wwmfs)
        )

    def grouped_label(self, *wwmfs: int) -> Optional[str]:
        if not self.ordered_keys:
            wwmfs = sorted(wwmfs)

        if len(wwmfs) >= 3 and all(self.is_precipitation(ts) for ts in wwmfs):
            try:
                return self.labels[self.subfamilies(*wwmfs)]
            except KeyError:
                return None

        for key, value in self.labels.items():
            if len(key) != len(wwmfs):
                continue
            if all(
                arg in key[i] if isinstance(key[i], Iterable) else arg == key[i]
                for i, arg in enumerate(wwmfs)
            ):
                return value
        return None

    def label(self, *wwmfs: int, concatenate: bool = True) -> Optional[str]:
        """Find the label for the given WWMF codes.

        Args:
            *wwmfs: Variable number of WWMF codes to generate a label for.
            concatenate: Indicates if the final result should be concatenated
                labels if not found

        Returns:
            Optional[str]: Generated label for the given WWMF codes, or None if no match
            is found.
        """
        if len(wwmfs) == 1:
            return self.labels.get((wwmfs[0],), None)

        if grouped_label := self.grouped_label(*wwmfs):
            return grouped_label

        if not concatenate:
            return None

        result = concatenate_string(
            [self.labels[(wwmfs[0],)]]
            + [decapitalize(self.labels[(arg,)]) for arg in wwmfs[1:]],
            last_delimiter=f" {_('et', self.language)} ",
        )

        result = re.sub(r" \{loc([^}]*)}", "", result)
        result += " {loc|" + _("par endroits", self.language) + "}"
        return result
