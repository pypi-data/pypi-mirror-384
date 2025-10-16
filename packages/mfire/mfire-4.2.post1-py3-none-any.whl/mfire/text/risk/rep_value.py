from __future__ import annotations

from abc import abstractmethod
from collections import defaultdict
from functools import cached_property
from typing import Annotated, Callable, ClassVar, List, Optional

import numpy as np
from pydantic import SkipValidation, field_validator

from mfire.composite.component import RiskComponentComposite
from mfire.composite.operator import ComparisonOperator
from mfire.text.base.builder import BaseBuilder
from mfire.text.base.geo import BaseGeo
from mfire.text.base.reducer import BaseReducer
from mfire.utils.calc import round_to_previous_multiple
from mfire.utils.lpn import Lpn
from mfire.utils.string import concatenate_string, get_synonym, split_var_name
from mfire.utils.wwmf import Wwmf

_start_stop_str = "{start} à {stop}"


class RepValueReducer(BaseReducer):
    feminine: bool = False
    plural: bool = False
    differentiate_plain_and_mountain: bool = False
    merge_locals: bool = True

    parent: Annotated[RiskComponentComposite, SkipValidation]

    @field_validator("infos", mode="before")
    def check_infos(cls, infos: dict) -> dict:
        """
        Validate if data has a var_name key with an accumulated variable as value.

        Args:
            infos: Information to validate.

        Returns:
            Validated information.

        Raises:
            KeyError: Raised when the var_name was not given.
        """
        var_name: Optional[str] = infos.get("var_name")
        if var_name is None:
            raise KeyError("Key 'var_name' not found.")

        return infos

    @property
    def phenomenon(self) -> str:
        return ""

    @property
    def definite_article(self) -> str:
        if self.plural:
            return self._("les")
        return self._("la") if self.feminine else self._("le")

    @property
    def indefinite_article(self) -> str:
        if self.plural:
            return self._("des")
        return self._("une") if self.feminine else self._("un")

    @property
    def definite_var_name(self) -> str:
        return f"{self.definite_article} {self.phenomenon}"

    @property
    def indefinite_var_name(self) -> str:
        return f"{self.indefinite_article} {self.phenomenon}"

    @property
    def around_word(self) -> str:
        return self._("de")

    @staticmethod
    def compare(a: dict, b: dict) -> bool:
        """Compares representative values.

        If the plain values are equals or don't exist, the comparison is based on the
        mountain value.

        Args:
            a: First value to compare
            b: Second value to compare.

        Returns:
            bool: True if dictionary a is the largest, False otherwise.
        """
        try:
            operator = ComparisonOperator(a["plain"]["operator"].strict)
            if not operator.is_order or operator(
                a["plain"]["value"], b["plain"]["value"]
            ):
                return True
            if a["plain"]["value"] != b["plain"]["value"]:
                return False
        except KeyError:
            if (plain_in_a := "plain" in a) or "plain" in b:
                return plain_in_a

        try:
            operator = ComparisonOperator(a["mountain"]["operator"].strict)
            return operator.is_order and operator(
                a["mountain"]["value"], b["mountain"]["value"]
            )
        except KeyError:
            return "mountain" in a

    def units(self, units: Optional[str]) -> str:
        """
        Translate the unity. If None then it returns an empty string

        Args:
            units: Unit to translate.

        Returns:
            Translated unity or an empty string.
        """
        return self._(units) or ""

    def round(self, x: Optional[float], **_kwargs) -> Optional[str]:
        """
        Make a rounding of the value.

        Args:
            x: Value to round.
            **_kwargs: Keyword arguments (not used here).

        Returns:
            String of the rounded value or None if not possible.
        """
        if x is None:
            return None
        return str(x) if abs(x) > 1e-6 else ""

    @property
    def around(self) -> str:
        return get_synonym(self.around_word, self.language)

    def compute_value(self, _value: float, text_value: str, unit: str) -> str:
        return f"{text_value}\xa0{unit}"

    def _compute_plain_frmt_table(self, frmt_table: dict) -> Optional[str]:
        if "plain" not in self.infos:
            return None

        plain_dict = self.infos["plain"]
        operator = ComparisonOperator(plain_dict.get("operator"))
        rep_value, local = self.parent.replace_critical(plain_dict)
        rep_plain = self.round(rep_value, operator=operator)
        if rep_plain is not None:
            if rep_plain != "":
                frmt_table["plain_value"] = self.compute_value(
                    rep_value, rep_plain, self.units(plain_dict["units"])
                )

            local_plain = self.round(local, operator=operator)
            if local_plain is not None and local_plain != rep_plain:
                frmt_table["local_plain_value"] = self.compute_value(
                    local, local_plain, self.units(plain_dict["units"])
                )
        return rep_plain

    def _compute_mountain_frmt_table(self, frmt_table: dict, rep_plain: Optional[str]):
        if "mountain" not in self.infos:
            return
        operator = ComparisonOperator(self.infos["mountain"].get("operator"))
        rep_value, local = self.parent.replace_critical(self.infos["mountain"])
        rep_mountain = self.round(rep_value, operator=operator)
        if rep_mountain is not None and (
            self.differentiate_plain_and_mountain or rep_plain != rep_mountain
        ):
            if rep_mountain != "":
                frmt_table["mountain_value"] = self.compute_value(
                    rep_value, rep_mountain, self.units(self.infos["mountain"]["units"])
                )

            local_mountain = self.round(local, operator=operator)
            if local_mountain is not None and local_mountain != rep_mountain:
                frmt_table["local_mountain_value"] = self.compute_value(
                    local, local_mountain, self.units(self.infos["mountain"]["units"])
                )

    @cached_property
    def format_table(self):
        frmt_table = {
            "var_name": "" if "ME" in self.infos else self.phenomenon,
            "definite_var_name": self.definite_var_name,
            "indefinite_var_name": self.indefinite_var_name,
            "feminine": "e" if self.feminine else "",
            "plural": "s" if self.plural else "",
            "around": self.around,
            "accumulated_hours": "",
        }

        rep_plain = self._compute_plain_frmt_table(frmt_table)
        self._compute_mountain_frmt_table(frmt_table, rep_plain)

        if (
            self.merge_locals is False
            or "plain" not in self.infos
            or "mountain" not in self.infos
        ):
            return frmt_table

        # Merge plain and mountain local values if it is possible
        p_value = frmt_table.get("plain_value")
        m_value = frmt_table.get("mountain_value")
        lp_value = frmt_table.get("local_plain_value")
        lm_value = frmt_table.get("local_mountain_value")

        if m_value is not None and m_value == p_value:
            frmt_table["equals_plain_mountain"] = True
            frmt_table.pop("mountain_value", None)
            frmt_table.pop("local_mountain_value", None)
            if lp_value is None and lm_value is not None:
                frmt_table["plain_value"] += (
                    self._(" (localement {lm_value} sur les hauteurs)")
                ).format(lm_value=lm_value)

        elif (
            p_value is None
            and m_value is None
            and lp_value is not None
            and lp_value == lm_value
        ):
            frmt_table["equals_plain_mountain"] = True
            frmt_table.pop("mountain_value", None)
            frmt_table.pop("local_mountain_value", None)

        return frmt_table

    @property
    def can_merge_values(self) -> bool:
        return self.format_table.get("equals_plain_mountain", False)

    def compute_reduction(self) -> dict:
        """
        Make computation and returns the reduced data.

        Returns:
            dict: Reduced data
        """
        return self.format_table


