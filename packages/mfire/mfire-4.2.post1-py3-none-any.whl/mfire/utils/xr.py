from __future__ import annotations

import functools
from typing import Any, Callable, List, Literal, Optional

import numpy as np

import mfire.utils.mfxarray as xr
from mfire.composite.base import BaseModel
from mfire.composite.serialized_types import s_path
from mfire.settings import Settings, get_logger
from mfire.utils.exception import LoaderError
from mfire.utils.selection import Selection
from mfire.utils.unit_converter import unit_conversion

xr.set_options(keep_attrs=True)

# Logging
LOGGER = get_logger(name="utils", bind="xr")


def rounding(val: xr.DataArray | xr.Dataset) -> xr.DataArray | xr.Dataset:
    """
    Perform the rounding of latitude/longitude.

    Args:
        val: DataArray or Dataset to round.

    Returns:
        Rounded DataArray of Dataset
    """
    for var in ("latitude", "longitude"):
        if hasattr(val, var):
            val[var] = val[var].round(5)
    return val


def da_set_up(da: xr.DataArray, axis: xr.DataArray | xr.Dataset) -> xr.DataArray:
    """
    Ensure that there are no 'holes' in the DataArray by comparing it to the data
    array or set of axis. It assumes that both the DataArray and data array or set
    exist in the same spatial domain.

    Args:
        da: The main DataArray.
        axis: The data array of axis.

    Returns:
        xr.DataArray: The mask with consistent spatial boundaries as the data array.
    """

    # Determine the latitude boundaries
    lat_bounds = (axis.latitude.values.min(), axis.latitude.values.max())
    index_lat_field = (da.latitude >= lat_bounds[0]) & (da.latitude <= lat_bounds[1])

    # Determine the longitude boundaries
    lon_bounds = (axis.longitude.values.min(), axis.longitude.values.max())
    index_lon_field = (da.longitude >= lon_bounds[0]) & (da.longitude <= lon_bounds[1])

    # Create a new mask with consistent spatial boundaries
    return da.where(index_lat_field & index_lon_field, drop=True)


def loader_error_decorator(func: Callable) -> Callable:
    """
    Decorator function that handles loader errors.

    Args:
        func: The function to be decorated.

    Returns:
        The decorated function.
    """

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> xr.DataArray:
        """
        Wrapper function that handles loader errors.

        Args:
            self: The instance of the class.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The data of the decorated function.

        Raises:
            LoaderError: If an error occurs during loading or dumping.
        """
        try:
            return func(self, *args, **kwargs)
        except Exception as excpt:
            raise LoaderError(
                f"{self!r}.{func.__name__}(*{args}, **{kwargs}): failed."
            ) from excpt

    return wrapper


class Loader(BaseModel):
    """Class representing a loader."""

    filename: s_path

    def _file_exists_or_raise(self):
        if self.filename.is_file() is False:
            raise FileNotFoundError(f"{self.filename} not found")

    @loader_error_decorator
    def load(self) -> xr.Dataset:
        """
        Load the dataset from the file.

        Returns:
            The loaded dataset
        """
        # Check if self.filename exists
        self._file_exists_or_raise()

        with xr.open_dataset(self.filename) as tmp_ds:
            ds = tmp_ds.load()
        return rounding(ds)

    @loader_error_decorator
    def dump(self, data: xr.Dataset) -> bool:
        """
        Dump the dataset to the file.

        Args:
            data: The dataset to be dumped.

        Returns:
            A boolean indicating if the dump was successful.
        """
        if self.filename.is_file():
            LOGGER.warning(
                f"{self.__class__.__name__} : Dumping to existing {self.filename}."
            )
        data.to_netcdf(self.filename)
        return self.filename.is_file()


class ArrayLoader(Loader):
    """Specific loader for opening NetCDF DataArray."""

    @loader_error_decorator
    def load(
        self, var_name: Optional[str] = None, selection: Selection = None
    ) -> xr.DataArray:
        """Load a DataArray

        Args:
            var_name: Variable to retrieve from the Dataset. If None given, it opens and
                loads the file as a DataArray, which can cause errors if the Dataset has
                multiple variables. Defaults to None
            selection: Selection object t consider.

        Returns:
            Loaded DataArray
        """
        # Check if self.filename exists
        self._file_exists_or_raise()

        if var_name:
            with xr.open_dataset(self.filename) as tmp_ds:
                dr = tmp_ds[var_name]
        else:
            with xr.open_dataarray(self.filename) as tmp_da:
                dr = tmp_da
        if selection:
            dr = selection.select(dr)
        da = dr.load()
        if da.dtype == "float64":
            da = da.astype("float32", copy=False)

        if getattr(da, "units", None) == "w1":
            da = unit_conversion(da, "wwmf")

        return rounding(da)

    @staticmethod
    def load_altitude(grid_name: str) -> xr.DataArray:
        return ArrayLoader(
            filename=Settings().altitudes_dirname / f"{grid_name}.nc"
        ).load()


