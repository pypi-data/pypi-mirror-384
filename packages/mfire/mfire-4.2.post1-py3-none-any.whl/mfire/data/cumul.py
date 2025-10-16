"""
cumul data (as grib define)
from instant data
time integration
duration cumul
export to netcdf

"""

from datetime import timezone
from pathlib import Path
from typing import List

import numpy as np

from mfire.settings import get_logger
from mfire.utils import mfxarray as xr
from mfire.utils import xr as xr_utils
from mfire.utils.date import Timedelta
from mfire.utils.exception import DataPreprocessingError

# Logging
LOGGER = get_logger(name=__name__)


def create_accum_config(preproc_config: dict) -> dict:
    """
    Summarize all info needed to compute accumulation configuration that are : for the
    trio param/step/grid, start and stop time needed.

    Args:
        preproc_config: All preproc files and sources needed.

    Returns:
        All needed info to compute accumulation.
    """
    accum_data = {}
    for file_id, da_group in preproc_config.items():
        # accum param
        if (da_group["postproc"].get("accum", 0) or 0) > 0:
            # create the key from param/step/grid
            data_config = da_group["postproc"]
            grid = data_config["grid"]
            step = data_config["step"]
            key = data_config["param"] + str(step) + grid
            end = data_config["stop"] + Timedelta(hours=data_config["accum"])
            preproc = {
                "file_id": file_id,
                "postproc": da_group["postproc"],
                "filename": da_group["filename"],
            }
            if key in accum_data:
                # update start/stop key value
                accum_data[key]["beginTime"] = min(
                    data_config["start"], accum_data[key]["beginTime"]
                )
                accum_data[key]["endTime"] = max(end, accum_data[key]["endTime"])
                accum_data[key]["files"].update(da_group["files"])
                accum_data[key]["preprocs"].append(preproc)
            else:
                # create start/stop key value
                accum_data[key] = {
                    "param": data_config["param"],
                    "grid": grid,
                    "beginTime": data_config["start"],
                    "endTime": end,
                    "step": step,
                    "files": da_group["files"],
                    "preprocs": [preproc],
                    "downscales": da_group["downscales"],
                }
    return accum_data


def time_step_unicity(gridded_data: List[xr.DataArray]) -> List[xr.DataArray]:
    """
    Remove duplicate time in series and keep the most recent (by GRIB_endStep minimum
    then subCentre maximum) GRIB_endStep is minimal for the most recent model run
    subCentre is increasing from j4j14/j2j3/(most recent j1 update)

    Args:
        gridded_data: List of DataArray to remove duplicate

    Returns:
        Sorted list of DataArray with removed duplicated times.
    """
    time_end_step = {}
    for data in gridded_data:
        valid_time = data.valid_time.item()
        if (
            (valid_time not in time_end_step)
            or data.attrs["GRIB_endStep"] < time_end_step[valid_time]["end"]
            or (
                data.attrs["GRIB_endStep"] == time_end_step[valid_time]["end"]
                and data.attrs["GRIB_subCentre"] > time_end_step[valid_time]["sub"]
            )
        ):
            time_end_step[valid_time] = {
                "end": data.attrs["GRIB_endStep"],
                "sub": data.attrs["GRIB_subCentre"],
            }
    # dictionary in order to update the same valid_time key if duplicate
    gridded_data = {
        data.valid_time.item(): data
        for data in gridded_data
        if time_end_step[data.valid_time.item()]["end"] == data.attrs["GRIB_endStep"]
        and time_end_step[data.valid_time.item()]["sub"] == data.attrs["GRIB_subCentre"]
    }
    return sorted(gridded_data.values(), key=lambda data: data.valid_time.item())


