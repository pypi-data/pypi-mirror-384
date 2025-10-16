"""
Preprocessing data 'binary' file
Preprocesses raw model data files (grib files) according to a given "data" configuration
"""

from pathlib import Path
from typing import Any, List, Tuple

from pydantic import field_validator

from mfire.composite.base import BaseModel
from mfire.configuration.rules import Rules
from mfire.data.cumul import compute_cumul, create_accum_config
from mfire.data.downscale import DownScale
from mfire.data.grib_reader import load_single_grib_param
from mfire.data.instant import compute_instant
from mfire.data.prepare_stack import PrepareStack
from mfire.data.run_info import run_info
from mfire.settings import RULES_NAMES, get_logger
from mfire.settings.constants import DOWNSCALABLE_PARAMETERS, DOWNSCALE_SOURCE
from mfire.settings.settings import Settings
from mfire.utils import Tasks
from mfire.utils import mfxarray as xr

# Logging
LOGGER = get_logger(name=__name__)


class DataPreprocessor(BaseModel):
    """DataPreprocessor
    Class handling the following data preprocessing according to a given config
    file :
        * parameter extraction from multigrib files
        * concatenation of term by parameter
        * FUTURE : accumulations and combinations of files
        * export to netcdf
    """

    rules: Any

    @field_validator("rules", mode="before")
    def init_rules(cls, v):
        LOGGER.info("Checking rules convention", func="__init__")
        if v not in RULES_NAMES:
            raise ValueError(
                f"Given rules '{v}' not among the available rules: {RULES_NAMES}"
            )

        return Rules(name=v) if isinstance(v, str) else v

    def _preprocess_extract_grib(
        self, configuration_path: Path, tasks: Tasks, **kwargs
    ):
        # Tasks local function to progressively append grib-extracted results to the
        # extracts dictionary.
        def extract_completed(res: Tuple[dict, xr.DataArray]):
            file_id, da = res
            extracts[file_id]["data"] = da

        # Building the preprocessing stack
        extracts, outputs, downscales = PrepareStack().stack(
            configuration_path=configuration_path, **kwargs
        )
        # Extract grib file only once
        for extract_id, extract in extracts.items():
            tasks.append(
                load_single_grib_param,
                task_name=str(extract_id),
                args=(self.rules, extract_id, extract),
                callback=extract_completed,
            )
        tasks.run(name="extract", timeout=Settings().timeout)
        tasks.clean()

        # export run info for forecasters
        run_info(extracts)

        return extracts, outputs, downscales

    def save_downscale_data(self, downscaling, outputs):
        success_resource = 0
        # export downscaled instant data
        for downscaled in downscaling.values():
            # changer la grille proprement ?!
            downscaled["filename"] = Path(
                str(downscaled["filename"]).replace("EURW1S40", "EURW1S100")
            )
            downscaled["data"] = downscaled["data"].astype("float32")
            downscaled["data"].to_netcdf(downscaled["filename"])
            if all(
                (
                    downscaled["filename"].is_file(),
                    downscaled["filename"]
                    in [output["filename"] for output in outputs.values()],
                )
            ):
                success_resource += 1
        return success_resource

    def _preprocess_concat_and_export(self, tasks, outputs, downscales):
        downscalisation = downscales and any(
            DOWNSCALE_SOURCE == output["postproc"]["param"]
            for output in outputs.values()
        )

        # Task local function to progressively sum results to the success_resource
        # dictionary for logging and keep downscaled parameter data
        def instant_completed(res: List):
            success, data, filename, param = res
            # keep parameter downscaled data
            if all(
                (
                    downscalisation,
                    (param in DOWNSCALABLE_PARAMETERS + [DOWNSCALE_SOURCE]),
                    downscale_info["file_filter"] in str(filename),
                )
            ):
                downscaling[param] = {"filename": filename, "data": data}
            success_resource["ok"] += sum(success)

        downscaling = {}
        downscale_info = {"grid": "eurw1s100", "file_filter": "0051_0"}
        for file_id, output in outputs.items():
            if all(
                (
                    (output["postproc"].get("accum", 0) or 0) == 0,
                    "france_jj14" not in file_id or DOWNSCALE_SOURCE in file_id,
                )
            ):
                tasks.append(
                    compute_instant,
                    task_name=file_id,
                    args=(output["filename"], output),
                    callback=instant_completed,
                )
        success_resource = {"ok": 0}
        tasks.run(name="instant", timeout=Settings().timeout)
        tasks.clean()
        if downscalisation:
            downscale = DownScale(
                downscaling=downscaling, grid_name=downscale_info["grid"]
            )
            try:
                downscale.down_scaling_data()
                success_resource["ok"] += self.save_downscale_data(downscaling, outputs)
            except ValueError as ve:
                LOGGER.error(f"{ve}")
                downscalisation = False
        return downscaling, success_resource

    def _preprocess_accumulation_export(
        self, tasks, outputs, downscales, downscaling, success_resource
    ):
        # Task local function to progressively sum results to the success_resource
        # dictionary for logging.
        def cumul_completed(res: List):
            success_resource["ok"] += sum(res)

        accums = create_accum_config(outputs)
        succes_attendu = len(outputs) + 1  # T_AS will be counted 2 times

        # export all cumul data of all raw param
        for name, accum in accums.items():
            if accum["downscales"] is None:
                downscaled_data = None
            else:
                param = downscales[accum["downscales"]]["param"]
                downscaled_data = downscaling.get(param, {}).get("data", None)
            tasks.append(
                compute_cumul,
                task_name=name,
                args=(accum, downscaled_data),
                callback=cumul_completed,
            )
        tasks.run(name="cumul", timeout=Settings().timeout)
        if success_resource["ok"] == succes_attendu:
            LOGGER.info(f"{success_resource['ok']} resources")
        else:
            LOGGER.error(f"{success_resource['ok']}/{succes_attendu} resources")

    def preprocess(self, configuration_path: Path, nproc: int, **kwargs):
        """
        Preprocess all the data config dict in self.data_config.

        Args:
            configuration_path: configuration file path.
            nproc: Number of CPUs to be used in parallel.
            **kwargs: Keyword arguments.
        """

        tasks = Tasks(processes=nproc)
        extracts, outputs, downscales = self._preprocess_extract_grib(
            configuration_path, tasks, **kwargs
        )

        # make data available for output file building
        for extract_id, extract in extracts.items():
            if "data" not in extract:
                continue
            if extract["data"] is None:
                LOGGER.error(f"Extracted grib empty for {extract_id}.")
                continue
            for preproc_config in outputs.values():
                if extract_id in preproc_config["files"]:
                    preproc_config["files"][extract_id].update(
                        {"data": extract["data"]}
                    )

        # Concat and export instant data, keep downscale data
        downscaling, success_resource = self._preprocess_concat_and_export(
            tasks, outputs, downscales
        )
        self._preprocess_accumulation_export(
            tasks, outputs, downscales, downscaling, success_resource
        )
