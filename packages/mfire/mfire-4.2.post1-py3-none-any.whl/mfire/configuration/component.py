from abc import abstractmethod
from collections import defaultdict
from copy import deepcopy
from functools import cached_property
from time import time
from typing import List, Tuple

import numpy as np
import shapely.geometry as sh

from mfire.composite.aggregation import Aggregation
from mfire.composite.base import BaseModel, precached_property
from mfire.composite.component import (
    AbstractComponentComposite,
    RiskComponentComposite,
    SynthesisComponentComposite,
    SynthesisModule,
)
from mfire.composite.event import EventAccumulationComposite, EventComposite, Threshold
from mfire.composite.field import FieldComposite
from mfire.composite.geo import AltitudeComposite, GeoComposite
from mfire.composite.level import LevelComposite, LocalisationConfig
from mfire.composite.period import PeriodComposite, PeriodsComposite
from mfire.configuration.geo import FeatureCollection
from mfire.configuration.rules import Rules
from mfire.settings import TEXT_ALGO, get_logger
from mfire.utils.date import Datetime
from mfire.utils.exception import ConfigurationError, ConfigurationWarning
from mfire.utils.selection import Selection
from mfire.utils.string import join_var_name, split_var_name

# Logging
LOGGER = get_logger(name=__name__)