class MaskLoader(Loader):
    """Specific loader for opening NetCDF DataArray as masks"""

    grid_name: Optional[str] = None

    @loader_error_decorator
    def load(self, ids: List[str] | str = None) -> xr.DataArray:
        """Load a xr.DataArray as a mask

        Args:
            ids: List of ids to select. All ids are selected if None. Defaults to None.

        Returns:
            Mask DataArray
        """
        # Check if self.filename exists
        self._file_exists_or_raise()

        if self.grid_name:
            with xr.open_dataset(self.filename) as tmp_ds:
                mask_da = tmp_ds[self.grid_name].load()
                mask_da["areaName"] = tmp_ds.get(
                    "areaName", (["id"], ["unknown"] * tmp_ds.id.size)
                )
                mask_da["altAreaName"] = tmp_ds.get(
                    "altAreaName", (["id"], ["unknown"] * tmp_ds.id.size)
                )
                mask_da["areaType"] = tmp_ds.get(
                    "areaType", (["id"], ["unknown"] * tmp_ds.id.size)
                )
        else:
            with xr.open_dataarray(self.filename) as tmp_da:
                mask_da = tmp_da.load()
        mask_da = mask_da.mask.f32

        # Rename the dimensions to "latitude" and "longitude" (instead of
        # latitude_glob05 e.g.)
        dict_dims = {x: x[:idx] for x in mask_da.dims if (idx := x.find("_")) != -1}
        mask_da = mask_da.rename(dict_dims)

        # Select the masks that we are interested in.
        if ids:
            if isinstance(ids, str):
                ids = {ids}
            else:
                ids = set(ids)

            # Get the set of IDs in the dataset.
            ds_ids = set(mask_da.id.values)

            # Intersect the two sets and select the masks with the intersecting IDs.
            intersection = ids.intersection(ds_ids)
            mask_da = mask_da.sel(id=list(intersection))

        else:
            LOGGER.debug("No selection on mask is performed")

        # Round the mask data array.
        return rounding(mask_da)


#
# Fonction permettant le changement de grilles.
#
def from_0_360_to_center(grid_da: xr.DataArray) -> xr.DataArray:
    """
    Converts a grid from [0:360] to [-180:180].

    Args:
        grid_da: The data array to transform.

    Returns:
        xr.DataArray: The transformed data array.
    """
    longitude = next(x for x in grid_da.dims if "longitude" in x)
    new_da = grid_da.copy()
    new_da[longitude] = ((new_da[longitude] + 180) % 360 - 180).round(5)
    return new_da.sortby(longitude)


def from_center_to_0_360(grid_da: xr.DataArray) -> xr.DataArray:
    """
    Converts a grid from [-180:180] to [0:360].

    Args:
        grid_da: The data array to transform.

    Returns:
        xr.DataArray: The transformed data array.
    """
    longitude = next(x for x in grid_da.dims if "longitude" in x)
    new_da = grid_da.copy()
    new_da[longitude] = (new_da[longitude] % 360).round(5)
    return new_da.sortby(longitude)


