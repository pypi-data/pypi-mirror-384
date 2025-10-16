from __future__ import annotations

from typing import List, Optional, Tuple

import mfire.utils.mfxarray as xr
from mfire.settings import SPACE_DIM, Dimension, get_logger

__all__ = ["compute_iou"]

# Logging
LOGGER = get_logger(name=__name__)

MIN_IOU_THRESHOLD = 0.2
MARGIN_THRESHOLD = 0.5


def compute_iou(
    left_da: xr.DataArray, right_da: xr.DataArray, dims: Dimension = SPACE_DIM
) -> xr.DataArray:
    """Compute the IoU of two given binary dataarrays along the given dimensions.

    We may interpret the IoU (Intersection over Union) as a similarity score
    between two sets. Considering two sets A and B, an IoU of 1 means they are
    identical, while an IoU of 0 means they are completly disjoint.
    Using dims = ("latitude", "longitude") means that we want to find the most
    similarity between spatial zones.

    For example, this is the most common use case:
    >>> lat = np.arange(10, 0, -1)
    >>> lon = np.arange(-5, 5, 1)
    >>> id0 = ['a', 'b']
    >>> id1 = ['c', 'd', 'e']
    >>> arr0 = np.array(
    ... [[[int(i > k) for i in lon] for j in lat] for k in range(len(id0))]
    ... )
    >>> arr1 = np.array(
    ... [[[int(j > 5 + k) for i in lon] for j in lat] for k in range(len(id1))]
    ... )
    >>> da0 = xr.DataArray(arr0, coords=(("id0", id0), ("lat", lat), ("lon", lon)))
    >>> da1 = xr.DataArray(arr1, coords=(("id1", id1), ("lat", lat), ("lon", lon)))
    >>> da0
    <xarray.DataArray (id0: 2, lat: 10, lon: 12)>
    array([[[...]]])
    Coordinates:
    * id0      (id0) <U1 'a' 'b'
    * lat      (lat) int64 10 9 8 7 6 5 4 3 2 1
    * lon      (lon) int64 -6 -5 -4 -3 -2 -1 0 1 2 3 4 5
    >>> da1
    <xarray.DataArray (id1: 3, lat: 10, lon: 12)>
    array([[[...]]])
    Coordinates:
    * id1      (id1) <U1 'c' 'd' 'e'
    * lat      (lat) int64 10 9 8 7 6 5 4 3 2 1
    * lon      (lon) int64 -6 -5 -4 -3 -2 -1 0 1 2 3 4 5
    >>> compute_iou(da0, da1, dims=("lat", "lon"))
    <xarray.DataArray (id0: 2, id1: 3)>
    array([[0.29411765, 0.25641026, 0.21126761],
        [0.25      , 0.22222222, 0.1875    ]])
    Coordinates:
    * id0      (id0) <U1 'a' 'b'
    * id1      (id1) <U1 'c' 'd' 'e'

    In this example, we created 2 binary dataarrays da0 and da1 containing
    respectively the zones ('a', 'b') and ('c', 'd', 'e'). The IoU returns us a
    table_localisation of the IoUs of all the combinations of the 2 sets of zones.

    make sure entries are of type booleans to be more efficient

    Args:
        left_da: Left dataarray
        right_da: Right DataArray
        dims: Dimensions to apply IoU on. Defaults to SPACE_DIM.

    Returns:
        xr.DataArray: TableLocalisation of the computed IoU along the given dims.
    """
    if left_da.dtype != "bool":
        left_da = left_da.fillna(0).astype("int8").astype("bool")
    if right_da.dtype != "bool":
        right_da = right_da.fillna(0).astype("int8").astype("bool")
    return (left_da * right_da).sum(dims) / (right_da + left_da).sum(dims)


def _iou_retained_ids(
    geos_descriptive: xr.DataArray, phenomenon_map: xr.DataArray
) -> Tuple[List[str], bool]:
    if "id" in phenomenon_map.dims:
        phenomenon_map = phenomenon_map.squeeze("id")

    iou = compute_iou(phenomenon_map, geos_descriptive)
    iou_max = iou.max("id").data
    if iou_max == 0:
        return (None, False)
    # sort geos_descriptive by iou
    iou = iou.sortby(iou, ascending=False)
    gd = geos_descriptive.reindex(indexers={"id": iou.id})
    gd = gd.where(iou >= iou_max * MARGIN_THRESHOLD, drop=True)
    gd = gd.id.data.tolist()
    return (gd, iou_max < MIN_IOU_THRESHOLD)