class AbstractComponent(BaseModel):
    rules: Rules
    configuration: dict
    configuration_datetime: Datetime

    mask_config: dict
    data_config: dict = {}

    processed_periods: PeriodsComposite
    processed_hazards: dict = {}

    geos: FeatureCollection

    @precached_property
    def box(self) -> Tuple:
        # Collect axes based on their IDs
        unique_geo_ids = set(self.configuration["geos"]) | set(
            self.configuration["geos_descriptive"]
        )
        needed_features = [
            geo for geo in self.geos.features if geo.id in unique_geo_ids
        ]

        mesh_size = 0.26  # Retrieve mesh size dynamically based on configuration?!

        # Return the calculated bounding box
        bounds = np.array([geo.shape.bounds for geo in needed_features])
        lonn, latn, _, _ = tuple(bounds.min(axis=0))
        _, _, lonx, latx = tuple(bounds.max(axis=0))
        return (latx + mesh_size, latn - mesh_size), (
            lonn - mesh_size,
            lonx + mesh_size,
        )

    @abstractmethod
    def process_files_groups(
        self, files_groups: dict
    ) -> List[AbstractComponentComposite]:
        """
        This abstract method must be implemented by child classes to process groups of
        files and their associated data. The function should return a list of component
        objects.

        Args:
            files_groups: A dictionary where keys are tuples of file identifiers and
                values are lists of tuples containing file ID, start time, and stop
                time.

        Returns:
            A list of AbstractComponentComposite objects.
        """

    @precached_property
    @abstractmethod
    def all_parameters(self) -> set[str]:
        """
        Retrieves all parameters used directly or linked to the component.

        Returns:
            list: A list of unique parameters used or linked to the component.
        """

    @cached_property
    def processed_period(self) -> PeriodComposite:
        """Retrieves processed period object from  base component.

        Returns:
            PeriodComposite: The processed period object corresponding to the configured
                period.
        """
        return self.processed_periods[self.configuration["period"]]

    @property
    def processed_config(self) -> dict:
        """
        Retrieves the processed component configuration, ensuring a copy is made
        to avoid modifying the original. Updates the configuration's "period" key
        with the corresponding processed period.

        Returns:
            dict: The processed component configuration with the updated "period".
        """
        # Copy configuration to avoid modifying the original
        processed_config = deepcopy(self.configuration)
        processed_config["period"] = self.processed_period
        processed_config["production_datetime"] = self.rules.bulletin_datetime
        processed_config["configuration_datetime"] = self.configuration_datetime
        return processed_config

    def process(self) -> Tuple[List[AbstractComponentComposite], int]:
        """Processes a single component based on its configuration.

        This function retrieves component configuration, fetches relevant parameters
        and periods, and then iterates over geos associated with the component.
        For each geo, it finds the best preprocessed files using the component manager
        and groups them based on the selected files. Finally, it generates a list of
        components using the processed configuration, file groups, and parameters.

        Returns:
            List of components using the configuration.
            number of errors
        """
        logger = LOGGER.bind(
            compo=self.configuration.get("id"),
            period=self.configuration.get("period"),
            hazard=self.configuration.get(
                "hazard_name", self.configuration.get("hazard_id", "text")
            ),
        )

        result = []
        nb_error = 0
        logger.info("Component processing...")
        start_time = time()
        try:

            # Process each geo associated with the component
            files_groups = defaultdict(lambda: [])

            for geo_id in self.configuration["geos"]:
                logger = logger.bind(geo=geo_id)
                logger.info("Processing geo")

                # Find usable geometries for this geo
                geometries = self.usable_geometries(geo_id)

                # Find best preprocessed files for this geo
                try:
                    best_files = tuple(
                        self.rules.best_preprocessed_files(
                            start=self.processed_period.start,
                            stop=self.processed_period.stop,
                            geometries=geometries,
                            params=self.all_parameters,
                        )
                    )
                    if not best_files:
                        logger.warning("No preprocessed file found for geo")
                    else:
                        files_groups[best_files] += [geo_id]
                except ConfigurationWarning as e:
                    logger.warning(e)
                except ConfigurationError as e:
                    nb_error += 1
                    logger.error(e)
            logger = logger.try_unbind("geo")

            if files_groups:
                # Generate final component list
                result = self.process_files_groups(files_groups)
            else:
                if nb_error > 0:
                    logger.error("No preprocessed files found for any geo")
                logger.warning(
                    "No preprocessed files found for any geo: but OK (period)"
                )

        except Exception as excpt:
            nb_error += 1
            logger.error(f"Failed to process component: {excpt}", exc_info=True)

        logger.info(f"Component processed. Elapsed time={time() - start_time:.3f}s")
        return result, nb_error

    def usable_geometries(self, geo_id: str) -> List[str]:
        """
        Returns a list of usable geometry names within a geographical zone based on its
        configuration.

        Args:
            geo_id: The geographical zone's id.

        Returns:
            List[str]: A list containing the names of usable geometries.
        """
        try:
            geo_shape = next(
                geo.shape for geo in self.geos.features if geo.id == geo_id
            )
        except StopIteration:
            return []  # Return empty list if geo_base is not found

        # Extract usable geometries based on zone configuration and bounds
        return [
            bound_name
            for bound_name, bounds in self.rules.bounds
            if sh.box(*bounds).contains(geo_shape)
        ]

    def selection(self, start_stop: Tuple[Datetime, Datetime]) -> Selection:
        """
        Sets a selection based on a start and stop time, latitude/longitude bounds, and
        a mesh size.

        Args:
            start_stop: Tuple containing the start and stop times

        Returns:
            Dictionary containing the selection information.
        """
        return Selection(
            slice={
                "valid_time": start_stop,  # Assumes start_stop is a valid time tuple
                "latitude": (self.box[0][0], self.box[0][1]),
                "longitude": (self.box[1][0], self.box[1][1]),
            }
        )

    def _file_start_stop_ids(self, best_files: list) -> Tuple[Datetime, Datetime, list]:
        start, stop, file_ids = None, None, []
        for file_id, file_start, file_stop in best_files:
            file_start, file_stop = Datetime(file_start), Datetime(file_stop)
            if start is None or file_start < start:
                start = file_start
            if stop is None or file_stop > stop:
                stop = file_stop

            for param in self.all_parameters:
                if (key := (file_id, param)) not in self.data_config:
                    # Preprocess data if it doesn't exist
                    self.data_config[key] = self.rules.resource_handler(
                        file_id, None, param
                    )

                if file_id not in file_ids:
                    file_ids.append(file_id)
        return start, stop, file_ids