def time_sum(gridded_data: List[xr.DataArray], downscale_time: xr.DataArray, step: int):
    """
    Normalize series data by time and do cumulative sum.

    Args:
        gridded_data: List of data info.
        downscale_time: Downscale time data array.
        step: Expected step between 2 successive data.

    Returns:
        Data array of cumulative data along time step
    """
    # order and add intermediate time as needed
    for data in gridded_data:
        if data.valid_time.size == 0:
            LOGGER.warning(f"No valid time {data}")
    if len(gridded_data) > 0:
        steps = xr_utils.compute_grib_step_size(gridded_data)
        gridded_data = time_step_unicity(gridded_data)
        gridded_data = xr.concat(gridded_data, dim="valid_time")
        if downscale_time is not None:
            steps = xr.concat(
                [steps, xr_utils.compute_grib_step_size(downscale_time)],
                dim="valid_time",
            )
            gridded_data = xr.concat([gridded_data, downscale_time], dim="valid_time")
    else:
        if downscale_time is not None:
            steps = xr_utils.compute_grib_step_size(downscale_time)
            gridded_data = downscale_time
        else:
            return None
    gridded_data = xr_utils.stepping_data(gridded_data, steps, step)
    # add first 0 data
    initial_date = gridded_data.valid_time.min() - np.timedelta64(step, "h")
    initial_data = gridded_data.sel({"valid_time": gridded_data.valid_time.min()})
    initial_data.data = np.zeros(initial_data.shape)
    initial_data = initial_data.assign_coords(valid_time=initial_date)
    initial_data = initial_data.expand_dims(dim={"valid_time": 1}, axis=0)
    initial_data["valid_time"] = initial_data.valid_time.assign_attrs(
        {"standard_name": "time", "long_name": "time"}
    )
    gridded_data = xr.concat(
        [initial_data, gridded_data], dim="valid_time", combine_attrs="no_conflicts"
    )
    # cumulative sum
    return gridded_data.cumsum(dim=["valid_time"])


def _compute_cumul_loop(datas, instant_data, instant_timemax, gridded_data):
    # filter by time
    if "data" not in instant_data:
        return None

    original_step = int(instant_data["data"].attrs["GRIB_lengthOfTimeRange"])
    limit_time = datas["endTime"].as_np_dt64 + np.timedelta64(original_step, "h")
    timelimit_data = instant_data["data"].where(
        instant_data["data"].valid_time <= limit_time, drop=True
    )
    # No more data available
    if timelimit_data.count() == 0:
        return None

    if instant_data["preproc"]["source_grid"] != datas["grid"]:
        # adjust to same grid
        timelimit_data = xr_utils.interpolate_to_new_grid(timelimit_data, datas["grid"])
    timelimit_data = xr.where(
        timelimit_data is not None, timelimit_data, 0, keep_attrs=True
    )
    gridded_data.append(timelimit_data)

    if instant_timemax is None:
        return timelimit_data.valid_time.data.max() + np.timedelta64(original_step, "h")
    return max(instant_timemax, timelimit_data.valid_time.data.max()) + np.timedelta64(
        original_step, "h"
    )


def compute_cumul(datas: dict, downscaled_data: xr.DataArray) -> List[bool]:
    """
    Parallel action to create time-integrated data of a "parameter" (param/grid/accum)

    Args:
        datas: list of all data to time-integrate (datarray:valid_time,lat,lon)
        downscaled_data: DataArray to compute accumulation

    Returns:
        List of booleans indicating the success or fails of the tasks.

    Raises:
        DataPreprocessingError: raised when the computation failed.
    """
    # prepare and format data
    gridded_data = []
    instant_timemax = None
    for instant_data in datas["files"].values():
        if timemax := _compute_cumul_loop(
            datas, instant_data, instant_timemax, gridded_data
        ):
            instant_timemax = timemax
    if downscaled_data is not None:
        if instant_timemax:
            downscaled_data = downscaled_data.sel(
                valid_time=slice(instant_timemax, datas["endTime"].as_np_dt64)
            )
        if downscaled_data.valid_time.size == 0:
            downscaled_data = None

    if len(gridded_data) == 0 and downscaled_data is None:
        raise DataPreprocessingError("Gridded data empty")
    gridded_data = time_sum(gridded_data, downscaled_data, datas["step"])
    return [
        single_cumul(param_period["filename"], param_period["postproc"], gridded_data)
        for param_period in datas["preprocs"]
    ]