def interpolate_to_new_grid(
    da: xr.DataArray,
    grid_name: str,
    method: Literal[
        "linear",
        "nearest",
        "zero",
        "slinear",
        "quadratic",
        "cubic",
        "polynomial",
        "barycentric",
        "krogh",
        "pchip",
        "spline",
        "akima",
    ] = "nearest",
) -> xr.DataArray:
    """
    Performs a grid interpolation within Promethee.

    The results should be treated with caution if high precision is required.

    The input grid name is currently not used but may be utilized in the future
    to handle special cases.

    Args:
        da: The input dataset to interpolate. Its dimensions must include latitude and
            longitude.
        grid_name: The name of the output grid.
        method: Method to apply.

    Returns:
        Interpolated DataArray.
    """
    # Open the file containing the grids
    grid_da = ArrayLoader.load_altitude(grid_name)

    step_lat_new = (grid_da.latitude[1] - grid_da.latitude[0]).data

    start_lat, end_lat = (
        (da.latitude.min().values, da.latitude.max().values)
        if step_lat_new > 0
        else (da.latitude.max().values, da.latitude.min().values)
    )
    slice_lat = slice(start_lat, (end_lat + step_lat_new).round(5))

    step_lon_new = (grid_da.longitude[1] - grid_da.longitude[0]).data

    start_lon, end_lon = (
        (da.longitude.min().values, da.longitude.max().values)
        if step_lon_new > 0
        else (da.longitude.max().values, da.longitude.min().values)
    )

    start_grid = (
        grid_da.longitude.min().values
        if step_lon_new > 0
        else grid_da.longitude.max().values
    )
    if start_lon >= 0 and (end_lon - start_lon) > 350 and start_grid < 0:
        slice_lon = slice(0, 180 - step_lon_new / 2)
        da_est = da.sel(latitude=slice_lat, longitude=slice_lon)
        slice_lon = slice(180, 360)
        da_ouest = da.sel(latitude=slice_lat, longitude=slice_lon)
        da_ouest["longitude"] = da_ouest["longitude"] - 360
        da = xr.concat([da_ouest, da_est], dim="longitude")
    else:
        slice_lon = slice(start_lon, (end_lon + step_lon_new).round(5))
        # Select the subset of the grid based on latitude and longitude slices
        grid_da = grid_da.sel(latitude=slice_lat, longitude=slice_lon)
    return da.interp_like(grid_da, method=method).astype("float32")


# Fonctions gérant les cumuls
def compute_step_size(val: xr.DataArray | xr.Dataset) -> xr.DataArray:
    """
    This function returns the time step (at each point). This time step may vary
    from one step to another. Therefore, we do not rely on the metadata of the file
    to provide this information.

    Args:
        val: DataArray or Dataset on which to calculate the time step.

    Example:
       da.step = 1, 2, 5, 10

    Returns:
        A dataset with "stepsize" as a variable and "var" as a coordinate.
        The step size is expressed in hours (as an integer).
    """

    # We will lose the last occurrence of stepsize via diff
    step_size = (
        val["valid_time"].diff("valid_time", label="lower").dt.seconds / 3600
    ).astype(int)
    step_size.name = "step_size"
    step_size.attrs["units"] = "hours"

    # Add the last occurrence by aligning stepsize with the temporal grid of the input
    # variable. We assume that the last occurrence is identical to the penultimate one.
    step_comp = (
        step_size.broadcast_like(val["valid_time"])
        .shift({"valid_time": 1})
        .isel({"valid_time": -1})
        .expand_dims("valid_time")
    )
    stepout = xr.merge([step_size, step_comp]).fillna(0).astype(int)
    return stepout["step_size"]


def compute_grib_step_size(data_list: List[xr.DataArray | xr.Dataset]) -> xr.DataArray:
    """
    This function returns the GRIB time step (at each point). This time step may vary
    from one step to another. We rely on the metadata of the file to provide this
    information.

    Args:
        data_list: The array on which to calculate the time step.

    Returns:
        A dataset with "stepsize" as a variable. The step size is expressed in hours as
        an integer.
    """
    valid_time = np.concatenate([elt.valid_time.data for elt in data_list], axis=None)
    step_size_data = [
        elt.attrs.get("GRIB_lengthOfTimeRange") or elt.attrs.get("accum_hour")
        for elt in data_list
        if elt.valid_time.data.size > 0
    ]

    return xr.DataArray(
        step_size_data,
        coords={"valid_time": valid_time},
        attrs={"units": "hours"},
        name="step_size",
    )