def _iol_retained_ids(
    geos_descriptive: xr.DataArray,
    phenomenon_map: xr.DataArray,
    threshold_area_proportion: float,
    threshold_phenomenon_proportion: float,
) -> List[str]:
    if phenomenon_map.dtype != "bool":
        phenomenon_map = phenomenon_map.fillna(0).astype("int8").astype("bool")
    if "id" in phenomenon_map.dims:
        phenomenon_map = phenomenon_map.sum("id")
    phenomenon_size = phenomenon_map.sum()

    # we drop the zones which have a proportion of the phenomenon below the threshold
    inter = (geos_descriptive * phenomenon_map).sum(SPACE_DIM)
    geos_prop = inter / geos_descriptive.sum(SPACE_DIM)
    phenomenon_prop = inter / phenomenon_map.sum(SPACE_DIM)
    remainings = geos_descriptive
    criteria = geos_prop.sortby(geos_prop, ascending=False)
    geos_prop = geos_prop.reindex(indexers={"id": criteria.id})
    phenomenon_prop = phenomenon_prop.reindex(indexers={"id": criteria.id})
    remainings = remainings.reindex(indexers={"id": criteria.id})
    remainings = remainings[
        (geos_prop >= threshold_area_proportion)
        & (phenomenon_prop >= threshold_phenomenon_proportion)
    ]

    ids = []
    selected_prop = 0.0
    while remainings.count() > 0 and selected_prop < 0.9:
        map_with_exclusions = remainings
        if ids:
            map_with_exclusions *= geos_descriptive.sel(id=ids).sum("id") == 0
        phenomenon_map_with_exclusions = map_with_exclusions * phenomenon_map

        phenomenon_proportion = phenomenon_map_with_exclusions.sum(
            SPACE_DIM
        ) / map_with_exclusions.sum(SPACE_DIM)
        cond = phenomenon_proportion >= phenomenon_proportion.max() * MARGIN_THRESHOLD
        id_to_take = phenomenon_map_with_exclusions[cond].sum(SPACE_DIM).idxmax().item()
        ids.append(id_to_take)

        sorted_areas = geos_descriptive.sel(id=ids).sum("id") > 0
        selected_prop = (phenomenon_map * sorted_areas).sum() / phenomenon_size

        remainings = remainings.drop_sel(id=id_to_take)
        if remainings.count() > 0:
            inter = (remainings * phenomenon_map * ~sorted_areas).sum(SPACE_DIM)
            geos_prop = inter / remainings.sum(SPACE_DIM)
            phenomenon_prop = inter / phenomenon_map.sum(SPACE_DIM)
            criteria = geos_prop.sortby(geos_prop, ascending=False)
            geos_prop = geos_prop.reindex(indexers={"id": criteria.id})
            phenomenon_prop = phenomenon_prop.reindex(indexers={"id": criteria.id})
            remainings = remainings.reindex(indexers={"id": criteria.id})
            remainings = remainings[
                (geos_prop >= threshold_area_proportion)
                & (phenomenon_prop >= threshold_phenomenon_proportion)
            ]
    return ids


def _clean_inclusions(
    geos_descriptive: xr.DataArray,
    phenomenon_map: xr.DataArray,
    ids: List[str],
    threshold_area_proportion: float,
) -> List[str]:
    if not ids:
        return []

    sorted_areas = geos_descriptive.sel(id=ids)
    sorted_ids = sorted_areas.id
    i = 0
    while i < len(sorted_ids):
        ids_to_exclude = []
        for j in range(i + 1, len(sorted_ids)):
            map_with_exclusions = sorted_areas.isel(id=j) > 0
            map_size = map_with_exclusions.sum(SPACE_DIM)
            for k in range(i + 1):
                map_with_exclusions &= ~sorted_areas.isel(id=k) > 0

            # We exclude the nested location
            geo_prop = (map_with_exclusions & phenomenon_map).sum(SPACE_DIM) / map_size
            if geo_prop < threshold_area_proportion:
                ids_to_exclude.append(j)
        if ids_to_exclude:
            sorted_ids = sorted_ids.drop_isel(id=ids_to_exclude)
        i += 1
    return [id for id in ids if id in sorted_ids.id]  # to avoid unsorted values


def compute_iol(
    geos_descriptive: xr.DataArray,
    phenomenon_map: xr.DataArray,
    threshold_area_proportion: float = 0.25,
    threshold_phenomenon_proportion: float = 0.1,
) -> Tuple[Optional[xr.DataArray], bool]:
    """
    Compute the IoL of two given binary dataarrays along the given dimensions.
    We may interpret the IoL (Intersection over Location) as a similarity score
    between two sets. Make sure entries are of type booleans to be more efficient

    Args:
        geos_descriptive: Containing all geos descriptive with different ids
        phenomenon_map: Map of the phenomenon
        threshold_area_proportion: Minimal proportion of the phenomenon in an area over
            the size of area
        threshold_phenomenon_proportion: Minimal proportion of the phenomenon in an area
            over the size of phenomenon

    Returns:
        Tuple with the best area and a boolean indicating if it's a default area or not.
    """
    if geos_descriptive.id.size == 0:
        return None, False

    if geos_descriptive.dtype != "bool":
        geos_descriptive = geos_descriptive.fillna(0).astype("int8").astype("bool")

    ids = _iol_retained_ids(
        geos_descriptive,
        phenomenon_map,
        threshold_area_proportion,
        threshold_phenomenon_proportion,
    )

    # we delete subareas contained in a selected area
    ids = _clean_inclusions(
        geos_descriptive, phenomenon_map, ids, threshold_area_proportion
    )
    if len(ids) > 0:
        return geos_descriptive.sel(id=ids), False

    LOGGER.warning(f"IoL failed, IoU is used for {phenomenon_map.name}")

    ids, default = _iou_retained_ids(geos_descriptive, phenomenon_map)
    ids = _clean_inclusions(
        geos_descriptive, phenomenon_map, ids, threshold_area_proportion
    )
    return (geos_descriptive.sel(id=ids), default) if len(ids) > 0 else (None, False)


def compute_iou_left(
    left_da: xr.DataArray, right_da: xr.DataArray, dims: Dimension = SPACE_DIM
) -> xr.DataArray:
    """Compute the IoU of two given binary dataarrays along the given dimensions.

    Args:
        left_da: Left dataarray
        right_da: Right DataArray
        dims: Dimensions to apply IoU on. Defaults to SPACE_DIM.

    Returns:
        xr.DataArray: TableLocalisation of the computed IoL along the given dims.
    """
    if left_da.dtype != "bool":
        left_da = left_da.fillna(0).astype("int8").astype("bool")
    if right_da.dtype != "bool":
        right_da = right_da.fillna(0).astype("int8").astype("bool")
    return (left_da * right_da).sum(dims) / (1.0 * left_da.sum(dims))