class _HandleWindOnBrideRepValue(RepValueReducer):

    @classmethod
    @abstractmethod
    def interval_rep(cls, x: float) -> tuple[int, int]:
        pass

    def compute_value(self, value: float, text_value: str, unit: str) -> str:
        if self.parent.hazard_name != "Vent sur pont" or self.infos["var_name"] not in [
            "FF__HAUTEUR10",
            "RAF__HAUTEUR10",
        ]:
            return super().compute_value(value, text_value, unit)

        bridge_value = self.round(value * 1.3)
        if bridge_value == text_value:
            return super().compute_value(value, text_value, unit)

        return f"{text_value}\xa0{unit}, {bridge_value}\xa0{unit} " + self._(
            "sur le pont"
        )

    def round(self, x: Optional[float], **_kwargs) -> Optional[str]:
        """
        Rounds values to the nearest interval of 5.
        Examples:
            Input --> Output
             7.5   -->  5 à 10
             12.5   -->  10 à 15

        Args:
            x: Value to round
            **_kwargs: Keyword arguments (not used here).

        Returns:
            Rounded value or None if not possible
        """
        if x is None:
            return None

        start, stop = self.interval_rep(x)
        return (
            self._(_start_stop_str).format(start=start, stop=stop) if start > 0 else ""
        )