def disaggregate_sum_values(
    da: xr.DataArray, da_step: xr.DataArray, step_out: int = 1
) -> xr.DataArray:
    """
    Disaggregates and sums values in a DataArray.

    This function performs disaggregation and summing of values in a DataArray.
    It interpolates the values based on the given step sizes and performs
    resampling to the desired output step size.

    Args:
        da: Input DataArray.
        da_step: DataArray providing the step size value for each time step in the input
            array.
        step_out: Output step size in hours. It must be greater than or equal to the
            smallest step size. Defaults to 1.

    Returns:
        DataArray with desaggregated and summed values.
    """
    # Perform desaggregation by dividing the original values by the step size,
    # multiplying by the desired output step size, and performing backfill.
    da_fill = (da / da_step * step_out).resample(valid_time=str(step_out) + "h").bfill()

    # Set attributes for the desaggregated array
    da_fill.attrs["accum_hour"] = step_out
    da_fill.attrs["stepUnits"] = step_out
    da_fill.attrs["history"] = (
        "Disaggregation performed. The assumption was made that filling by the "
        "forward value is needed. The value has been disaggregated by taking the mean."
    )

    return da_fill


def compute_sum_future(
    da: xr.DataArray, da_step: xr.DataArray, step_out: int = 6
) -> xr.DataArray:
    """
    Compute the future sum of a DataArray.

    This function calculates the sum of values in the future. At time t,
    it provides the summed information between t and t+step_out.
    The time steps are determined based on the smallest StepSize.
    For example, if a series has StepSizes between 1H and 6H, the time steps
    will be spaced at 1H intervals.

    Args:
        da: Input DataArray.
        da_step: Time steps provided as input. Defaults to None.
        step_out: Number of hours to sum. Defaults to 6.

    Returns:
        New DataArray with the summed values.
    """

    step_min = da_step.min().item()
    LOGGER.debug("Step sizes:", stepmin=step_min, stepout=step_out, da_step=da_step)

    if step_min != da_step.max().item() or step_min > step_out:
        # In this case, we need to disaggregate before performing the sum
        RR = disaggregate_sum_values(da, da_step, step_out=min(step_min, step_out))
    else:
        RR = da.copy()

    # If we need to cumulate
    if step_out >= step_min:
        n = int(step_out / step_min)
    else:
        # Select only at step_min intervals
        RR = RR.sel(valid_time=da.valid_time)

        # If we disaggregate, we keep all the values.
        n = 1

    LOGGER.debug("Final values", stepout=step_out, n=n, stepmin=step_min)

    # Now we calculate the sum for the next "n" hours.
    nb_step = RR.valid_time.size

    # Start of the series
    rr_cumul_beg = (
        RR.rolling(valid_time=n, min_periods=1)
        .sum()
        .shift(valid_time=-n + 1)
        .isel(valid_time=range(nb_step - n + 1))
    )

    # End of the series
    rr_cumul_end = (
        RR.shift(valid_time=-n + 1)
        .rolling(valid_time=n, min_periods=1)
        .sum()
        .isel(valid_time=range(nb_step - n + 1, nb_step))
    )

    # Reset the correct name for merging purposes.
    rr_cumul_beg.name = da.name
    rr_cumul_end.name = da.name

    # Restore the original attributes.
    # Note: This might be excessive, and some attributes may need filtering
    # (e.g., Grib_StepUnits if present).
    rr_cumul_beg.attrs = RR.attrs
    rr_cumul_end.attrs = RR.attrs

    # Merge the arrays
    dout = xr.merge([rr_cumul_beg, rr_cumul_end])[da.name].astype("float32")
    dout.attrs["accum_hour"] = step_out

    if "GRIB_startStep" in dout.attrs:
        dout.attrs["GRIB_endStep"] = dout.attrs["GRIB_startStep"] + step_out
        dout.attrs["GRIB_stepRange"] = "{}-{}".format(
            dout.attrs["GRIB_startStep"], dout.attrs["GRIB_endStep"]
        )

    return dout


def stepping_data(
    da: xr.DataArray, da_step: xr.DataArray, step_out: int = 6
) -> xr.DataArray:
    """
    Compute the future of a DataArray.

    This function calculates the  values in the future. At time t,
    it provides the  information between t and t+step_out.
    The time steps are determined based on the smallest StepSize.
    For example, if a series has StepSizes between 1H and 6H, the time steps
    will be spaced at 1H intervals.

    Args:
        da: Input DataArray.
        da_step: Time steps provided as input. Defaults to None.
        step_out: Number of hours. Defaults to 6.

    Returns:
        New DataArray with the summed values.
    """

    step_min = da_step.min().item()
    LOGGER.debug("Step sizes:", stepmin=step_min, stepout=step_out, da_step=da_step)

    if step_min != da_step.max().item() or step_min > step_out:
        # In this case, we need to disaggregate
        RR = disaggregate_sum_values(da, da_step, step_out=min(step_min, step_out))
    else:
        RR = da.copy()

    RR.attrs["accum_hour"] = step_out

    return RR


