"""
for forecasters' use in another application rthat metronome
"""

import pandas as pd


def run_info(extracteds: dict):
    """
    Extracts and formats run information (subcenter and run time) from all
    parameters within a GRIB data dictionary, suitable for forecasters' use.

    This function iterates through the provided GRIB data dictionary and extracts
    subcenter and run time information for each parameter and step. The run time is
    converted from a numeric format (HMM) to hours (H). The extracted information
    is then formatted into a Pandas DataFrame for easy manipulation and viewing.

    Args:
        extracteds: A dictionary containing information about all GRIB data.
    """
    # Extract subcentre and run time from grib
    infos = {}
    for gribkey, gribinfo in extracteds.items():
        param, _, _, step = gribkey
        data = gribinfo.get("data")
        # Organize run information by parameter and step
        if data is None:
            infos.setdefault(param, {})["run"] = 0
            infos[param].setdefault("step_subCentre", {})[step] = 9999
        else:
            # dataTime is numeric as HMM : we needd only H
            infos.setdefault(param, {})["run"] = data.attrs["GRIB_dataTime"] / 100
            infos[param].setdefault("step_subCentre", {})[step] = data.attrs[
                "GRIB_subCentre"
            ]

    # Collect all unique steps across all parameters
    all_step = {}
    for info in infos.values():
        all_step.update(info["step_subCentre"])
    all_step = dict(sorted(all_step.items(), key=lambda kv: int(kv[0])))
    # Format data for json_normalize and create DataFrame
    params = []
    for param, info in infos.items():
        single_param = {"param": param, "run": info["run"]}
        for step in all_step.keys():
            if step in info["step_subCentre"].keys():
                single_param[step] = int(info["step_subCentre"][step])
            else:
                single_param[step] = None
        params.append(single_param)
    df = pd.json_normalize(params)
    # Save DataFrame to CSV with integer-like formatting
    df.to_csv("run_info.csv", float_format="%.0f")