def get_cumul(
    time_integrated_data: xr.DataArray,
    actual_date: np.datetime64,
    step: int,
    period: int,
) -> xr.DataArray:
    """
    From a time-integrated datarray, give the cumul from start time with period by step
    concept : compute integrate[start+period] - integrate[start]

    Args:
        time_integrated_data: dataarray(time,lat,lon) with time integrated data
        actual_date: start time for computation
        step: step of cumul
        period: duration of cumul

    Returns:
        Duration accumulation for one time (at actual_date)
    """
    # redefine start as period begin
    # with the info of instant_data_completed of actual_date
    # and therefore, the real start is before the actual_date
    start = actual_date + np.timedelta64(-step, "h")
    stop = start + np.timedelta64(period, "h")
    stop = min(stop, time_integrated_data.valid_time.data.max())
    # filter the period
    try:
        data_period = time_integrated_data.sel(valid_time=slice(start, stop))
    except Exception as e:
        LOGGER.warning(
            f"out of range {e}"
            f" start {start}"
            f" stop  {stop}"
            f"(min : {time_integrated_data.valid_time.data.min()}"
            f" max : {time_integrated_data.valid_time.data.max()})"
        )
        return None
    # get available start and stop date
    if len(data_period.valid_time.data) == 0:
        return None
    start = data_period.valid_time.data.min()
    stop = data_period.valid_time.data.max()
    if start == stop:
        # only one data available :search for step next time
        # and divide by step as doing in earlier version
        data_period = (
            time_integrated_data.sel(
                valid_time=slice(start, stop + np.timedelta64(step, "h"))
            )
            / step
        )
        # get available start and stop date
        start = data_period.valid_time.data.min()
        stop = data_period.valid_time.data.max()
    data_cumul = data_period.sel(valid_time=stop) - data_period.sel(valid_time=start)
    # add valid_time dimension and attributes
    data_cumul = data_cumul.assign_coords(valid_time=actual_date)
    data_cumul = data_cumul.expand_dims(dim={"valid_time": 1}, axis=0)
    data_cumul["valid_time"] = data_cumul.valid_time.assign_attrs(
        {"standard_name": "time", "long_name": "time"}
    )
    dout = data_cumul
    if "GRIB_startStep" in dout.attrs:
        dout.attrs["GRIB_endStep"] = dout.attrs["GRIB_startStep"] + period
        dout.attrs["GRIB_stepRange"] = (
            f"{dout.attrs['GRIB_startStep']}-{dout.attrs['GRIB_endStep']}"
        )
    data_cumul = dout

    return data_cumul


def single_cumul(
    filename: str, data_config: dict, time_integrated_data: xr.DataArray
) -> bool:
    """
    Retrieves the cumul of a single param for all step given time-integrated data
    and an accum.

    Args:
        filename: final filename for param data
        data_config: store accum,param,step,start,stop
        time_integrated_data: dataarray(time,lat,lon) with time integrated data

    Returns:
        whether backup succeed
    """

    accum = data_config["accum"]
    # find param filename
    param = data_config["param"]
    meteo, _, niveau = param.split("_")
    nomvariable = "__".join(["".join([meteo, str(accum)]), niveau])
    begin = data_config["start"]
    str_utc = begin.replace(tzinfo=timezone.utc).isoformat().split("+")[0]
    end = data_config["stop"]
    all_cumul = [
        get_cumul(
            time_integrated_data,
            np.datetime64(str_utc)
            + np.timedelta64(hour, "h")
            + np.timedelta64(0, "ns"),
            data_config["step"],
            accum,
        )
        for hour in range(
            0, (end - begin).total_hours + data_config["step"], data_config["step"]
        )
    ]
    try:
        all_cumul = xr.concat(
            [cumul for cumul in all_cumul if cumul is not None],
            dim="valid_time",
            combine_attrs="no_conflicts",
        )
        # format attributes
        all_cumul = all_cumul.rename(nomvariable)
        all_cumul = all_cumul.assign_attrs({"accum_hour": accum})
        all_cumul = all_cumul.assign_attrs({"PROMETHEE_z_ref": data_config["grid"]})
        if accum == data_config["step"]:
            if "stepUnits" in all_cumul.attrs:
                del all_cumul.attrs["stepUnits"]
            if "history" in all_cumul.attrs:
                del all_cumul.attrs["history"]
        all_cumul = all_cumul.astype("float32")
        all_cumul.to_netcdf(filename)
        return Path(filename).is_file()
    except Exception as e:
        LOGGER.error(f"{filename} {e}")
        return False