def slice_da(
    da: xr.DataArray,
    start: np.datetime64 = None,
    stop: np.datetime64 = None,
    step: int = 1,
) -> xr.DataArray:
    """
    Slice a given DataArray along a given dimension.

    Args:
        da: DataArray to slice.
        start: Start of the slice, if None the minimum value. Defaults to None.
        stop: Stop of the slice, if None the maximum value. Defaults to None.
        step: Step of the slice. Defaults to 1.

    Returns:
        Sliced DataArray.
    """
    from mfire.utils.date import Datetime

    vals = da["valid_time"].values
    real_start = start if start is not None else np.min(vals)
    real_start = Datetime(real_start).as_np_dt64
    real_stop = stop if stop is not None else np.max(vals)
    real_stop = Datetime(real_stop).as_np_dt64

    # Changing start/stop order if dim's values are reversed
    if len(vals) > 1 and all(vals[i] > vals[i + 1] for i in range(len(vals) - 1)):
        # Changing start/stop order if dim's values are reversed
        real_start, real_stop = real_stop, real_start

    return da.sel({"valid_time": slice(real_start, real_stop, step)})


def extend_da(
    da: xr.DataArray,
    start: np.datetime64 = None,
    stop: np.datetime64 = None,
    step: int = 1,
    freq_base: str = "h",
) -> xr.DataArray:
    """
    Extend a given DataArray to a new start, stop, and step without filling new steps.

    Args:
        da: DataArray to extend.
        start: New start datetime. Defaults to None.
        stop: New stop datetime. Defaults to None.
        step: New step. Defaults to 1
        freq_base: Frequency base to choose among all pandas's frequency strings
            available here:
            https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html

    Returns:
        New DataArray with extended steps.
    """
    delta = np.timedelta64(step, freq_base).astype("timedelta64[ns]")
    real_start = start if start is not None else np.min(da.valid_time.values)
    real_stop = stop if stop is not None else np.max(da.valid_time.values)
    new_range = np.arange(real_start, real_stop + delta, delta)
    new_range_da = xr.DataArray(
        np.ones(new_range.shape), dims=["valid_time"], coords={"valid_time": new_range}
    )
    return da.broadcast_like(new_range_da)


def fill_da(
    da: xr.DataArray,
    source_steps: List[int],
    target_step: int = 1,
    freq_base: str = "h",
) -> xr.DataArray:
    """
    Fill values in a given DataArray along a given dimension to a target step
    with a filling tolerance based on source steps.

    Args:
        da: DataArray to fill.
        source_steps: List of source file step lengths. Used for
            limiting the filling of values.
        target_step: Target file step length. Defaults to 1.
        freq_base: Frequency base to choose among all pandas's frequency strings
            available here:
            https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html

    Returns:
        New DataArray with filled values.
    """
    if len(source_steps) != len(da.valid_time):
        LOGGER.error(
            "Source steps list and given DataArray must have the same length",
            source_steps_len=len(source_steps),
            da_len=len(da.valid_time),
        )
        return da

    delta = np.timedelta64(1, freq_base)
    new_das = []

    # Extension of each step
    for i, local_stop in enumerate(da.valid_time.values):
        sub_da = da.sel(valid_time=local_stop)
        source_step = source_steps[i] - 1
        local_start = local_stop - source_step * delta
        new_das.append(
            extend_da(
                da=sub_da,
                start=local_start,
                stop=local_stop,
                step=target_step,
                freq_base=freq_base,
            ).bfill(dim="valid_time")
        )

    # Concatenation of the new DataArray
    return xr.DataArray(xr.concat(new_das, dim="valid_time"))


def finest_grid_name(ds: xr.Dataset) -> str:
    """
    Returns the name of the finest resolution longitude grid in the `ds` dataset.

    Args:
        ds: An xarray.Dataset object that contains all latitude and longitude coordinate
            variables.

    Returns:
        The name of the finest resolution longitude grid as a string.
    """
    grid_ref = ""
    grid_points = 0
    for key, val in ds.coords.items():
        if str(key).startswith("longitude_") and len(val) > grid_points:
            grid_points = len(val)
            grid_ref = ds[key]
    return str(grid_ref.name)[10:]
