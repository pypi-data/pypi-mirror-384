from __future__ import annotations

import copy
import operator
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
from pydantic import StrictInt, ValidationInfo, field_validator, model_validator

import mfire.utils.mfxarray as xr
from mfire.composite.aggregation import Aggregation, AggregationMethod, Aggregator
from mfire.composite.base import BaseComposite, BaseModel
from mfire.composite.field import FieldComposite
from mfire.composite.geo import AltitudeComposite, GeoComposite
from mfire.composite.operator import ComparisonOperator
from mfire.composite.serialized_types import s_threshold
from mfire.settings import SPACE_DIM, get_logger
from mfire.utils.calc import all_close
from mfire.utils.unit_converter import get_unit_context, unit_conversion
from mfire.utils.xr import da_set_up

# Logging
LOGGER = get_logger(name="composite.events.mod", bind="composite.events")


class Category(str, Enum):
    """Création d'une classe d'énumération contenant les categories possibles
    des unités
    """

    BOOLEAN = "boolean"
    QUANTITATIVE = "quantitative"
    CATEGORICAL = "categorical"
    RESTRICTED_QUANTITATIVE = "restrictedQuantitative"


class Threshold(BaseModel):
    """
    Threshold object containing the configuration of the plain and mountain objects for
    the Promethee production task.
    """

    threshold: s_threshold
    comparison_op: str | ComparisonOperator
    units: Optional[StrictInt | str] = None
    next_critical: Optional[float] = None

    def __eq__(self, other: Threshold) -> bool:
        return all(
            (
                self.comparison_op == other.comparison_op,
                self.units == other.units,
                all_close(self.next_critical, other.next_critical),
                all_close(self.threshold, other.threshold),
            )
        )

    @field_validator("comparison_op")
    def init_comparison_op(cls, value: str | ComparisonOperator) -> ComparisonOperator:
        return ComparisonOperator(value) if isinstance(value, str) else value

    @field_validator("threshold")
    def validate_threshold(cls, value: s_threshold) -> s_threshold:
        """
        Validator to validate the threshold value.

        Args:
            value: The threshold value to be validated.

        Returns:
            The validated threshold value.
        """
        if isinstance(value, list):
            return [
                int(x) if isinstance(x, float) and int(x) == x else x for x in value
            ]

        return int(value) if isinstance(value, float) and int(value) == value else value

    @model_validator(mode="before")
    def check_comparison_op_and_value(cls, values: dict) -> dict:
        """
        Validates the comparison operator and threshold.

        Args:
            values: The input values.

        Returns:
            The validated values.
        """
        if isinstance(values["threshold"], List) and values["comparison_op"] in (
            ComparisonOperator.EGAL,
            ComparisonOperator.DIF,
        ):
            if len(values["threshold"]) > 1:
                values["comparison_op"] = (
                    ComparisonOperator.ISIN
                    if values["comparison_op"] == ComparisonOperator.EGAL
                    else ComparisonOperator.NOT_ISIN
                )
            else:
                values["threshold"] = values["threshold"][0]
        return values

    @staticmethod
    def from_configuration(threshold: Optional[dict]) -> Optional[Threshold]:
        return (
            Threshold(
                threshold=threshold["threshold"],
                comparison_op=threshold["comparisonOp"],
                units=threshold["units"],
            )
            if threshold is not None
            else None
        )

    def change_units(self, new_units: str, context: Optional[str] = None) -> Threshold:
        """This function changes the threshold to match the units of the field.

        Args:
            new_units: New units to convert.
            context: Possible context for DataArray.

        Returns:
            Threshold: The modified threshold.
        """
        threshold = copy.deepcopy(self)
        if isinstance(threshold.units, str) and threshold.units != new_units:
            threshold.threshold = unit_conversion(
                (threshold.threshold, threshold.units), new_units, context=context
            )
            if threshold.next_critical is not None:
                threshold.next_critical = unit_conversion(
                    (threshold.next_critical, threshold.units),
                    new_units,
                    context=context,
                )
            threshold.units = new_units
        return threshold

    def update_next_critical(self, threshold: Threshold):
        """
        This function updates the next_critical value of threshold. It adds an
        information (next_critical) about the threshold of the next higher level.
        If a next_critical value exists, it checks if the value of that level is
        less critical.

        Args:
            threshold: The dictionary of another threshold
        """
        if (
            self.comparison_op.is_order
            and self.comparison_op.strict == threshold.comparison_op.strict
        ):
            # In this case, we will check if the value is more critical
            # than the base value and less critical than the next one
            # Check if the value is more critical than the current one
            threshold = threshold.change_units(self.units)
            if self.comparison_op(threshold.threshold, self.threshold) and (
                self.next_critical is None
                or self.comparison_op(threshold.threshold, self.next_critical)
            ):
                self.next_critical = threshold.threshold