class RiskComponent(AbstractComponent):
    @precached_property
    def all_parameters(self) -> set[str]:
        """
        Retrieves all parameters used directly or linked to the risk component.

        This method gathers parameters from events within each level of the
        component configuration, considering both direct parameters and those
        linked through the rules' parameter link DataFrame.

        Returns:
            list: A list of unique parameters (strings) used or linked to the component.
        """
        all_params = set()
        rules = self.rules

        for level in self.configuration["levels"]:
            for event in level["elementsEvent"]:
                param_name, accum = split_var_name(event["field"])
                if param_name not in rules.param_link_df:
                    all_params |= {event["field"]}
                    continue
                linked_root_params = [
                    p.split("__")
                    for p in rules.param_link_df[param_name].dropna().index
                ]
                all_params |= {
                    join_var_name(p, l, accum) for p, l in linked_root_params
                }

        if "Neige" in self.configuration["hazard_name"]:
            all_params |= {"WWMF__SOL", "NEIPOT3__SOL"}
        if "Pluies" in self.configuration["hazard_name"]:
            all_params |= {"WWMF__SOL", "EAU1__SOL"}

        return all_params

    def process_level(self, level: dict, **kwargs) -> LevelComposite:
        """
        Processes a level dictionary and its associated events into a `LevelComposite`
        object.

        This function takes a `level` dictionary (representing a level in a hierarchy)
        and various keyword arguments as input. It processes the level data,
        including aggregation, localization configuration, and events, and returns a
        `LevelComposite` object encapsulating the processed information.

        Args:
            level: The dictionary representing the level to be processed.
            **kwargs: Additional keyword arguments that may be used by the processing
                functions.

        Returns:
            LevelComposite: A LevelComposite object containing the processed level data.
        """
        aggregation = level.get("aggregation")
        return LevelComposite(
            level=level["level"],
            logical_op_list=level["logicalOpList"],
            aggregation_type=level["aggregationType"],
            aggregation=Aggregation.from_configuration(
                aggregation, self.mask_config["file"]
            ),
            events=[
                self.process_event(event, **kwargs) for event in level["elementsEvent"]
            ],
            localisation=LocalisationConfig(
                compass_split=self.configuration.get("compass_split", True),
                altitude_split=self.configuration.get("altitude_split", True),
                geos_descriptive=self.configuration.get("geos_descriptive", []),
            ),
        )

    def process_event(self, event: dict, **kwargs) -> EventComposite:
        """
        Processes an event definition dictionary and constructs an EventComposite
        object.

        Args:
            event: The event definition dictionary.
            **kwargs: Additional keyword arguments used for processing.
                - mask_id: Id of mask.
                - file_id: File identifier.
                - start_stop: Start and stop time for data selection.
                - aggregation: Aggregation configuration for data.

        Returns:
            EventComposite (or EventAccumulationComposite): An EventComposite or
                EventAccumulationComposite object representing the processed event.
        """

        # Extract data from kwargs
        file_id = kwargs["file_id"]
        data_config = self.data_config[(file_id, event["field"])][0]

        # Define composite class based on event type (default: EventComposite)
        composite_class = EventComposite

        # Field data selection with extended bounding box
        field_selection = self.selection(kwargs["start_stop"])

        # Create core event composite elements
        new_event = {
            "field": FieldComposite(
                file=data_config["local"],
                name=event["field"],
                grid_name=data_config["geometry"],
                selection=field_selection,
            ),
            "category": event["category"],
            "altitude": AltitudeComposite.from_grid_name(
                data_config["geometry"],
                alt_min=self.configuration.get("alt_min"),
                alt_max=self.configuration.get("alt_max"),
            ),
            "geos": GeoComposite(
                grid_name=data_config["geometry"],
                file=self.mask_config["file"],
                mask_id=kwargs["mask_id"],
            ),
            "aggregation": Aggregation.from_configuration(
                event.get("aggregation"), kwargs["mask_id"], data_config["geometry"]
            ),
        }

        # Handle plain and mountain thresholds based on event definition
        if event.get("alt_min"):
            new_event["mountain"] = Threshold.from_configuration(event["plain"])
        else:
            new_event["plain"] = Threshold.from_configuration(event["plain"])
            if "mountain" in event:
                new_event["mountain"] = Threshold.from_configuration(event["mountain"])

        # Handle mountain altitude if provided
        if "altitude" in event:
            new_event["mountain_altitude"] = event["altitude"][0]["mountainThreshold"]

        # Handle case where accumulation period exceeds model step
        prefix, level, accum = split_var_name(event["field"], full_var_name=False)
        if accum and accum > (model_step := int(self.rules.file_info(file_id)["step"])):
            # Check if base parameter configuration exists for this file
            param_base = join_var_name(prefix, level, model_step)
            if (file_id, param_base) not in self.data_config:
                # If not, generate configuration for the base parameter
                self.data_config[(file_id, param_base)] = self.rules.resource_handler(
                    file_id, None, param_base
                )

            # Add field_1 and accumulation period values
            new_event |= {
                "field_1": FieldComposite(
                    file=self.data_config[(file_id, param_base)][0]["local"],
                    name=param_base,
                    grid_name=data_config["geometry"],
                    selection=field_selection,
                ),
                "cum_period": accum,
            }
            composite_class = EventAccumulationComposite

        return composite_class(**new_event)

    def process_files_groups(self, files_groups: dict) -> List[RiskComponentComposite]:
        """
        This function processes groups of files and their associated geographical data
        to create RiskComponentComposite objects.

        Args:
            files_groups: A dictionary where keys are tuples of file identifiers and
                values are lists of tuples containing file ID, start time, and stop
                time.

        Returns:
            A list of RiskComponentComposite objects.
        """
        result = []
        mask_id = next(iter(files_groups.values()))

        for best_files in files_groups:
            start, stop, file_ids = self._file_start_stop_ids(best_files)

            # Create and append RiskComponentComposite object
            result.append(
                self._process_files_groups_new_risk(
                    mask_id, best_files, file_ids, (start, stop)
                )
            )
        return result

    def _process_files_groups_new_risk(
        self,
        mask_id: str,
        best_files: list,
        file_ids: list,
        start_stop: Tuple[Datetime, Datetime],
    ) -> RiskComponentComposite:
        # Update process configuration with geographical data
        new_risk = self.processed_config
        new_risk["levels"] = []
        for file_id, start_time, stop_time in best_files:
            # Update process configuration with processed levels
            new_risk["levels"] += [
                self.process_level(
                    level,
                    file_id=file_id,
                    start_stop=(start_time, stop_time),
                    mask_id=mask_id,
                )
                for level in self.processed_config["levels"]
            ]

        new_risk["params"] = {}
        for param in self.all_parameters:
            param_info = self.data_config[(file_ids[0], param)][0]
            new_risk["params"][param] = FieldComposite(
                file=[
                    self.data_config[(file_id, param)][0]["local"]
                    for file_id in file_ids
                ],
                grid_name=param_info["geometry"],
                name=param,
                selection=self.selection(start_stop),
            )
        return RiskComponentComposite(**new_risk)


