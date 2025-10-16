from __future__ import annotations

from pathlib import Path
from typing import Annotated, Dict, List, Optional

import numpy as np
from pydantic import Field, ValidationInfo, field_validator

import mfire.utils.mfxarray as xr
from mfire.composite.aggregation import (
    Aggregation,
    AggregationMethod,
    AggregationType,
    Aggregator,
)
from mfire.composite.base import BaseComposite, BaseModel
from mfire.composite.event import EventAccumulationComposite, EventComposite
from mfire.composite.operator import LogicalOperator
from mfire.settings import get_logger
from mfire.utils.xr import MaskLoader

# Logging
LOGGER = get_logger(name="levels.mod", bind="level")


class LocalisationConfig(BaseModel):
    """
    Class containing information related to location.
    """

    compass_split: bool = False
    altitude_split: bool = False
    geos_descriptive: List[str] = []


class LevelComposite(BaseComposite):
    """
    Object containing the configuration of levels for the Promethee production task.
    """

    level: int
    aggregation_type: AggregationType
    aggregation: Optional[Aggregation] = None
    logical_op_list: List[str | LogicalOperator] = []
    events: Annotated[
        List[EventAccumulationComposite | EventComposite], Field(discriminator="type")
    ]
    localisation: LocalisationConfig

    _spatial_risk_da: xr.DataArray = xr.DataArray()

    @field_validator("logical_op_list")
    def init_logical_op_list(cls, val: str | LogicalOperator) -> List[LogicalOperator]:
        return [LogicalOperator(v) for v in val]

    @field_validator("aggregation")
    def check_aggregation(cls, v: Optional[Aggregation], info: ValidationInfo):
        """
        Validates the aggregation value based on the aggregation_type.

        Args:
            v: Input aggregation value.
            info: Information for validation.

        Returns:
            The validated aggregation value.

        Raises:
            ValueError: If the aggregation is missing and the aggregation_type is not
                AggregationType.UP_STREAM.
        """
        if info.data.get("aggregation_type") == AggregationType.UP_STREAM:
            return None
        if v is None:
            raise ValueError("Missing expected value 'aggregation' in level")
        return v

    @field_validator("events")
    def check_nb_elements(cls, v: List, info: ValidationInfo):
        """
        Validates the number of elements in events based on the
        aggregation_type.

        Args:
            v: Input events value.
            info: Input values.

        Returns:
            The validated events value.

        Raises:
            ValueError: If the number of logical operators is not consistent with the
                number of elements in the case of upstream aggregation.
        """
        if info.data.get("aggregation_type") == AggregationType.UP_STREAM:
            logical_op_list = info.data.get("logical_op_list") or []
            if len(logical_op_list) != len(v) - 1:
                raise ValueError(
                    "The number of logical operator is not consistent with the len "
                    f"of element list. Should be {len(v)-1}."
                )
        return v

    def is_same_than(self, other: LevelComposite):
        if self.logical_op_list != other.logical_op_list or len(self.events) != len(
            other.events
        ):
            return False
        return all(
            evt.plain == other_evt.plain and evt.mountain == other_evt.mountain
            for evt, other_evt in zip(self.events, other.events)
        )

    @property
    def mask(self) -> Optional[xr.MaskAccessor]:
        """
        Computes and returns the mask data array.

        Returns:
            xr.DataArray: Mask data array.
        """
        return xr.MaskAccessor.unions(*(evt.mask for evt in self.events))

    @property
    def spatial_risk_da(self) -> xr.DataArray:
        """
        Returns the spatial risk data array.

        Returns:
            xr.DataArray: Spatial risk data array.
        """
        return self._spatial_risk_da

    @property
    def alt_min(self) -> int:
        """
        Returns the minimum altitude among all events.

        Returns:
            int: Minimum altitude.
        """
        return min(ev.altitude.alt_min for ev in self.events if ev.altitude is not None)

    @property
    def alt_max(self) -> int:
        """
        Returns the maximum altitude among all events.

        Returns:
            int: Maximum altitude.
        """
        return max(ev.altitude.alt_max for ev in self.events if ev.altitude is not None)

    @property
    def cover_period(self) -> List[np.datetime64]:
        """
        Get the cover period of the first event.

        This method returns the cover period of the first event in the `events`
        list.

        Returns:
            List[Datetime]: The cover period of the first event.
        """
        return self.events[0].cover_period

    @property
    def is_accumulation(self) -> bool:
        """
        Checks if all events in the list are of type EventAccumulationComposite.

        Returns:
            bool: True if all events are of type EventAccumulationComposite,
                False otherwise.
        """
        return all(
            isinstance(event, EventAccumulationComposite) for event in self.events
        )

    def get_single_evt_comparison(self) -> Dict:
        """
        Gets the comparison operator for a single event.

        Returns:
            Dict: A list of comparison operators for a single event.
                None if there are multiple events.
        """
        return self.events[0].comparison

    @property
    def comparison(self) -> dict:
        """
        Gets the comparison operators for a level.

        Returns:
            dict: Dictionary of comparison operators (on plain or mountain).
        """
        dout = {}
        for event in self.events:
            field_name = event.field.name
            comparison = event.comparison
            if field_name is not None and field_name not in dout:
                dout[field_name] = comparison
            elif field_name in dout and dout[field_name] != comparison:
                LOGGER.error(
                    f" Current {dout[field_name]} is different of new one "
                    f"{comparison}. Don't know what to do in this case. "
                )
        return dout

    def update_selection(
        self,
        new_sel: Optional[dict] = None,
        new_slice: Optional[dict] = None,
        new_isel: Optional[dict] = None,
        new_islice: Optional[dict] = None,
    ):
        """
        Updates the selection for all events.

        Args:
            new_sel: Selection dictionary.
            new_slice: Slice dictionary.
            new_isel: isel dictionary.
            new_islice: islice dictionary.
        """
        if new_sel is None:
            new_sel = {}
        if new_slice is None:
            new_slice = {}
        if new_isel is None:
            new_isel = {}
        if new_islice is None:
            new_islice = {}
        for element in self.events:
            element.update_selection(
                new_sel=new_sel,
                new_slice=new_slice,
                new_isel=new_isel,
                new_islice=new_islice,
            )

    @property
    def grid_name(self) -> str:
        """
        Returns the grid name.

        Returns:
            str: Grid name.
        """
        return self.events[0].field.grid_name

    @property
    def geos_file(self) -> Path:
        """
        Returns the geos file.

        Returns:
            Path: Geos file.
        """
        return self.events[0].geos.file

    @property
    def geos_descriptive(self) -> xr.DataArray:
        """
        Returns the descriptive geos.

        Returns:
            xr.DataArray: Descriptive geos.
        """
        return MaskLoader(filename=self.geos_file, grid_name=self.grid_name).load(
            ids=self.localisation.geos_descriptive
        )

    def compute(self) -> xr.Dataset:
        """
        Computes the risk for a level by combining different events. The output
        dataset is not generated here, only the risk is calculated.

        Returns:
            xr.Dataset: Output dataset containing the computed risk.
        """
        output_ds = xr.Dataset()
        mask = self.mask.f32

        # Computing all events and retrieving results for output
        events = []
        for i, event in enumerate(self.events):
            events.append(event.compute())
            tmp_ds = event.values_ds.expand_dims(dim="evt").assign_coords(evt=[i])
            output_ds = xr.merge([output_ds, tmp_ds])

        # Combining all events using logical operators
        risk_da = LogicalOperator.apply(self.logical_op_list, events)
        self._spatial_risk_da = risk_da * mask

        # Aggregating if necessary
        if self.aggregation is not None:
            output_ds["threshold_dr"] = self.aggregation.kwargs.get("dr")

            # Adding to have the combined event density as output
            agg_handler = Aggregator(self._spatial_risk_da)
            output_ds["risk_density"] = agg_handler.compute(
                Aggregation(method=AggregationMethod.DENSITY)
            )
            output_ds["risk_density"].attrs = {}

            # Adding to have the combined event summarized density as output
            agg_handler_time = Aggregator(risk_da, aggregate_dim="valid_time")
            max_risk_da = (
                agg_handler_time.compute(Aggregation(method=AggregationMethod.MAX))
                * mask
            )
            agg_handler_space = Aggregator(max_risk_da)
            output_ds["risk_summarized_density"] = agg_handler_space.compute(
                Aggregation(method=AggregationMethod.DENSITY)
            )
            output_ds["risk_summarized_density"].attrs = {}

            # Calculating the risk occurrence
            risk_da = agg_handler.compute(self.aggregation)

        output_ds["occurrence"] = risk_da > 0
        output_ds["occurrence"].attrs = {}

        # Clean useless attributes
        self._spatial_risk_da.attrs = {}

        # Checking if the variables are present
        for coord in ("areaName", "areaType"):
            if coord not in output_ds.coords:
                output_ds.coords[coord] = ("id", ["unknown"] * output_ds.id.size)

        return output_ds.squeeze("tmp")

    def reset(self) -> LevelComposite:
        super().reset()
        for event in self.events:
            event.reset()
        return self

    def multiply_all_dr_by(self, mult: float) -> LevelComposite:
        copy = self.make_copy().reset()
        for obj in [copy] + copy.events:
            if obj.aggregation is not None and "dr" in obj.aggregation.kwargs:
                obj.aggregation.kwargs["dr"] *= mult
        return copy
