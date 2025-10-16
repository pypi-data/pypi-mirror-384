from typing import List, Optional

import numpy as np
from pydantic import Field

import mfire.utils.mfxarray as xr
from mfire.composite.base import BaseComposite
from mfire.composite.serialized_types import s_path
from mfire.settings import get_logger
from mfire.utils.selection import Selection
from mfire.utils.unit_converter import unit_conversion
from mfire.utils.xr import ArrayLoader, interpolate_to_new_grid

# Logging
LOGGER = get_logger(name="composite.fields.mod", bind="composite.fields")


class FieldComposite(BaseComposite):
    """
    Object containing the configuration of the fields for the Promethee production task.
    """

    file: List[s_path] | s_path = Field(union_mode="left_to_right")
    selection: Optional[Selection] = Selection()
    grid_name: str
    name: str

    def compute(self) -> xr.DataArray:
        """
        Computes and returns the computed field data based on the file and selection
        criteria.

        Returns:
            Computed field data
        """

        field_da = None

        # we can either have a single file (if all the data for the Period have the same
        # time step)
        # or a list of files (if the data have heterogeneous time steps).
        files = self.file if isinstance(self.file, List) else [self.file]
        for file in files:
            new_field_da = ArrayLoader(filename=file).load(selection=self.selection)

            if field_da is None:
                field_da = new_field_da
            else:
                # first, we make sure all tha data are on the same grid
                # then we remove the dates that are on both DataArrays
                # (we keep the first because it's the one which
                # has not been interpolated : the further in the future we are, the
                # coarser the grid is)
                new_field_da = unit_conversion(new_field_da, field_da.units)
                new_field_da = interpolate_to_new_grid(new_field_da, self.grid_name)
                field_da = xr.DataArray(
                    xr.concat([field_da, new_field_da], dim="valid_time")
                ).drop_duplicates(dim="valid_time", keep="first")

        if field_da is not None:
            LOGGER.debug(
                "Opening Field file",
                filename=self.file,
                da_name=field_da.name,
                da_grid_name=field_da.attrs.get("PROMETHEE_z_ref"),
                shape=field_da.shape,
                dims=field_da.dims,
            )
        return field_da

    def coord(self, coord_name: str) -> np.ndarray:
        """
        Retrieves the coordinate values based on the coordinate name.

        Args:
            coord_name: Name of the coordinate.

        Returns:
            Any: Coordinate values.
        """
        return self.compute().coords[coord_name].data
