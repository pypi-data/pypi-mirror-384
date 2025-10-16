"""
Retrieve information to
extract grib,
export netdf
data used to downscaling
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel as PydanticBaseModel

from mfire.settings import get_logger
from mfire.utils.date import Datetime, Timedelta
from mfire.utils.json import JsonFile

# Logging
LOGGER = get_logger(name=__name__)


class PrepareStack(PydanticBaseModel):
    """
    sources_config : store source information temporarily
    """

    sources_config: Optional[Dict] = None

    def stack(self, configuration_path: Path, **kwargs) -> Tuple[Dict, Dict, Dict]:
        data_config = JsonFile(configuration_path).load()
        self.sources_config = data_config["sources"]
        grib, preproc = self.preproc_stack(data_config["preprocessed"], **kwargs)
        grib_scale, downscale = self.downscale_stack(
            data_config.get("downscaled"), **kwargs
        )
        grib.update(grib_scale)
        return grib, preproc, downscale

    def get_source(
        self, source_config: List, term: str, missing_gribs: List
    ) -> Optional[List[Dict]]:
        # Retrieve grib information
        if term not in source_config:
            LOGGER.error(
                "Inconsistency between term given by preprocessed file "
                "and available source terms"
            )
            return None

        if len(source_config[term]) == 0:
            LOGGER.error("Source file configuration empty.")
            return None

        source_conf = [source for source in source_config[term] if "role" in source][0]
        # checking if the source_conf["local"] grib is missing or empty
        grib_filename = Path(source_conf["local"])
        if grib_filename in missing_gribs:
            # if grib is already labeled as missing
            return None

        if not grib_filename.is_file():
            # if grib is missing and not already labeled as missing
            LOGGER.error("Missing source grib file.", grib_filename=grib_filename)
            missing_gribs.append(grib_filename)
            return None

        if grib_filename.stat().st_size < 200:
            LOGGER.error(
                "Source grib file empty (size = "
                f"{grib_filename.stat().st_size} octets).",
                grib_filename=grib_filename,
            )
            missing_gribs.append(grib_filename)
            return None

        return source_conf

    def source_assign(self, sources, root_param) -> Tuple[Dict, Dict, int]:
        # Retrieve all files grib information
        files = {}
        stack = {}
        global LOGGER
        proceed = 0
        missing_gribs = []

        for source_id, source_info in sources.items():
            for term in source_info["terms"]:
                LOGGER = LOGGER.bind(term=term, source_id=source_id)
                proceed += 1
                source = self.get_source(
                    self.sources_config[source_id], str(term), missing_gribs
                )
                if source is None:
                    continue
                file_id = (root_param, source["block"], source["geometry"], term)
                # store reference to grib in preproc file definition
                files.update(
                    {
                        file_id: {
                            "preproc": {
                                "source_grid": source["geometry"],
                                "source_step": int(source_info["step"]),
                            }
                        }
                    }
                )
                stack.update(
                    {
                        file_id: {
                            "model": source["model"],
                            "param": root_param,
                            "step": source_info["step"],
                            "grib_filename": Path(source["local"]),
                        }
                    }
                )
            # break on first source available
        LOGGER = LOGGER.try_unbind("term", "source_id")
        return files, stack, proceed

    def preproc_stack(
        self, preprocessed_config: dict, errors: dict = None
    ) -> Tuple[Dict, Dict]:
        """
        Builds a kind of "task processing stack"

        Args:
            preprocessed_config: configuration of dat to preprocess
            errors: dictionary of errors

        Returns:
            Tuple containing preprocessing config for a specific file to extract.
        """
        stack = {}
        preproc_stack = {}
        proceed = 0
        global LOGGER
        # Loop on all the preprocessed files configurations to create
        # a 'raw stack', i.ea list of all the preprocessing config dicts
        for preproc_id, preproc_config in preprocessed_config.items():
            LOGGER = LOGGER.bind(preproc=preproc_id)
            preproc_stack[preproc_id] = {}
            preproc_rh = [
                preproc
                for preproc in preproc_config["resource_handler"]
                if "role" in preproc
            ][0]
            preproc_rundate = Datetime(preproc_rh["date"])
            postproc = {
                "step": preproc_rh["step"],
                "start": preproc_rundate + Timedelta(hours=preproc_rh["begintime"]),
                "stop": preproc_rundate + Timedelta(hours=preproc_rh["endtime"]),
                "grid": preproc_rh["geometry"],
            }
            postproc.update(preproc_config["agg"])
            preproc_stack[preproc_id]["postproc"] = postproc
            preproc_filename = Path(preproc_rh["local"])
            preproc_stack[preproc_id]["filename"] = preproc_filename
            preproc_stack[preproc_id]["downscales"] = preproc_config.get("downscales")
            preproc_filename.parent.mkdir(parents=True, exist_ok=True)
            root_param = preproc_config["agg"]["param"]
            preproc_stack[preproc_id]["param"] = root_param
            preproc_stack[preproc_id]["grid"] = preproc_rh["geometry"]
            # Retrieving all useful post-proc information
            (preproc_stack[preproc_id]["files"], stack_source, proceed_source) = (
                self.source_assign(preproc_config["sources"], root_param)
            )
            if (
                "T_AS__HAUTEUR2" == preproc_config["agg"]["param"]
                or "france_jj14" not in preproc_id
            ):
                stack.update(stack_source)
            proceed += proceed_source
        LOGGER = LOGGER.try_unbind("preproc")
        if isinstance(errors, dict) and "count" in errors:
            errors["count"] = errors["count"] + proceed - len(stack)
        return stack, preproc_stack

    def downscale_stack(
        self, downscaled_config: dict, errors: dict = None
    ) -> Tuple[Dict, Optional[Dict]]:
        """
        Builds a kind of task processing stack.

        Args:
            downscaled_config: ...
            errors: Dictionary of errors.

        Returns:
            List of dictionaries. Each dictionary is the downscale config for a specific
            file to extract.
        """
        if not isinstance(downscaled_config, dict):
            return {}, None
        stack = {}
        downscales = {}
        proceed = 0
        global LOGGER
        for downscale_id, downscale_config in downscaled_config.items():
            LOGGER = LOGGER.bind(downscale=downscale_id)
            (files, stack_source, proceed_source) = self.source_assign(
                downscale_config["files"], downscale_config["param"]
            )
            downscales.setdefault(downscale_id, {}).setdefault("files", files)
            downscales[downscale_id]["down_grid"] = downscale_config["down_grid"]
            downscales[downscale_id]["param"] = downscale_config["param"]
            if "france_jj14" not in downscale_id:
                stack.update(stack_source)
            proceed += proceed_source
        LOGGER = LOGGER.try_unbind("downscale")
        if isinstance(errors, dict) and "count" in errors:
            errors["count"] = errors["count"] + proceed - len(stack)
        return stack, downscales