class FFRepValueReducer(_HandleWindOnBrideRepValue):
    feminine: bool = False
    plural: bool = False
    interval_size: ClassVar[int] = 5

    @property
    def phenomenon(self) -> str:
        return self._("vent moyen")

    @classmethod
    def interval_rep(cls, x: float) -> tuple[int, int]:
        start = (int(x / cls.interval_size)) * cls.interval_size
        return start, start + cls.interval_size


class TemperatureRepValueReducer(RepValueReducer):
    feminine: bool = True
    plural: bool = False

    @property
    def phenomenon(self) -> str:
        return self._("température")

    @property
    def around_word(self) -> str:
        return self._("aux alentours de")

    def round(self, x: Optional[float], **kwargs) -> Optional[str]:
        """
        Rounds down or up as appropriate.

        Examples:
            Input --> Output
             7.5 + <=  -->  7
             7.5 + >= -->  8

        Args:
            x: Value to round.
            **kwargs: Keywords argument.

        Returns:
            Rounded value or None if not possible
        """
        if super().round(x) is None:
            return None
        if ComparisonOperator(kwargs["operator"]).is_decreasing_order:
            return str(int(np.floor(x)))
        return str(int(np.ceil(x)))


class TemperatureMinDailyRepValueReducer(TemperatureRepValueReducer):
    @property
    def phenomenon(self) -> str:
        return self._("température minimale quotidienne")


class TemperatureMaxDailyRepValueReducer(TemperatureRepValueReducer):
    @property
    def phenomenon(self) -> str:
        return self._("température maximale quotidienne")


class FFRafRepValueReducer(_HandleWindOnBrideRepValue):
    feminine: bool = True
    plural: bool = True
    interval_size: ClassVar[int] = 10

    @property
    def phenomenon(self) -> str:
        return self._("rafales")

    @classmethod
    def interval_rep(cls, x: float) -> tuple[int, int]:
        """
        Returns the representative interval of given gust value.

        Args:
            x: Gust value.

        Returns:
            Representative interval of gust value.
        """
        start: int = int(round_to_previous_multiple(x, cls.interval_size))
        return start, start + cls.interval_size


class AccumulationRepValueReducer(RepValueReducer):
    feminine: bool = False
    bounds: List
    last_bound_size: int
    differentiate_plain_and_mountain: bool = True

    @field_validator("infos", mode="before")
    def check_infos(cls, infos: dict) -> dict:
        """
        Validate if data has a var_name key with an accumulated variable as value.

        Args:
            infos: Information to validate.

        Returns:
            Validated information.

        Raises:
            ValueError: raised when the var_name has incorrect name.
        """
        super().check_infos(infos)

        var_name: str = infos["var_name"]

        accumulation: Optional[int] = split_var_name(var_name)[1]

        if not accumulation:
            raise ValueError(f"No accumulation found for '{var_name}' var_name.")

        return infos

    @property
    def var_name(self) -> str:
        return self.infos["var_name"]

    @property
    def accumulated_hours(self) -> int:
        """
        Gets the number of hours over which the var_name is accumulated.

        Returns:
            int: Number of hours over which the var_name is accumulated
        """
        return split_var_name(self.var_name)[1]

    @property
    def definite_var_name(self) -> str:
        return self.accumulation_time_suffix(
            f"{self.definite_article} {self.phenomenon}"
        )

    @property
    def indefinite_var_name(self) -> str:
        return self.accumulation_time_suffix(
            f"{self.indefinite_article} {self.phenomenon}"
        )

    @property
    def accumulated_phenomenon(self) -> str:
        return self.accumulation_time_suffix(self.phenomenon)

    def accumulation_time_suffix(self, var: str) -> str:
        return self._("{var} sur {accumulated_hours}h").format(
            var=var, accumulated_hours=self.accumulated_hours
        )

    @cached_property
    def format_table(self) -> dict[str, str]:
        return super().format_table | {
            "var_name": self.accumulated_phenomenon,
            "accumulated_hours": self._("en {accumulated_hours}h").format(
                accumulated_hours=self.accumulated_hours
            ),
        }

    def _value_as_string(self, x: float) -> str:
        for low_bound, up_bound in self.bounds:
            if x < up_bound:
                start, stop = low_bound, up_bound
                break
        else:
            start = int(x / self.last_bound_size) * self.last_bound_size
            stop = start + self.last_bound_size
        return self._(_start_stop_str).format(start=start, stop=stop)

    def round(self, x: Optional[float], **_kwargs) -> Optional[str]:
        if super().round(x) is None:
            return None
        if abs(x) > 1e-6:
            return self._value_as_string(x)
        return ""