class SynthesisComponent(AbstractComponent):
    @precached_property
    def all_parameters(self) -> set[str]:
        """
        Retrieves all parameters used in the text component.

        This method iterates through weather configurations within the component
        configuration and collects parameters.

        Returns:
            list: A list of unique parameters (strings) used by the text component.
        """
        params = set()
        for weather in self.configuration["weather"]:
            algo_conf = TEXT_ALGO[weather["id"]][weather.get("algo", "generic")]
            params |= {d["field"] for d in algo_conf["params"].values()}
            if field := (weather.get("condition") or {}).get("field"):
                params.add(field)
        return params

    def grid_name(self, file_id: str, param: dict) -> str:
        """
        Retrieves the grid name from the component manager's data configuration.

        Args:
            file_id: The ID of the data file.
            param: Dictionary containing the field name to retrieve the grid name for.

        Returns:
            Grid name associated with the specified file ID and field name.
        """
        return self.data_config[(file_id, param["field"])][0]["geometry"]

    def name(self, file_id: str, param: dict) -> str:
        """
        Retrieves the data name from the component manager's data configuration.

        Args:
            file_id: The ID of the data file.
            param: A dictionary containing the field name to retrieve the data
                name for.

        Returns:
            str: The data name associated with the specified file ID and field name.
        """
        return self.data_config[(file_id, param["field"])][0]["param"]

    def _files_groups_start_stop_ids(self, files_groups: dict) -> Tuple[Tuple, List]:
        # Find the earliest and latest file times across all groups
        start, stop, file_ids = None, None, []
        for best_files in files_groups.keys():
            file_start, file_stop, ids = self._file_start_stop_ids(best_files)
            file_ids += ids
            if start is None or file_start < start:
                start = file_start
            if stop is None or file_stop > stop:
                stop = file_stop

        return (start, stop), file_ids

    def process_weather(self, files_groups: dict, weather: dict) -> SynthesisModule:
        """
        Computes the weather data based on the provided configuration and retrieves
        necessary information from the component manager.

        Args:
            files_groups: A dictionary where keys are tuples of file identifiers and
                values are lists of tuples containing file ID, start time, and stop
                time.
            weather: A dictionary containing the weather data configuration.

        Returns:
            SynthesisModule with the processed weather data.
        """
        start_stop, file_ids = self._files_groups_start_stop_ids(files_groups)

        # Create a deep copy of the weather dictionary to avoid modifying the original
        new_weather = deepcopy(weather)

        # Set the algorithm based on the weather configuration or default to "generic"
        algorithm = weather.get("algo", "generic")
        new_weather["algorithm"] = algorithm
        new_weather["period"] = self.processed_config["period"]
        new_weather["localisation"] = LocalisationConfig(
            compass_split=self.processed_config["compass_split"],
            altitude_split=self.processed_config["altitude_split"],
            geos_descriptive=self.processed_config["geos_descriptive"],
        )
        new_weather["nebulosity"] = weather.get("nebulosity")

        # Retrieve parameter information from the weather configuration
        new_weather["geos"] = GeoComposite(
            grid_name=self.grid_name(
                file_ids[0],
                next(iter(TEXT_ALGO[weather["id"]][algorithm]["params"].values())),
            ),
            file=self.mask_config["file"],
            mask_id=next(iter(files_groups.values())),
        )

        # Process each weather parameter
        new_weather["params"], new_weather["units"] = {}, {}
        for key, param in TEXT_ALGO[weather["id"]][algorithm]["params"].items():
            # Create a FieldComposite object to handle the parameter data
            new_weather["params"][key] = FieldComposite(
                file=[
                    self.data_config[(file_id, param["field"])][0]["local"]
                    for file_id in file_ids
                ],
                selection=self.selection(start_stop),
                grid_name=self.grid_name(file_ids[0], param),
                name=self.name(file_ids[0], param),
            )

            new_weather["units"][key] = weather.get("algo", param["default_units"])

        if weather_condition := weather.get("condition"):
            grid_name = self.grid_name(file_ids[0], weather_condition)

            # Create an EventComposite object to handle the condition
            new_weather["condition"] = EventComposite(
                field=FieldComposite(
                    file=[
                        self.data_config[(file_id, weather_condition["field"])][0][
                            "local"
                        ]
                        for file_id in file_ids
                    ],
                    selection=self.selection(start_stop),
                    grid_name=grid_name,
                    name=self.name(file_ids[0], weather_condition),
                ),
                plain=Threshold.from_configuration(weather_condition["plain"]),
                mountain=Threshold.from_configuration(
                    weather_condition.get("mountain")
                ),
                mountain_altitude=weather.get("altitude", [{}])[0].get(
                    "mountainThreshold"
                ),
                category=weather_condition["category"],
                geos=GeoComposite(grid_name=grid_name, file=self.mask_config["file"]),
                aggregation=Aggregation.from_configuration(
                    weather_condition["aggregation"],
                    self.mask_config["file"],
                    grid_name,
                ),
                altitude=AltitudeComposite.from_grid_name(grid_name),
            )

        new_weather.pop("altitude", None)
        return SynthesisModule(**new_weather)

    def process_files_groups(
        self, files_groups: dict
    ) -> List[SynthesisComponentComposite]:
        """
        This function processes groups of files and their associated data to create a
        SynthesisComponentComposite object.

        Args:
            files_groups:  A dictionary where keys are tuples of file identifiers and
                values are lists of tuples containing file ID, start time, and stop
                time.

        Returns:
            A list containing a single SynthesisComponentComposite object.
        """
        processed_config = self.processed_config
        processed_config["weathers"] = [
            self.process_weather(files_groups, weather)
            for weather in self.processed_config["weather"]
        ]

        # Create and return a single SynthesisComponentComposite object
        return [SynthesisComponentComposite(**processed_config)]
