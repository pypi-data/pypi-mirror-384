"""Create divisions along cardinal points of a shapefile"""

from typing import Tuple

from geojson import Feature, FeatureCollection
from shapely import affinity
from shapely import geometry as shp_geom
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

from mfire.settings import get_logger

LOGGER = get_logger(name="masks.processor.cardinals", bind="masks.processor")


class CardinalMasks:
    """
    Creates masks according to cardinal directions.
    """

    PERCENT_ONE = 0.5  # Percentage of a zone (N, S, E, O) relative to the whole
    PERCENT_SMALL = 0.35  # Percentage of a "small" zone
    MIN_AREA = 0.1  # Minimum percentage of the initial area to keep a cut
    MAX_AREA = 0.8  # Maximum percentage
    PERCENT_UNICITY = (
        0.85  # Maximum correspondence between two zones (otherwise we keep only one)
    )

    BUFFER_SIZE = 0.01  # Percentage of simplification of the cut (by enlargement)

    def __init__(self, geo: BaseGeometry, area_id: str):
        self.l_result = []  # keep only unique geo (nearby PERCENT_UNICITY)
        self.geo = geo if geo.geom_type == "Polygon" else geo.buffer(self.BUFFER_SIZE)
        self.area_id = area_id
        min_lon, min_lat, max_lon, max_lat = self.geo.bounds
        delta_lat = max_lat - min_lat
        mid_lat = (max_lat + min_lat) / 2
        delta_lon = max_lon - min_lon
        mid_lon = (max_lon + min_lon) / 2

        self.bounding_rect = shp_geom.Polygon(
            [
                (min_lon, min_lat),
                (min_lon, max_lat),
                (max_lon, max_lat),
                (max_lon, min_lat),
            ]
        )
        self.central_square = shp_geom.Polygon(
            [
                (mid_lon, mid_lat + delta_lat / 2 * self.PERCENT_ONE),
                (mid_lon + delta_lon / 2 * self.PERCENT_ONE, mid_lat),
                (mid_lon, mid_lat - delta_lat / 2 * self.PERCENT_ONE),
                (mid_lon - delta_lon / 2 * self.PERCENT_ONE, mid_lat),
            ]
        )

        # nom du découpage associé
        # - aux arguments de transformation scalaire
        #               [x, y, (origin_x, origin_y] ('change_me' = proportions)
        # - au déterminant employé
        self.inputs = {
            "Nord": [(1, "change_me", (min_lon, max_lat)), "le "],
            "Sud": [(1, "change_me", (min_lon, min_lat)), "le "],
            "Est": [("change_me", 1, (max_lon, max_lat)), "l'"],
            "Ouest": [("change_me", 1, (min_lon, max_lat)), "l'"],
            "Sud-Est": [("change_me", "change_me", (max_lon, min_lat)), "le "],
            "Sud-Ouest": [("change_me", "change_me", (min_lon, min_lat)), "le "],
            "Nord-Est": [("change_me", "change_me", (max_lon, max_lat)), "le "],
            "Nord-Ouest": [("change_me", "change_me", (min_lon, max_lat)), "le "],
        }

        # possible utilisation de matrices avec affinity.affine_transform
        # mNorth = [1, 0, 0, x, 0, self.max_lat / 2]
        # mSouth = [1, 0, 0, 0.5, 0, self.min_lat / 2]
        # mEast = [0.5, 0, 0, 1, self.max_lon / 2, 0]
        # mWest = [0.5, 0, 0, 1, self.min_lon / 2, 0]

    def test_area(self, sub: BaseGeometry) -> bool:
        """
        Tests if the new area is "large enough" but "not too large" compared to its
        original area and that the proposed cut does not look too much like one that
        has already been made.

        Args:
            sub: Cut

        Returns:
            True if the new area is valid, False otherwise.
        """
        geo_t = (
            self.geo
            if self.geo.geom_type == "Polygon"
            else self.geo.buffer(self.BUFFER_SIZE)
        )
        sub_t = sub if sub.geom_type == "Polygon" else sub.buffer(self.BUFFER_SIZE)

        if (sub_t.area <= geo_t.area * self.MIN_AREA) or (
            sub_t.area >= geo_t.area * self.MAX_AREA
        ):
            return False

        for other_geo in self.l_result:
            if sub_t.intersects(other_geo):
                inter = sub_t.intersection(other_geo).area
                if (inter / other_geo.union(sub_t).area) > self.PERCENT_UNICITY:
                    return False

        self.l_result.append(sub_t)
        return True

    def get_rect_mask(
        self, lon_scale: float, lat_scale: float, origin: Tuple
    ) -> Polygon:
        """Returns a part of the bounding rectangle

        Args:
            lon_scale: scalar used to multiple longitude values
            lat_scale: scalar used to multiple latitude values
            origin: center point (lon, lat) of the transformation

        Returns:
            Bounding of the transformed rectangle.
        """
        return affinity.scale(self.bounding_rect, lon_scale, lat_scale, origin=origin)

    def make_name(self, card: str) -> str:
        """Create a geo mask descriptive name from templates

        Args:
            card: compact cardinal mask name

        Returns:
            Name fo cardinal mask
        """
        name_template = "dans {}{}"
        if card.startswith("Small"):
            return name_template.format("une petite partie ", card[5:])
        return name_template.format(self.inputs[card][1], card)

    @property
    def all_masks(self) -> FeatureCollection:
        """
        Makes the masks according to cardinal points.

        Returns:
            FeatureCollection of masks according to given cardinal points.
        """
        result = []
        for cardinal_point in [
            "Nord",
            "Sud",
            "Est",
            "Ouest",
            "Sud-Est",
            "Sud-Ouest",
            "Nord-Est",
            "Nord-Ouest",
        ]:
            inpt = self.inputs[cardinal_point]
            for card_name, size in {
                cardinal_point: self.PERCENT_ONE,
                "Small" + cardinal_point: self.PERCENT_SMALL,
            }.items():
                scaling = [x if x != "change_me" else size for x in inpt[0]]
                rect_mask = self.get_rect_mask(*scaling)
                geo_mask = self.geo.intersection(rect_mask)
                if "-" in cardinal_point:
                    # we remove the center for intercardinals
                    geo_mask = geo_mask.difference(self.central_square)
                if self.test_area(geo_mask):
                    geo_buf = geo_mask.buffer(self.BUFFER_SIZE)
                    name = self.make_name(card_name)
                    result.append(
                        Feature(
                            geometry=geo_buf,
                            id=f"{self.area_id}_{card_name}",
                            properties={"name": name},
                        )
                    )
        return FeatureCollection(result)