class SnowRepValueReducer(AccumulationRepValueReducer):
    # List contents of the tuples with the lower limits and the amplitude of the
    # interval
    bounds: List = [(0, 1), (1, 3), (3, 5), (5, 7), (7, 10), (10, 15), (15, 20)]
    last_bound_size: int = 10

    @property
    def phenomenon(self) -> str:
        return self._("potentiel de neige")


class FallingWaterRepValueReducer(AccumulationRepValueReducer):
    # List contents of the tuples with the lower limits and the amplitude of the
    # interval
    bounds: List = [
        (3, 7),
        (7, 10),
        (10, 15),
        (15, 20),
        (20, 25),
        (25, 30),
        (30, 40),
        (40, 50),
        (50, 60),
        (60, 80),
        (80, 100),
    ]
    last_bound_size: int = 50

    def round(self, x: Optional[float], **kwargs) -> Optional[str]:
        """
        Rounds the value to the nearest interval.

        Args:
            x: Value to round.
            **kwargs: Keyword arguments.

        Returns:
            Rounded value.

        Examples:
            Input --> Output
             42   -->  40 to 45
             39   -->  35 to 40
        """
        rounded_x = super().round(x, **kwargs)
        if rounded_x is None:
            return None
        if rounded_x != "" and x < 3:
            return self._("au maximum") + " 3"
        return rounded_x


class PrecipitationRepValueReducer(FallingWaterRepValueReducer):
    @property
    def phenomenon(self) -> str:
        return self._("cumul de précipitation")


class RainRepValueReducer(FallingWaterRepValueReducer):
    @property
    def phenomenon(self) -> str:
        return self._("cumul de pluie")


class LpnRepValueReducer(RepValueReducer):
    def compute_reduction(self) -> dict:
        if (
            "LPN__SOL" not in self.parent.params
            or "WWMF__SOL" not in self.parent.params
        ):
            return {}

        geo_da = self.parent.geo(self.geo_id)
        if (
            snow_geo_da := geo_da.where(
                Wwmf.is_snow(self.parent.params["WWMF__SOL"].compute())
            )
        ).count() > 0:
            geo_da = snow_geo_da
        else:
            geo_da = self.parent.levels_of_risk(
                self.parent.final_risk_max_level(self.geo_id)
            )[0].spatial_risk_da.sel(id=self.geo_id)
            geo_da = geo_da.where(geo_da > 0)

        lpn_da = self.parent.params["LPN__SOL"].compute() * geo_da
        lpn = Lpn(da=lpn_da, period_describer=self.parent.period_describer)
        if lpn.extremums_da is None:
            return {}

        return {
            "key": lpn.template_key,
            "lpn": lpn.extremums,
            "temp": lpn.temporalities,
        }


