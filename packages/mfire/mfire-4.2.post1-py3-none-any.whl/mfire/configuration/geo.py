import re
from functools import cached_property
from typing import Any, List, Optional

import geojson
import shapely
from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo
from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry

from mfire.composite.base import BaseModel, precached_property
from mfire.settings import get_logger
from mfire.utils.hash import MD5

LOGGER = get_logger(name=__name__)


class FeatureConfig(BaseModel):
    id: str
    properties: dict = {}
    geometry: Optional[dict | BaseGeometry]

    @field_validator("geometry")
    def init_geometry(cls, v: Any, info: ValidationInfo) -> Optional[dict]:
        """
        Initializes a geometry object and performs validation checks.

        Args:
            v: The geometry object or dictionary representing GeoJSON data.
            info: Validation info from pydantic.

        Returns:
            A validated geometry object (Geometry type) or None if validation fails.
        """
        if v is None:
            return v

        feat_id = info.data.get("id")
        feat_label = info.data.get("properties", {}).get("label")

        # Handle geometry input format (either Geometry object or GeoJSON dict)
        if not isinstance(v, dict):
            v = mapping(v)

        if not geojson.Feature(geometry=v).is_valid:
            LOGGER.error(
                f"Invalid geometry (id={feat_id}, label={feat_label}). Removed from "
                f"available zones."
            )
            return None

        # Validate geometry shape and GeoJSON representation
        shape = shapely.geometry.shape(v)
        if not shape.is_valid:
            LOGGER.error(
                f"Invalid geometry shape (id={feat_id}, label={feat_label}). Removed "
                "from available zones."
            )
            return None

        # Extract and validate longitude/latitude bounds
        lon0, lat0, lon1, lat1 = shape.bounds
        lon_lat_valid = (
            -180 <= lon0 <= 180
            and -180 <= lon1 <= 180
            and -90 <= lat0 <= 90
            and -90 <= lat1 <= 90
        )
        if not lon_lat_valid:
            LOGGER.error(
                f"Longitude/Latitude error for (id={feat_id}, label={feat_label}): "
                f"{(lon0, lat0, lon1, lat1)}. Valid ranges: longitude [-180, 180], "
                f"latitude [-90, 90]."
            )
            return None

        # Return the validated geometry
        return v

    @field_validator("properties")
    def init_name_property_from_label(cls, v: dict) -> dict:
        """
        Initializes the "name" property in a dictionary if it's missing and sets it
        based on the "label" property.

        Args:
            v: A dictionary containing feature properties.

        Returns:
            The modified dictionary with the "name" property set (if necessary).
        """
        if "name" not in v and "label" in v:
            v["name"] = (
                search.group(1).strip("()")
                if (search := re.search(r"^.*_\((.*)$", v["label"]))
                else v["label"]
            )  # Set "name" from "label" and extract name using regex
        return v

    @precached_property
    def shape(self) -> Optional[BaseGeometry]:
        return shapely.geometry.shape(self.geometry) if self.geometry else None


class FeatureCollection(BaseModel):
    features: List[FeatureConfig]

    @property
    def hash(self) -> str:
        return MD5(self.model_dump()).hash

    @field_validator("features")
    def init_features(cls, v: []) -> List[FeatureConfig]:
        return [feat for feat in v if feat.geometry is not None]

    @cached_property
    def centroid(self):
        return self.features[0].shape.centroid
