from __future__ import annotations

import re
from functools import cached_property
from pathlib import Path
from typing import ClassVar, Dict, List, Literal, Optional

import numpy as np
from pydantic import model_validator
from shapely import STRtree, box
from shapely.geometry import shape

from mfire.composite.base import BaseComposite
from mfire.composite.operator import ComparisonOperator
from mfire.mask.cardinal_mask import CardinalMasks
from mfire.settings import Settings, get_logger
from mfire.utils import MD5
from mfire.utils import mfxarray as xr
from mfire.utils.xr import ArrayLoader, from_0_360_to_center, from_center_to_0_360

# Logging
LOGGER = get_logger(name="mask_processor", bind="mask")


class Processor(BaseComposite):
    """
    Class to create geographical masks on data arrays.

    Attributes:
        config: Configuration dictionary for the production, containing
            at least the key 'geos'.

    """

    config: dict
    _shared_config: dict = {}

    @model_validator(mode="after")
    def init_shared_config(self) -> Processor:
        self.shared_config["language"] = self.config["config_language"]
        return self

    @property
    def merged_ds(self) -> xr.Dataset:
        """
        Returns a merged xr.Dataset containing masks for each grid name.

        This property iterates through the configured grid names, processes masks
        for each grid using a GridProcessor object, and merges the resulting DataArrays
        into a single xr.Dataset. Finally, it converts all mask variables to boolean
        data type for efficiency.

        Returns:
            xr.Dataset: The merged dataset containing masks for each grid.
        """

        # List to store processed DataArrays from each grid
        datasets = []

        # Get configured grid names from the Settings class
        grid_names = Settings().grid_names()

        # Process masks for each grid and append DataArrays
        for grid_name in grid_names:
            grid_ds = GridProcessor(
                parent=self,
                features=self.config["geos"]["features"],
                grid_name=grid_name,
            ).compute()
            if grid_ds is not None:
                datasets.append(grid_ds)

        # Merge all processed DataArrays into a single Dataset
        merged_ds = xr.merge(datasets)

        # Convert all mask variables to boolean type for efficiency
        for grid_name in grid_names:
            if grid_name in merged_ds.data_vars:
                merged_ds[grid_name] = merged_ds[grid_name].mask.bool

        return merged_ds

    def compute(self):
        """
        Computes and saves merged masks to a NetCDF file.

        This function first checks for the presence of an "output file" key in the
        data dictionary. It then retrieves the merged masks using the `merged_ds`
        property. The MD5 hash of the masks is added to the NetCDF attributes.
        Finally, the merged masks are written to a NetCDF file specified by the
        "output file" key.

        Raises:
            ValueError: If the data dictionary does not contain an "output file" key.
        """

        if "file" not in self.config:
            raise ValueError(
                'Data dictionary must include a "file" key specifying the output '
                "filename."
            )

        gridded_masks_ds = self.merged_ds  # Consider a more descriptive name

        # Add the md5sum of the masks to the netcdf attributes
        md5sum = self.config.get("mask_hash") or MD5(self.config["geos"]).hash
        gridded_masks_ds.attrs["md5sum"] = md5sum

        # Write the netcdf file to disk
        output_path = Path(self.config["file"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        gridded_masks_ds.to_netcdf(output_path)


class GridProcessor(BaseComposite):
    """
    Draw geometry from json to image as mask
    """

    features: List[dict]
    grid_name: str

    areas: Dict[str, dict] = {}

    PERCENT: ClassVar[int] = 1
    MIN_ALT: ClassVar[list] = [200, 300, 400, 500]
    MAX_ALT: ClassVar[list] = [
        300,
        400,
        500,
        600,
        700,
        800,
        900,
        1000,
        1200,
        1400,
        1600,
        1800,
        2000,
        2300,
        2600,
        2900,
        3200,
        3500,
    ]

    @model_validator(mode="after")
    def init_areas(self):
        """
        Processes area features and populates the `areas` dictionary.

        This function iterates through the `features` list within the model and
        populates the `areas` dictionary with information about each area and its
        corresponding compass areas (if applicable).
        """
        for area in self.features:
            area_id = area["id"]
            properties = area["properties"]

            self.areas[area_id] = {
                "name": self.area_name(properties),
                "alt_name": self.alt_area_name(properties),
                "type": (
                    "Axis" if properties.get("is_axe") else properties.get("type", "")
                ),
                "shape": shape(area["geometry"]),
            }

            if not properties.get("is_axe"):
                continue

            for area_compass in CardinalMasks(
                self.areas[area_id]["shape"], area_id=f"{area_id}_compass_"
            ).all_masks["features"]:
                compass_properties = area_compass["properties"]
                self.areas[area_compass["id"]] = {
                    "name": self.area_name(compass_properties),
                    "alt_name": self.alt_area_name(compass_properties),
                    "type": "compass",
                    "shape": shape(area_compass["geometry"]),
                }

    @staticmethod
    def area_name(properties: dict) -> str:
        """Extracts the area name from a dictionary of properties.

        Searches for the area name in the provided `properties` dictionary using a
        predefined order of keys. Returns the first valid area name found, or raises a
        `ValueError` if no name is found.

        Args:
            properties: A dictionary containing potential keys for the area name.
                - "name" (preferred)
                - "label"
                - "alt_label" (alternative label)
                - "areaName" (explicit area name)
                - "area_name" (alternative explicit area name)

        Returns:
            str: The extracted area name.

        Raises:
            ValueError: If no valid area name is found in the `properties` dictionary.
        """
        for key in ("name", "label", "alt_label", "areaName", "area_name"):
            if area_name := properties.get(key):
                return area_name
        raise ValueError("Area name not found in properties dictionary")

    def alt_area_name(self, properties: dict) -> str:
        """
        Extracts the alternative area name from the properties' dictionary.

        This function searches for the "alt_label" property in the provided
        `properties` dictionary. If found, it attempts to extract the text within
        parentheses using a regular expression. If successful, the extracted text
        is returned as the alternative area name. Otherwise, a default string
        (assumed to be translated using `_` function) is returned.

        Args:
            properties: Dictionary containing area properties.

        Returns:
            str: The alternative area name (if found) or a default string.
        """
        if alt_label := properties.get("extra_fields", {}).get(
            f"field_inter_{self.language}"
        ):
            return alt_label

        if alt_label := properties.get("alt_label"):
            # Extract text within parentheses using regular expression
            search_result = re.search(r"^.*_\((.*)\)$", alt_label)
            if search_result:
                return search_result.group(1)

        # Return default string if extraction fails or "alt_label" is not found
        return self._("sur la zone")

    @cached_property
    def grid_da(self) -> xr.DataArray:
        """
        Loads and returns the grid data as an xr.DataArray.

        Returns:
            xr.DataArray: The loaded grid data as an xr.DataArray.
        """

        return ArrayLoader.load_altitude(self.grid_name)

    @cached_property
    def centered_grid_da(self) -> xr.DataArray:
        """
        Returns the grid data centered around the prime meridian (0 degrees longitude)
        if necessary.

        This cached property checks if the maximum longitude value in the `grid_da`
        exceeds 180 degrees. If so, it applies the `from_0_360_to_center` function
        (assumed to be defined elsewhere) to center the longitude values around
        the prime meridian. Otherwise, it simply returns the original `grid_da`.

        Returns:
            xr.DataArray: The grid data centered around 0 degrees longitude (if needed)
                        or the original data.
        """
        return (
            from_0_360_to_center(self.grid_da)
            if self.grid_da.longitude.max() > 180
            else self.grid_da
        )

    @cached_property
    def lon_step(self) -> float:
        """
        Calculates and returns the longitudinal grid spacing.

        Returns:
            float: The longitudinal grid spacing of the data in degrees.
        """
        return (self.grid_da.longitude[1] - self.grid_da.longitude[0]).item()

    @cached_property
    def lat_step(self) -> float:
        """
        Calculates and returns the latitudinal grid spacing.

        Returns:
            float: The latitudinal grid spacing of the data in degrees.
        """

        return (self.grid_da.latitude[1] - self.grid_da.latitude[0]).item()

    @cached_property
    def bounds(self) -> tuple[float, float, float, float]:
        """
        Calculates and returns the global bounding box encompassing all areas.

        This cached property iterates through the shapes of all areas in the `areas`
        dictionary. It initializes global minimum and maximum values for longitude
        (X) and latitude (Y) boundaries. For each shape, it updates these values to
        encompass the entire set of shapes. The final result is a tuple containing
        the minimum and maximum values for longitude and latitude, representing
        the global bounding box.

        Returns:
            tuple[float, float, float, float]: The global bounding box (xmin, ymin,
                                                xmax, ymax).
        """

        xmin_global, ymin_global = float("inf"), float("inf")
        xmax_global, ymax_global = float("-inf"), float("-inf")

        for area in self.areas.values():
            xmin, ymin, xmax, ymax = area["shape"].bounds

            # Update global bounds to encompass all shapes
            xmin_global = min(xmin_global, xmin)
            ymin_global = min(ymin_global, ymin)
            xmax_global = max(xmax_global, xmax)
            ymax_global = max(ymax_global, ymax)

        return xmin_global, ymin_global, xmax_global, ymax_global

    @cached_property
    def subgrid(self) -> xr.DataArray:
        """
        Extracts a subgrid from the centered grid data encompassing all areas.

        Returns:
            xr.DataArray: The subgrid data encompassing all areas.
        """

        bounding_box = self.bounds
        min_x, min_y, max_x, max_y = bounding_box

        # Calculate half the grid step size for buffer around bounding box
        lon_diff = self.lon_step / 2
        lat_diff = self.lat_step / 2

        # Select a subgrid from the centered grid data
        return self.centered_grid_da.sel(
            latitude=slice(max_y - lat_diff, min_y + lat_diff),
            longitude=slice(min_x - lon_diff, max_x + lon_diff),
        )

    @cached_property
    def offset_lon(self) -> int:
        """
        Calculates the integer offset of the subgrid longitude relative to the centered
        grid.

        Returns:
            int: The integer offset of the subgrid longitude (number of grid points).
        """

        lon_diff = (
            self.subgrid.longitude[0].item() - self.centered_grid_da.longitude[0].item()
        )
        return int(round(lon_diff / self.lon_step))

    @cached_property
    def offset_lat(self) -> int:
        """
        Calculates the integer offset of the subgrid latitude relative to the centered
        grid.

        Returns:
            int: The integer offset of the subgrid latitude (number of grid points).
        """
        return round(
            (self.subgrid.latitude[0] - self.centered_grid_da.latitude[0]).item()
            / self.lat_step
        )

    @cached_property
    def str_tree(self) -> STRtree:
        """
        Creates and returns a spatial index (STRtree) for the subgrid data.

        Returns:
            STRtree: The spatial index for the subgrid data.
        """

        lon_diff = self.lon_step / 2
        lat_diff = self.lat_step / 2

        # Extract longitude and latitude values for meshgrid
        lons, lats = np.meshgrid(
            self.subgrid.longitude.values, self.subgrid.latitude.values
        )

        # Create bounding boxes for each grid cell with a half-step buffer
        grid_boxes = [
            box(lon - lon_diff, lat + lat_diff, lon + lon_diff, lat - lat_diff)
            for lon, lat in zip(lons.ravel(), lats.ravel())
        ]

        return STRtree(grid_boxes)

    @cached_property
    def array(self) -> np.ndarray:
        """
        Creates a boolean mask array indicating areas intersecting the subgrid.

        Returns:
            np.ndarray: A boolean mask array with True indicating intersection with an
                        area.
        """

        # Query the STRtree for intersections with area shapes
        intersection_results = self.str_tree.query(
            [area["shape"] for area in self.areas.values()], predicate="intersects"
        )

        # Unpack intersection indices and offsets
        area_indices, intersection_offsets = intersection_results

        # Calculate offsets in latitude and longitude directions
        lats, lons = np.divmod(intersection_offsets, self.subgrid.longitude.size)

        # Create boolean mask array with broadcasting
        array_shape = (
            len(self.areas),
            self.grid_da.latitude.size,
            self.grid_da.longitude.size,
        )
        array = np.zeros(array_shape, dtype=bool)
        array[area_indices, self.offset_lat + lats, self.offset_lon + lons] = True

        return array

    def compute(self) -> Optional[xr.Dataset]:
        """
        Computes a new DataArray containing only valid data points and
        associated area information from the original data.

        Returns:
            xr.Dataset: A new dataset containing the filtered data and area information.
        """
        if self.subgrid.size == 0:
            return None

        # Find indices of valid data points along latitude and longitude axes
        valid_lons = np.nonzero(np.any(self.array, axis=(0, 1)))[0]
        valid_lats = np.nonzero(np.any(self.array, axis=(0, 2)))[0]

        # Create a new DataArray with zeros and select valid data points
        da = (
            xr.zeros_like(self.centered_grid_da)
            .isel(longitude=valid_lons, latitude=valid_lats)
            .expand_dims({"id": self.areas.keys()})
        )
        da.data = self.array.take(valid_lats, axis=1).take(valid_lons, axis=2)

        # Extract area information from the areas dictionary
        names, alt_names, types = [], [], []
        for area in self.areas.values():
            names.append(area["name"])
            alt_names.append(area["alt_name"])
            types.append(area["type"])

        # Add area information as coordinates in the DataArray
        da["areaName"] = (["id"], names)
        da["altAreaName"] = (["id"], alt_names)
        da["areaType"] = (["id"], types)

        # Handle data exceeding 180 degrees longitude
        if self.grid_da.longitude.max() > 180:
            da = from_center_to_0_360(da)

        # Rename latitude and longitude axes with grid name
        da = self._compute_axis_altitude(da).rename(
            {
                "latitude": f"latitude_{self.grid_name}",
                "longitude": f"longitude_{self.grid_name}",
            }
        )

        # Create a Dataset and reset coordinates to avoid dimension errors
        return xr.Dataset(
            {da.name: da}, coords={x: da[x].values for x in da.dims}
        ).reset_coords(["areaName", "altAreaName", "areaType"])

    def _compute_axis_altitude(self, data_array: xr.DataArray) -> xr.DataArray:
        """
        Computes altitude information for specific areas in the DataArray.

        Args:
            data_array: The original DataArray containing the data.

        Returns:
            xr.DataArray: The modified DataArray with additional altitude information.
        """

        temp_da = []  # List to store temporary DataArrays for altitude regions

        # Load altitude data corresponding to the grid
        altitude_da = ArrayLoader.load_altitude(self.grid_name).sel(
            longitude=data_array.longitude, latitude=data_array.latitude
        )

        # Loop through areas and identify "Axis" type
        for area_id, area_info in self.areas.items():
            if area_info["type"] != "Axis":
                continue

            # Extract data for the current area
            area_da = data_array.sel(id=area_id).mask.f32
            area_alt_da = area_da * altitude_da

            # Calculate minimum, maximum altitude, and total data points
            min_alt = area_alt_da.min().values
            max_alt = area_alt_da.max().values

            # Loop through minimum altitude thresholds
            for altitude in [alt for alt in self.MIN_ALT if min_alt <= alt <= max_alt]:
                if (
                    data := self._compute_axis_altitude_for_alt(
                        area_da, area_alt_da, altitude, above_or_below="below"
                    )
                ) is not None:
                    temp_da.append(data)

            # Similar loop for maximum altitude thresholds (above)
            for altitude in [alt for alt in self.MAX_ALT if min_alt <= alt <= max_alt]:
                if (
                    data := self._compute_axis_altitude_for_alt(
                        area_da, area_alt_da, altitude, above_or_below="above"
                    )
                ) is not None:
                    temp_da.append(data)

        # Concatenate the original data with altitude regions (if any)
        return xr.concat([data_array] + temp_da, dim="id") if temp_da else data_array

    def _compute_axis_altitude_for_alt(
        self,
        area_da: xr.DataArray,
        area_alt_da: xr.DataArray,
        altitude: int,
        above_or_below: Literal["above", "below"],
    ) -> Optional[xr.DataArray]:
        comp_op = (
            ComparisonOperator.SUP
            if above_or_below == "above"
            else ComparisonOperator.INF
        )
        data = comp_op(area_alt_da, altitude).mask.f32
        proportion = data.sum().data / area_da.sum().data
        if proportion < self.PERCENT / 100 or proportion > 1 - self.PERCENT / 100:
            return None

        data = data.expand_dims(dim="id").assign_coords(
            id=[
                f"{area_da.id.item()}"
                f"_alt__{'sup' if above_or_below == 'above' else 'inf'}"
                f"_{altitude}"
            ]
        )
        data["areaType"] = (["id"], ["Altitude"])

        if above_or_below == "above":
            name = self._("au-dessus de {altitude} m")
        else:
            name = self._("en dessous de {altitude} m")
        data["areaName"] = data["altAreaName"] = (
            ["id"],
            [name.format(altitude=altitude)],
        )

        return data