class AltitudeRepValueReducer(RepValueReducer):
    """
    This class will represent the sentences "Surveillance client au-dessus/en-dessous de
    xxx m : ...

    """

    @field_validator("infos", mode="before")
    def check_infos(cls, infos: dict) -> dict:
        """
        This validator override RepValueReducer.check_infos which verifies that data
        has a key called var_name.

        Args:
            infos: Information value.

        Returns:
            Return simply data.
        """
        return infos

    @staticmethod
    def get_reducer(var_name: str) -> Optional[Callable]:
        prefix = split_var_name(var_name, full_var_name=False)[0]
        reducers = {
            "FF": FFRepValueReducer,
            "RAF": FFRafRepValueReducer,
            "T": TemperatureRepValueReducer,
            "TMAXQ": TemperatureMaxDailyRepValueReducer,
            "TMINQ": TemperatureMinDailyRepValueReducer,
            "PRECIP": PrecipitationRepValueReducer,
            "EAU": RainRepValueReducer,
            "NEIPOT": SnowRepValueReducer,
            "LPN": LpnRepValueReducer,
        }
        try:
            return reducers[prefix]
        except KeyError:
            return None

    def _compute_val(self, frmt_table: dict, key: str, is_accum: bool):
        new_val = frmt_table.get(key, "")
        if new_val:
            new_val = self._("de {new_val}").format(new_val=new_val)
        if local_val := frmt_table.get(f"local_{key}"):
            local_val = self._("localement de {local_val}").format(local_val=local_val)
            new_val = f"{new_val} ({local_val})" if new_val != "" else local_val
        return new_val if new_val or not is_accum else self._("non significatif")

    def compute_reduction(self) -> dict:
        """
        Make computation and returns the reduced data.

        Returns:
            dict: Reduced data
        """
        values: dict = {
            "plain_value": defaultdict(lambda: defaultdict(lambda: [])),
            "mountain_value": defaultdict(lambda: defaultdict(lambda: [])),
        }

        for var_name, infos in self.infos.items():
            reducer_class = self.get_reducer(var_name)
            if not reducer_class:
                continue

            reducer: RepValueReducer = reducer_class(
                infos=infos | {"var_name": var_name},
                differentiate_plain_and_mountain=True,
                merge_locals=False,
                parent=self.parent,
                geo_id=self.geo_id,
            )
            is_accum = isinstance(reducer, AccumulationRepValueReducer)
            accum = reducer.accumulation_time_suffix("") if is_accum else ""
            frmt_table = reducer.compute()

            for kind in {"plain", "mountain"} & infos.keys():
                value = self._compute_val(frmt_table, f"{kind}_value", is_accum)
                if value != "":
                    values[f"{kind}_value"][reducer.phenomenon][value].append(accum)

        last_delimiter = f" {self._('et')} "

        if not any(values.values()):
            return {}

        result = {"altitude": next(iter(self.infos.values())).get("mountain_altitude")}
        for key, value in values.items():
            if not value:
                continue

            result[key] = concatenate_string(
                [
                    phenomenon
                    + " "
                    + concatenate_string(
                        [
                            value
                            + concatenate_string(accums, last_delimiter=last_delimiter)
                            for value, accums in values[key][phenomenon].items()
                        ],
                        last_delimiter=last_delimiter,
                    )
                    for phenomenon in values[key]
                ],
                last_delimiter=last_delimiter,
            )

        return result