class EventComposite(BaseComposite):
    """
    Object containing the configuration of the event elements  for the Promethee
    production task.
    """

    type: Literal["no_accumulation"] = "no_accumulation"

    field: FieldComposite
    category: Category
    plain: Optional[Threshold] = None
    mountain: Optional[Threshold] = None
    mountain_altitude: Optional[int] = None
    altitude: AltitudeComposite
    geos: GeoComposite | xr.DataArray
    aggregation: Optional[Aggregation] = None

    _values_ds: xr.Dataset = xr.Dataset()
    _field_da: Optional[xr.DataArray] = None

    def reset(self) -> EventComposite:
        super().reset()
        self._values_ds = xr.Dataset()
        self._field_da = None
        return self

    @property
    def values_ds(self) -> Optional[xr.Dataset]:
        """Get the values dataset.

        Returns:
            Optional[xr.Dataset]: Values dataset.
        """
        return self._values_ds

    @field_validator("mountain")
    def check_plain_or_mountain(cls, val: Optional[Threshold], info: ValidationInfo):
        if not info.data.get("plain") and not val:
            raise ValueError("Either plain or mountain is required")
        return val

    @property
    def is_pre_aggregation(self):
        return self.aggregation is not None and self.aggregation.is_pre

    @property
    def is_post_aggregation(self):
        return self.aggregation is not None and self.aggregation.is_post

    @property
    def geos_da(self) -> xr.DataArray:
        return self.geos.compute() if isinstance(self.geos, GeoComposite) else self.geos

    @property
    def geos_id(self) -> List[str]:
        if isinstance(self.geos, xr.DataArray):
            return self.geos.id.values.tolist()
        if self.geos.mask_id is None:
            return []
        return (
            self.geos.mask_id
            if isinstance(self.geos.mask_id, List)
            else [self.geos.mask_id]
        )

    @property
    def mask(self) -> Optional[xr.MaskAccessor]:
        """Get the mask.

        Returns:
            Optional[xr.MaskAccessor]: Mask accessor.
        """
        geos_mask_da = da_set_up(self.geos_da, self.field_da).mask.f32

        alt_field_da = self.altitude.compute()
        alt_mask_da = da_set_up(alt_field_da, self.field_da).notnull()
        return (geos_mask_da * alt_mask_da).mask

    @property
    def field_da(self) -> Optional[xr.DataArray]:
        """Get the values dataset.

        Returns:
            Optional[xr.DataArray]: Values dataset.
        """
        if self._field_da is None:
            self._field_da = self.field.compute()
        return self._field_da

    def compute(self) -> Optional[xr.DataArray | xr.Dataset]:
        """
        Compute the event based on the initialized fields and return the data as a
        DataArray.

        Returns:
            xr.DataArray: The computed data of the event.
        """
        # Compute for plain and mountain
        plain_da, mountain_da = self.compute_plain_and_mountain()

        # Aggregate if necessary
        return self.compute_post_aggregation(plain_da, mountain_da)

    @property
    def comparison(self) -> dict:
        """
        Get the comparison operator for an event.

        Returns:
            dict: Dictionary of comparison operator (on plain or mountain). Here
                is an example of the results:
                {
                    "plain": Threshold(...),
                    "mountain": Threshold(...),
                    "category": ...,
                    "mountain_altitude": ...,
                    "aggregation": ...,
                }
        """
        dict_out: Dict[str, Any] = {"category": self.category}
        if self.plain is not None:
            dict_out["plain"] = self.plain
        if self.mountain is not None:
            dict_out["mountain"] = self.mountain
        if self.mountain_altitude is not None:
            dict_out["mountain_altitude"] = self.mountain_altitude

        # Get the aggregation function. Will be used for future checks.
        dict_out["aggregation"] = (
            self.aggregation.model_dump() if self.aggregation is not None else {}
        )
        return dict_out

    @property
    def cover_period(self) -> List[np.datetime64]:
        """
        Get the period covered by the event.

        This method opens the DataArray to get the coordinates of the time dimension.
        The coordinates are then converted to `Datetime` objects and returned as a list.

        Returns:
            List[Datetime]: The period covered by the event.
        """
        return list(self.field.coord("valid_time").astype("datetime64[ns]"))

    def update_selection(
        self, new_sel: dict, new_slice: dict, new_isel: dict, new_islice: dict
    ):
        """
        Update the selection of the field and field_1.

        Args:
            new_sel: Selection dictionary for the field.
            new_slice: Slice dictionary for the field.
            new_isel: Index selection dictionary for the field.
            new_islice: Index slice dictionary for the field.
        """
        # Update selection for the main field
        if (selection := self.field.selection) is not None:
            selection.update(
                new_sel=new_sel,
                new_slice=new_slice,
                new_isel=new_isel,
                new_islice=new_islice,
            )

        # Update selection for field_1 if it exists
        if (field_1 := getattr(self, "field_1", None)) is not None:
            if (selection := field_1.selection) is not None:
                selection.update(
                    new_sel=new_sel,
                    new_slice=new_slice,
                    new_isel=new_isel,
                    new_islice=new_islice,
                )

    def get_risk(self, field_da: xr.DataArray, threshold: Threshold) -> xr.DataArray:
        """Function created to allow other child classes to implement the risk in
            another way.

        Args:
            field_da: The field DataArray values.
            threshold: Threshold to apply.

        Returns:
            Risk for every pixel.
        """
        result = threshold.comparison_op(field_da, threshold.threshold)
        return xr.where(field_da.notnull(), result, np.nan)

    def compute_density(self, risk_field_da: xr.DataArray) -> xr.DataArray:
        """Compute the density of an event.

        This function calculates the density of an event, regardless of the
        aggregation method used (e.g., average, DRR).

        Args:
            risk_field_da: Risk field

        Returns:
            xr.DataArray: Risk density
        """
        agg_handler = Aggregator(risk_field_da)
        density = agg_handler.compute(Aggregation(method=AggregationMethod.DENSITY))
        return density

    def compute_summarized_density(
        self, risk_field_da: xr.DataArray, mask_da: xr.DataArray
    ) -> xr.DataArray:
        """Compute the summarized density over time.

        Args:
            risk_field_da: Risk field.
            mask_da: Mask.

        Returns:
            xr.DataArray: Summarized density over time.
        """
        # Aggregate the risk field over time using the maximum threshold
        agg_handler_time = Aggregator(risk_field_da, aggregate_dim="valid_time")
        max_risk = (
            agg_handler_time.compute(Aggregation(method=AggregationMethod.MAX))
            * mask_da
        )

        # Compute the density using the maximum risk field
        agg_handler_space = Aggregator(max_risk)
        density = agg_handler_space.compute(
            Aggregation(method=AggregationMethod.DENSITY)
        )
        return density

    def get_extreme_values(
        self, field_da: xr.DataArray, unit: str
    ) -> Tuple[Optional[xr.DataArray], Optional[xr.DataArray]]:
        """
        Get extreme values, that is the minimum and maximum values.

        Arguments:
            field_da: The DataArray for which to find the minimum and maximum.
            unit: Unit of the result.

        Returns:
            The two extreme values representing the minimum and maximum values.
        """
        if self.category not in (
            Category.QUANTITATIVE,
            Category.RESTRICTED_QUANTITATIVE,
        ):
            return None, None

        agg_handler = Aggregator(field_da)
        min_agg = Aggregation(method=AggregationMethod.MIN)
        max_agg = Aggregation(method=AggregationMethod.MAX)
        min_da = unit_conversion(agg_handler.compute(min_agg), unit)
        max_da = unit_conversion(agg_handler.compute(max_agg), unit)
        return min_da, max_da

    def get_representative_values(
        self, field_da: xr.DataArray, threshold: Threshold
    ) -> Optional[xr.DataArray]:
        """
        Returns the representative threshold of the field. Handles aggregation by mean
        and density ratio regions (if the comparison operator is in [<,<=,>,>=]).

        Args:
            field_da: The field.
            threshold: the threshold of the current event

        Returns:
            The representative threshold. Returns None if the
                variable is qualitative/boolean or an error occurred.

        Raises:
            ValueError: If the comparison operator is not in [<,<=,>,>=, inf, infegal,
                sup, supegal] and the aggregation method is density ratio regions.
        """
        # Check if the category is quantitative or restricted quantitative
        if self.category not in (
            Category.QUANTITATIVE,
            Category.RESTRICTED_QUANTITATIVE,
        ):
            return None

        # Perform aggregation based on the method
        agg_handler = Aggregator(field_da)
        if self.aggregation is None or self.aggregation.method.startswith(
            "requiredDensity"
        ):
            from mfire.utils.string import split_var_name

            prefix = split_var_name(str(field_da.name), full_var_name=False)[0]
            if prefix in ["PRECIP", "EAU"]:
                thresh = 0.75
            elif prefix == "NEIPOT":
                thresh = 0.5
            else:
                thresh = 0.9
            try:
                if threshold.comparison_op.is_increasing_order:
                    quantile = thresh
                elif threshold.comparison_op.is_decreasing_order:
                    quantile = 1 - thresh
                else:
                    LOGGER.error(
                        f"Unknown case {threshold.comparison_op}",
                        func="get_representative_values",
                    )
                    raise ValueError(
                        f"Representative value is not possible to give with comparison "
                        f"operator {threshold.comparison_op}"
                    )  # Compute the desired quantile

                rep_value = agg_handler.compute(
                    Aggregation(
                        method=AggregationMethod.QUANTILE, kwargs={"q": quantile}
                    )
                ).drop_vars("quantile")

            except Exception as excpt:
                # Handle aggregation failure
                LOGGER.error(
                    f"Aggregation failed on the field: {field_da}",
                    comparison_op=threshold.comparison_op,
                    field=field_da,
                    func="get_representative_values",
                    excpt=excpt,
                )
                raise ValueError from excpt
        elif self.aggregation.is_pre:
            # Aggregation by mean or other non-threshold methods
            rep_value = agg_handler.compute(self.aggregation)
        else:
            # Invalid aggregation method
            LOGGER.error(
                f"Unknown aggregation method: {self.aggregation.method}",
                func="get_representative_values",
            )
            raise ValueError(
                f"Representative value is not possible to give with aggregation "
                f"method: {self.aggregation.method}"
            )

        # Convert to the original unit
        return unit_conversion(rep_value, threshold.units)

    def _compute_values(self, field: xr.DataArray, kind: Literal["plain", "mountain"]):
        threshold = self.plain if kind == "plain" else self.mountain

        if self.category in (Category.QUANTITATIVE, Category.RESTRICTED_QUANTITATIVE):
            self._values_ds[f"threshold_{kind}"] = threshold.threshold

        (mini, maxi) = self.get_extreme_values(field, threshold.units)
        if mini is not None:
            self._values_ds[f"min_{kind}"] = mini
            self._values_ds[f"max_{kind}"] = maxi

        rep_value = self.get_representative_values(field, threshold=threshold)
        if rep_value is not None:
            self._values_ds[f"rep_value_{kind}"] = rep_value

    def compute_plain_and_mountain(self) -> Tuple[xr.DataArray, xr.DataArray]:
        """
        Compute the risk and various representative/extreme values for plain or plain
        and mountain.

        Returns:
            Tuple containing respectively the risk for plain and mountain.
        """
        plain_risk, plain_field, plain_threshold = None, None, None
        mountain_risk, mountain_field, mountain_threshold = None, None, None

        alt_field_da = self.altitude.compute()
        unit_context = get_unit_context(str(self.field_da.name))

        if self.plain is not None:
            plain_threshold = self.plain.change_units(
                self.field_da.units, context=unit_context
            )
            plain_mask = (
                (alt_field_da <= self.mountain_altitude) * self.mask.bool
                if self.mountain_altitude is not None
                else self.mask.bool
            ).mask.f32
            plain_field = xr.DataArray(
                self.field_da * plain_mask, name=self.field_da.name
            )
            plain_risk = self.get_risk(plain_field, plain_threshold)

            self._compute_values(plain_field, "plain")

        if self.mountain is not None:
            mountain_threshold = self.mountain.change_units(
                self.field_da.units, context=unit_context
            )
            mountain_mask = (
                (alt_field_da > self.mountain_altitude) * self.mask.bool
            ).mask.f32
            mountain_field = xr.DataArray(
                self.field_da * mountain_mask, name=self.field_da.name
            )

            mountain_risk = self.get_risk(mountain_field, mountain_threshold)

            self._compute_values(mountain_field, "mountain")

        risk_field = xr.MaskAccessor.sum(plain_risk, mountain_risk)
        self._values_ds["density"] = self.compute_density(risk_field)

        self._values_ds["summarized_density"] = self.compute_summarized_density(
            risk_field, self.mask.bool
        )

        if self.is_pre_aggregation:
            if plain_field is not None:
                plain_field = Aggregator(plain_field).compute(self.aggregation)
                plain_risk = self.get_risk(plain_field, plain_threshold)

            # It would make more sense to say `if self.moutain is not None`
            # but Sonar throws a tantrum because it thinks that mountain_field
            # can be None, even though its valeur is explicitly set when
            # self.mountain is not None...
            if mountain_field is not None:
                mountain_field = Aggregator(mountain_field).compute(self.aggregation)
                mountain_risk = self.get_risk(mountain_field, mountain_threshold)

        if plain_risk is None:
            plain_risk = xr.full_like(mountain_risk, np.nan)
        if mountain_risk is None:
            mountain_risk = xr.full_like(plain_risk, np.nan)
        return plain_risk, mountain_risk

    def _compute_pm_occurrence(
        self, da: xr.DataArray, occurrence_event: bool
    ) -> xr.DataArray:
        # Compute the occurrence in plain or in mountain.
        occurrence: xr.DataArray = da > 0

        reduced_dims: list[str] = [d for d in SPACE_DIM if d in (da.dims)]
        if reduced_dims:
            occurrence = occurrence.any(reduced_dims)

        if occurrence_event is False:
            occurrence = xr.full_like(occurrence, False)

        occurrence.attrs = {}

        return occurrence

    def compute_post_aggregation(
        self, plain_da: xr.DataArray, mountain_da: xr.DataArray
    ) -> xr.DataArray:
        """
        Calculate the risk. If aggregation is specified, it can be done before (
            mean/quantile/...) or after the comparison with the operator (ddr/density).
            This function can take into account altitude conditions (if they have been
            properly specified).

        Args:
            plain_da: The risk DataArray for plain field.
            mountain_da: The risk DataArray for mountain field.

        Returns:
            xr.DataArray: The risk DataArray for this event.
        """
        risk_da = xr.DataArray(
            xr.MaskAccessor.sum(plain_da, mountain_da), name=self.field_da.name
        )

        # Perform post aggregation if specified
        if self.is_post_aggregation:
            agg_handler = Aggregator(risk_da)
            risk_da = agg_handler.compute(self.aggregation)
            self._values_ds["threshold_dr"] = self.aggregation.kwargs.get("dr")

        occurrence_event = (risk_da > 0).any().item()
        self._values_ds["occurrence_event"] = occurrence_event

        self._values_ds["occurrence_plain"] = self._compute_pm_occurrence(
            plain_da, occurrence_event
        )
        self._values_ds["occurrence_mountain"] = self._compute_pm_occurrence(
            mountain_da, occurrence_event
        )

        self._values_ds["weatherVarName"] = ("tmp", [self.field_da.name])

        try:
            self._values_ds["units"] = ("tmp", [self.plain.units])
        except AttributeError:
            self._values_ds["units"] = ("tmp", [self.mountain.units])

        return risk_da > 0


