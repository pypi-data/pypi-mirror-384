import tarfile
from os import cpu_count, getpid
from pathlib import Path
from tarfile import is_tarfile
from typing import Dict, List, Tuple

from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo

from mfire.composite.base import BaseModel, precached_property
from mfire.configuration.production import Production
from mfire.configuration.rules import Rules
from mfire.settings import Settings, get_logger
from mfire.settings.constants import DOWNSCALABLE_PARAMETERS
from mfire.utils import MD5, Tasks
from mfire.utils.date import Datetime, Timedelta
from mfire.utils.json import JsonFile
from mfire.utils.string import split_var_name

# Logging
LOGGER = get_logger(name=__name__)


# Main class : Processor
class Processor(BaseModel):
    """Processor : Parses a configuration file (tar archive or json)
    and produces three configurations files out of it :

    * a data configuration (self.data_config) : config which describes all
    the raw data files (using the Vortex Standard) necessary for production
    and all the pre-processings that must be done before production (parameter
    extraction, accumulations, combinations, etc.)
    This file is to be used by the data preprocessing module.
    """

    drafting_datetime: Datetime | str = Datetime.now()
    configuration_path: Path
    rules: str | Rules

    prod_configs: List[Tuple[str, Dict]] = []
    data_configs: List[Dict] = []
    mask_configs: List[Tuple[str, Dict]] = []
    _nbr_ok: int = 0
    _expected: int = 0
    _nbr_nok: int = 0

    @field_validator("drafting_datetime")
    def init_drafting_datetime(cls, v: Datetime | str) -> Datetime:
        """
        Converts the drafting_datetime value to a datetime object (if necessary).

        This validator ensures that the 'drafting_datetime' value is a valid datetime
        object. If it's not already a datetime, it attempts to convert it. Raises an
        error if the conversion fails.

        Args:
            v: The value to be converted.

        Returns:
            Converted datetime object.

        Raises:
            ValueError: If the conversion to datetime fails.
        """
        if not isinstance(v, Datetime):
            try:
                return Datetime(v)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid drafting_datetime format: {v}") from e
        return v

    @field_validator("rules")
    def init_rules(cls, v: str | Rules, info: ValidationInfo):
        return (
            Rules(name=v, drafting_datetime=info.data.get("drafting_datetime"))
            if isinstance(v, str)
            else v
        )

    @property
    def prod_config(self) -> dict:
        return {prod[0]: prod[1] for prod in self.prod_configs}

    @property
    def mask_config(self) -> dict:
        return {mask[0]: mask[1] for mask in self.mask_configs}

    @property
    def version_config(self) -> dict:
        return {
            "version": self.global_hash,
            "drafting_datetime": self.rules.drafting_datetime,
            "production_datetime": self.rules.bulletin_datetime,
            "configuration_datetime": Datetime(
                self.configurations[0].get("date_config")
            ),
        }

    @staticmethod
    def _handle_dble_and_oper(data_config: dict, resource_handler: dict):
        """
        Updates experiment information in resource handler and sources for
        'OPER' and 'DBLE' experiment types.

        Args:
            data_config: The data configuration dictionary containing sources
                information.
            resource_handler: The resource handler dictionary.
        """
        experiment = Settings().experiment

        if isinstance(experiment, str):
            experiment = experiment.upper()

        if experiment in ["OPER", "DBLE"]:
            # Update experiment information in resource handler and sources
            for source in data_config["sources"].values():
                for step in source.values():
                    for alternate in step:
                        alternate["experiment"] = experiment
            for ressource in resource_handler:
                ressource["experiment"] = experiment

    @property
    def data_config(self):
        """
        Constructs and returns the data configuration dictionary. This dictionary
        contains information about sources, preprocessed data, and configuration
        version.

        Returns:
            dict: The data configuration dictionary.
        """
        data_config = {
            "config_version": self.global_hash,
            "sources": {},  # Dictionary of source information
            "preprocessed": {},  # Dictionary of preprocessed data information
            "downscaled": {},  # optional downscaled data information
        }

        for data in self.data_configs:
            for (file_id, param), resource_handler in data.items():
                key = f"{file_id} {param}"  # Combine file_id and param for unique key

                if key in data_config["preprocessed"]:
                    continue  # Skip already processed entries

                # Extract parts of the parameter name
                full_root_param, accum = split_var_name(param)

                # Get source information based on configuration and parameters
                sources_dico = self.rules.source_files_terms(
                    data_config=data_config, file_id=file_id, var_name=param
                )
                downscale_id = None
                grid = (
                    resource_handler[0].get("geometry")
                    if len(resource_handler) > 0
                    else None
                )
                # downscale only if source file is eurw1s100 and eurw1s'0grid
                # ie for jj1/j2j3 shift or from fr_j2j3
                if (
                    full_root_param in DOWNSCALABLE_PARAMETERS
                    and len(sources_dico) > 1
                    and (
                        (
                            "eurw1s100" in sources_dico["geometries"]
                            and "eurw1s40" in sources_dico["geometries"]
                        )
                        or "france_jj14" in key
                    )
                ):
                    downscale_id = " ".join([file_id, "downscale", param])
                    data_config["downscaled"].setdefault(
                        downscale_id, {"files": sources_dico}
                    )
                    data_config["downscaled"][downscale_id]["down_grid"] = grid
                    data_config["downscaled"][downscale_id]["param"] = full_root_param
                sources_dico.pop("geometries")

                # Handle experiment for operational configurations (OPER or DBLE)
                self._handle_dble_and_oper(data_config, resource_handler)

                # Build the preprocessed data entry
                data_config["preprocessed"][key] = {
                    "resource_handler": resource_handler,
                    "sources": sources_dico,
                    "downscales": downscale_id,
                    "agg": {"param": full_root_param, "accum": accum},
                }

        return data_config

    @precached_property
    def global_hash(self) -> str:
        """
        Calculates a unique hash code for the entire configuration.

        This property uses the MD5 hashing algorithm to generate a hexadecimal hash key
        based on the serialized representation of all configurations. This hash
        efficiently identifies changes to the overall configuration, enabling
        efficient comparison and management.

        Returns:
            str: A hexadecimal string representing the MD5 hash code of the
                configuration.
        """
        return MD5(self.configurations).hash

    @precached_property
    def configurations(self) -> List[dict]:
        """
        Retrieves all parsed configuration data.

        This property reads the configuration file specified in settings config
        filename, handling single JSON files, JSON-container TAR archives and raising
        errors for unsupported formats. It returns a list of parsed configuration
        dictionaries.

        Returns:
            List of all configurations
        """
        raw_configurations = []
        if is_tarfile(self.configuration_path):
            LOGGER.info("Configuration loaded from a tarfile")

            with tarfile.open(self.configuration_path) as config_tar:
                raw_configurations = [
                    JsonFile(config_tar.extractfile(config_file)).load()
                    for config_file in config_tar.getmembers()
                ]
        elif self.configuration_path.name.endswith(".json"):
            LOGGER.info("Configuration loaded from a JSON")
            raw_configurations = [JsonFile(self.configuration_path).load()]

        configurations = []
        for configuration in raw_configurations:
            if isinstance(configuration, list):
                configurations += configuration
            elif isinstance(configuration, dict):
                configurations += [configuration]
            else:
                LOGGER.error(
                    f"Configuration is a {type(configuration)}, while list or dict"
                    " expected."
                )

        LOGGER.info(f"{len(configurations)} productions loaded")
        return configurations

    @staticmethod
    def _process_config(
        production_config: dict, rules: Rules, global_hash: str
    ) -> Tuple[Dict, Dict, Dict, int, int, int]:
        """
        Processes a single production configuration.

        This function takes a production configuration dictionary and processes
        it using the `Production` class. It then extracts the processed mask, data,
        and production configurations, along with success and failure counts for
        components within the configuration.

        Args:
            production_config: The production configuration dictionary to process.
            rules: Rules of production
            global_hash: Global hash of production

        Returns:
            A tuple containing:
                - processed_production_config: The processed production
                    configuration.
                - data_config: The extracted data configuration dictionary.
                - mask_config: The extracted mask configuration dictionary.
                - compo_ok: The number of successfully processed components.
                - expected: number of config expected
                - compo_nok: The number of components that encountered errors
                    during processing.
        """
        # Create a Production instance and process the configuration
        production = Production(
            global_hash=global_hash, configuration=production_config, rules=rules
        )
        processed_production_config, compo_ok, expected, compo_nok = (
            production.process()
        )

        if compo_nok > 0:
            LOGGER.error(f" {compo_nok} errors encountered in components")

        return (
            processed_production_config,
            production.data_config,
            production.mask_config,
            compo_ok,
            expected,
            compo_nok,
        )

    def _append_config(self, result: Tuple[Dict, Dict, Dict, int, int]):
        """
        Processes the results from parallel processing of individual configurations.

        Args:
            result: A tuple containing processed data for a single
                configuration:
                - result[0]: Product configuration dictionary
                - result[1]: Data configuration dictionary
                - result[2]: Mask configuration dictionary
                - result[3]: Number of successful component processing
                - result[4]: Number of failed component processing
        """
        prod_id = result[0]["id"]

        # Use unpacking and dictionary assignment for clarity
        self.prod_configs.append((prod_id, result[0]))
        self.data_configs.append(result[1])
        self.mask_configs.append((prod_id, result[2]))

        self._nbr_ok += result[3]
        self._expected += result[4]
        self._nbr_nok += result[5]

        LOGGER.info(f"Configuration {prod_id} treated")

    def tas_load(self):
        offset = self.rules.bulletin_datetime.hour
        tas_datetime = self.rules.bulletin_datetime - Timedelta(hours=offset)
        tas_stop = tas_datetime + Timedelta(hours=96)
        single_data_config = []
        # all data needed
        # DD added for synthese text
        for tas_domains, tas_param, start in [
            (["eurw1s100"], "T_AS__HAUTEUR2", 51),
            (["eurw1s40"], "PRECIP__SOL", 51),
            (["eurw1s40"], "PTYPE__SOL", 51),
            (["eurw1s40"], "LPN__SOL", 51),
            (["eurw1s40"], "FF__HAUTEUR10", 51),
            (["eurw1s40"], "RAF__HAUTEUR10", 51),
            (["eurw1s40"], "RISQUE_ORAGE__SOL", 51),
            (["eurw1s40"], "T__HAUTEUR2", 51),
            (["eurw1s40"], "WWMF__SOL", 51),
            (["eurw1s40"], "EAU__SOL", 51),
            (["eurw1s40"], "NEIPOT__SOL", 51),
            (["eurw1s40"], "HU__HAUTEUR2", 51),
            (["eurw1s40"], "DD__HAUTEUR10", 51),
        ]:
            tas_start = tas_datetime + Timedelta(hours=start)
            bests = self.rules.best_preprocessed_files(
                tas_start, tas_stop, tas_domains, [tas_param]
            )
            # only one a priori, first one select
            file_tas = bests[0][0]
            single_data = {
                (file_tas, tas_param): self.rules.resource_handler(
                    file_tas, None, tas_param
                )
            }
            single_data_config += [single_data]
        return single_data_config

    def process(self, nproc: int = cpu_count()):
        """
        Processes all configurations using parallel execution.

        This function clears internal configuration caches, counts successful and
        failed configurations, and then launches parallel tasks to process
        each configuration from `self.configurations`. Finally, it handles errors
        and dumps the processed configurations to JSON files.

        Args:
            nproc: The number of processes to use for parallel execution. Defaults to
                the number of available CPU cores.
        """
        # Dump version configuration to JSON file (it allows to cache the global hash)
        JsonFile(Settings().version_config_filename).dump(self.version_config)

        self.prod_configs.clear()  # Clear internal production configuration cache
        self.data_configs.clear()  # Clear internal data configuration cache
        # init dat with statistic adapted temperature
        if self.rules.name.startswith("alpha"):
            self.data_configs = self.tas_load()

        self.mask_configs.clear()  # Clear internal mask configuration cache
        self._nbr_ok = 0  # Initialize counter for successful configurations
        self._nbr_nok = 0  # Initialize counter for failed configurations

        tasks = Tasks(processes=nproc)  # Create a parallel task executor
        for config in self.configurations:
            # Submit a task to process the current configuration
            tasks.append(
                self._process_config,
                args=(config, self.rules, self.global_hash),
                callback=self._append_config,
                task_name=config.setdefault("production_id", str(getpid())),
            )

        # Run all parallel tasks with a timeout
        tasks.run(timeout=Settings().timeout)

        # Log information about successful and failed configurations
        if self._nbr_nok > 0:
            LOGGER.error(
                f"{self._nbr_ok}/{self._expected} components processed successfully, "
                f"{self._nbr_nok} encountered errors."
            )
        else:
            LOGGER.info(
                f"{self._nbr_ok}/{self._expected} components processed successfully, "
                f"no errors encountered."
            )

        # Dump processed configurations to JSON files
        JsonFile(Settings().prod_config_filename).dump(self.prod_config)
        JsonFile(Settings().mask_config_filename).dump(self.mask_config)
        JsonFile(Settings().data_config_filename).dump(self.data_config)