class RepValueBuilder(BaseBuilder):
    """
    This class enable to speak about representative values
    """

    module_name: str = "risk"
    reducer: Optional[RepValueReducer] = None
    reducer_class: type = RepValueReducer
    parent: Annotated[Optional[RiskComponentComposite], SkipValidation] = None
    not_significant_values: bool = False

    @property
    def template_name(self) -> str:
        """
        Get the template name.

        Returns:
            str: The template name.
        """
        return "rep_value_generic"

    @property
    def _template_key_kinds(self) -> List[str]:
        keys = []
        if (
            "plain" in self.infos and self.infos["plain"]["value"] is not None
        ) or "plain_value" in self.reduction:
            keys.append("plain")
        if (
            ("mountain" in self.infos and self.infos["mountain"]["value"] is not None)
            or "mountain_value" in self.reduction
        ) and not self.reducer.can_merge_values:
            keys.append("mountain")

        return keys

    @property
    def template_key(self) -> str:
        """
        Get the template key.

        Returns:
            Template key.
        """
        key_parts = []
        for zone in self._template_key_kinds:
            if f"{zone}_value" not in self.reduction:
                if self.not_significant_values:
                    key_parts.append(f"no_{zone}")

                if f"local_{zone}_value" in self.reduction:
                    key_parts.append(f"local_{zone}")
            else:
                if f"local_{zone}_value" in self.reduction:
                    key_parts.append("local")
                key_parts.append(zone)

        if key_parts and "ME" in self.infos:
            key_parts = ["ME"] + key_parts
        return "_".join(key_parts)

    @classmethod
    def get_builder(cls, infos: dict, base_geo: BaseGeo) -> Optional[RepValueBuilder]:
        """
        Returns a RepValueBuilder object for the given data dictionary.

        Args:
            infos: A dictionary of data, where the keys are the variable names and the
                values are the variable values.
            base_geo: Associated reducer or builder.

        Returns:
            A RepValueBuilder object for the given data dictionary, or None if no
            builder is available.
        """
        prefix = split_var_name(infos["var_name"], full_var_name=False)[0]
        builders = {
            "FF": FFRepValueBuilder,
            "RAF": FFRafRepValueBuilder,
            "T": TemperatureRepValueBuilder,
            "TMAXQ": TemperatureMaxDailyRepValueBuilder,
            "TMINQ": TemperatureMinDailyRepValueBuilder,
            "PRECIP": PrecipitationRepValueBuilder,
            "EAU": RainRepValueBuilder,
            "NEIPOT": SnowRepValueBuilder,
            "LPN": LpnRepValueBuilder,
        }
        try:
            return builders[prefix](
                infos=infos, parent=base_geo.parent, geo_id=base_geo.geo_id
            )
        except KeyError:
            return None

    def pre_process(self):
        """Make a pre-process operation on the text."""
        super().pre_process()
        rep_value = self.reduction.get("mountain_value") or self.reduction.get(
            "plain_value", ""
        )

        if rep_value.startswith("au"):
            self.reduction["around"] = "d'"
            self.text = self.text.replace("{around} ", "{around}")

    @staticmethod
    def _compute_all_altitude(base_geo: BaseGeo, all_infos: dict) -> str:
        altitude_data = defaultdict(dict)
        for key, infos in all_infos.items():
            altitude_data[split_var_name(key)[0]][key] = infos

        text = ""
        for param, infos in altitude_data.items():
            if param != "LPN__SOL":
                builder_class = AltitudeRepValueBuilder
            else:
                builder_class = LpnRepValueBuilder
                infos |= {"var_name": param}

            if builder_text := builder_class(
                infos=infos, parent=base_geo.parent, geo_id=base_geo.geo_id
            ).compute():
                text += f"\n{builder_text}"

        return text.rstrip()

    @staticmethod
    def _compute_all_no_altitude(base_geo: BaseGeo, all_infos: dict) -> str:
        text = ""
        for key, infos in all_infos.items():
            builder_class = RepValueBuilder.get_builder(
                infos | {"var_name": key}, base_geo
            )
            if isinstance(builder_class, LpnRepValueBuilder):
                text += "\n"
            if builder_class is not None:
                text += builder_class.compute() + " "
        return text.rstrip()

    @staticmethod
    def compute_all(base_geo: BaseGeo, all_data: dict) -> str:
        """
        Calculates a textual representation of all the variables in the given data
        dictionary.

        Args:
            base_geo: Associated reducer or builder
            all_data: A dictionary of data, where the keys are the variable names and
                the values are the variable values.

        Returns:
            A textual representation of all the variables in the data dictionary.
        """
        if not all_data:
            return ""

        # If monitoring with altitude, generate a specific sentence
        if "mountain_altitude" in next(iter(all_data.values())):
            return RepValueBuilder._compute_all_altitude(base_geo, all_data)

        # Otherwise, generate a sentence for each variable
        return RepValueBuilder._compute_all_no_altitude(base_geo, all_data)


class FFRepValueBuilder(RepValueBuilder):
    reducer_class: type = FFRepValueReducer
    not_significant_values: bool = True


class TemperatureRepValueBuilder(RepValueBuilder):
    reducer_class: type = TemperatureRepValueReducer


class TemperatureMaxDailyRepValueBuilder(RepValueBuilder):
    reducer_class: type = TemperatureMaxDailyRepValueReducer


class TemperatureMinDailyRepValueBuilder(RepValueBuilder):
    reducer_class: type = TemperatureMinDailyRepValueReducer


class FFRafRepValueBuilder(RepValueBuilder):
    reducer_class: type = FFRafRepValueReducer
    not_significant_values: bool = True


class SnowRepValueBuilder(RepValueBuilder):
    reducer_class: type = SnowRepValueReducer
    not_significant_values: bool = True


class PrecipitationRepValueBuilder(RepValueBuilder):
    reducer_class: type = PrecipitationRepValueReducer
    not_significant_values: bool = True


class RainRepValueBuilder(RepValueBuilder):
    reducer_class: type = RainRepValueReducer
    not_significant_values: bool = True


class LpnRepValueBuilder(RepValueBuilder):
    reducer_class: type = LpnRepValueReducer

    @property
    def template_name(self) -> str | List[str]:
        """
        Get the template name.

        Returns:
            str: The template name.
        """
        return "rep_value_lpn"

    @cached_property
    def template_key(self) -> Optional[str | List | np.ndarray]:
        """
        Get the template key.

        Returns:
            str | np.ndarray: The template key.
        """
        return self.reduction.get("key")


class AltitudeRepValueBuilder(RepValueBuilder):
    reducer_class: type = AltitudeRepValueReducer

    @property
    def template_name(self) -> str:
        """
        Get the template name.

        Returns:
            str: The template name.
        """
        return "rep_value_altitude"

    def compute(self) -> str:
        return super().compute() if self.reduction else ""