class EventAccumulationComposite(EventComposite):
    """
    Object containing the configuration of the Accumulation event for the promethee
    production task.
    """

    type: Literal["accumulation"] = "accumulation"
    field_1: FieldComposite
    cum_period: int

    @property
    def field_da(self) -> Optional[xr.DataArray]:
        """
        Compute the values DataArray.

        Returns:
            Values dataset.

        Raises:
            ValueError: Data must have the same units
        """
        if self._field_da is None:
            field_da = super().field_da
            rr1_da = self.field_1.compute()

            if field_da.GRIB_stepUnits != rr1_da.GRIB_stepUnits:
                raise ValueError(
                    "Both cumulative fields do not have the same stepUnits. "
                    f"Simple field is {field_da.GRIB_stepUnits} and "
                    f"cumulField is {rr1_da.GRIB_stepUnits}."
                )

            # Divide the time over which cumulations are taken by the step size.
            # This yields a properly defined risk.
            n = int(self.cum_period / rr1_da.accum_hour)
            max_p = field_da["valid_time"].size
            max_p = min(max_p, n)

            self._field_da = field_da.rolling(
                {"valid_time": max_p}, min_periods=1
            ).max()
            self._field_da.attrs.update(field_da.attrs)
            self._field_da.name = field_da.name

        return self._field_da

    def get_risk(self, field_da: xr.DataArray, threshold: Threshold) -> xr.DataArray:
        """
        Calculate the risk for cumulative events such as Rainfall.

        Args:
            field_da: Field (RRn in the future).
            threshold: Threshold for the accumulation event.

        Returns:
            The calculated risk.

        Raises:
            ValueError: Data must have the same units
        """
        rr1_da = self.field_1.compute()
        if field_da.GRIB_stepUnits != rr1_da.GRIB_stepUnits:
            raise ValueError(
                "Both cumulative fields do not have the same stepUnits. "
                f"Simple field is {field_da.GRIB_stepUnits} and "
                f"cumulField is {rr1_da.GRIB_stepUnits}."
            )

        if self.is_pre_aggregation:
            agg_handler = Aggregator(rr1_da)
            rr1_da = agg_handler.compute(self.aggregation)

        # Replace n with the maximum dataset size. Otherwise, we cannot take the
        # maximum. Divide the time over which cumulations are taken by the step size.
        # This yields a properly defined risk.
        n = int(self.cum_period / rr1_da.accum_hour)

        start = operator.and_(
            threshold.comparison_op(field_da, threshold.threshold),
            threshold.comparison_op(rr1_da, threshold.threshold / n),
        )
        keep = operator.and_(
            threshold.comparison_op(field_da, threshold.threshold),
            threshold.comparison_op(self.field.compute(), threshold.threshold / n),
        )
        risk = start.copy()

        for step in range(len(risk["valid_time"].values)):
            if step > 0:
                current_risk = operator.or_(
                    risk.isel({"valid_time": step - 1})
                    * keep.isel({"valid_time": step}),
                    start.isel({"valid_time": step}),
                )
                risk.isel({"valid_time": step})[:] = current_risk[:]

        risk.attrs.update(rr1_da.attrs)
        return xr.where(field_da.notnull(), risk, np.nan)
