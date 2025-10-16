from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from pydantic import field_validator

import mfire.utils.mfxarray as xr
from mfire.composite.base import BaseComposite
from mfire.composite.serialized_types import s_path
from mfire.settings import ALT_MAX, ALT_MIN, Settings, get_logger
from mfire.utils.xr import ArrayLoader, MaskLoader

# Logging
LOGGER = get_logger(name="geos.mod", bind="geos")


class GeoComposite(BaseComposite):
    """
    Object containing the configuration of the geometrics for the Promethee production
    task.
    """

    file: s_path
    mask_id: Optional[List[str] | str] = None
    grid_name: Optional[str] = None

    def compute(self) -> xr.DataArray:
        """
        Computes the GeoComposite object by loading mask data from the file.

        Returns:
            xr.DataArray: Computed GeoComposite object.
        """
        return MaskLoader(filename=self.file, grid_name=self.grid_name).load(
            ids=self.mask_id
        )

    @property
    def mask_da(self) -> xr.DataArray:
        return MaskLoader(filename=self.file, grid_name=self.grid_name).load()

    @property
    def all_axis(self) -> xr.DataArray:
        """
        Returns a DataArray containing all axis within the masked DataArray. If no
        axis features are found in `mask_da`, an empty DataArray is returned.

        Returns:
            xr.DataArray: A filtered DataArray containing all axis.
        """
        mask_da = self.mask_da
        return mask_da.where(mask_da.areaType == "Axis", drop=True)

    def all_sub_areas(self, area_id: str) -> List[str]:
        """
        Retrieves a list of ids containing all sub-areas associated with the given area
        identifier.

        Args:
            area_id: The unique identifier for the area of interest.

        Returns:
            List[str]: A list containing the id of the sub-areas.
        """
        all_axis, sub_areas_ids = self.all_axis, []

        for axis_id in all_axis.id.data:
            if axis_id == area_id:
                sub_areas_ids.append(axis_id)
                continue

            size_axis = all_axis.sel(id=axis_id).sum()
            if (
                0.9 * size_axis
                <= (all_axis.sel(id=area_id) * all_axis.sel(id=axis_id)).sum()
                <= 1.1 * size_axis
            ):
                sub_areas_ids.append(axis_id)
        return sub_areas_ids

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """
        Computes the bounds of the GeoComposite object.

        Returns:
            Tuple[float, float, float, float]: Bounds of the GeoComposite object as
                (min_lon, min_lat, max_lon, max_lat).
        """
        mask_da = self.compute()
        return (
            mask_da.longitude.values.min(),
            mask_da.latitude.values.min(),
            mask_da.longitude.values.max(),
            mask_da.latitude.values.max(),
        )


class AltitudeComposite(BaseComposite):
    """
    Object containing the configuration of the altitude of fields for the Promethee
    production task.
    """

    filename: s_path
    alt_min: Optional[int] = ALT_MIN
    alt_max: Optional[int] = ALT_MAX

    @field_validator("alt_min")
    def init_alt_min(cls, v: int) -> int:
        if v is None:
            return ALT_MIN
        return v

    @field_validator("alt_max")
    def init_alt_max(cls, v: int) -> int:
        if v is None:
            return ALT_MAX
        return v

    @field_validator("filename")
    def init_filename(cls, v: Path) -> Path:
        """
        Initializes the filename by converting it to a Path object and checking its
        existence.

        Args:
            v: Input filename.

        Returns:
            Path: Initialized filename as a Path object.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        filename = Path(v)
        if not filename.is_file():
            raise FileNotFoundError(f"No such file {v}.")
        return filename

    def compute(self) -> xr.DataArray:
        """
        Computes and returns the computed field data based on the altitude file and
        altitude restrictions.

        Returns:
            xr.DataArray: Computed field data.
        """
        field_da = ArrayLoader(filename=self.filename).load()
        if self.alt_min is not None:
            field_da = field_da.where(field_da >= self.alt_min)
        if self.alt_max is not None:
            field_da = field_da.where(field_da <= self.alt_max)
        return field_da

    @classmethod
    def from_grid_name(
        cls,
        grid_name: str,
        alt_min: Optional[int] = None,
        alt_max: Optional[int] = None,
    ) -> AltitudeComposite:
        """
        Creates an AltitudeComposite object from the grid name and altitude
        restrictions.

        Args:
            grid_name: Grid name.
            alt_min: Minimum altitude. Defaults to None.
            alt_max: Maximum altitude. Defaults to None.

        Returns:
            AltitudeComposite: Created AltitudeComposite object.
        """
        return cls(
            filename=Path(Settings().altitudes_dirname) / f"{grid_name}.nc",
            alt_min=alt_min,
            alt_max=alt_max,
        )
