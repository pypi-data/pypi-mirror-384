from copy import deepcopy
from itertools import product
from typing import Dict, List

import pandas as pd
from timezonefinder import TimezoneFinder

from mfire.composite.base import BaseModel, precached_property
from mfire.composite.component import TypeComponent
from mfire.configuration.component import RiskComponent, SynthesisComponent
from mfire.configuration.geo import FeatureCollection
from mfire.configuration.period import PeriodCollection
from mfire.configuration.rules import Rules
from mfire.settings import Settings, get_logger
from mfire.utils.date import Datetime
from mfire.utils.exception import ConfigurationError
from mfire.utils.json import prepare_json

# Logging
LOGGER = get_logger(name=__name__)


class Production(BaseModel):
    global_hash: str
    rules: Rules
    configuration: dict

    data_config: dict = {}

    @precached_property
    def id(self) -> str:
        """
        Returns the production ID from the configuration or a default value.

        This property attempts to retrieve the "production_id" key from the
        configuration dictionary. If the key is missing, it returns a default value
        of "UnknownProductionID".

        Returns:
            str: The production ID from the configuration or the default value.
        """
        return self.configuration.get("production_id", "UnknownProductionID")

    @precached_property
    def name(self) -> str:
        """
        Returns the production name from the configuration or a constructed value.

        This property retrieves the "production_name" key from the configuration
        dictionary. If the key is missing, it constructs a name using the format
        "UnknownProductionName_<production_id>".

        Returns:
            str: The production name from the configuration or the constructed value.
        """
        return self.configuration.get(
            "production_name", f"UnknownProductionName_{self.id}"
        )

    @property
    def language(self) -> str:
        """
        Returns the language from the configuration or a default value.

        This property retrieves the "language" key from the configuration dictionary.
        If the key is missing, it returns the (french) default language.

        Returns:
            str: The language from the configuration or the default value.
        """
        return self.configuration.get("production_language", "fr")

    @property
    def time_zone(self) -> str:
        """
        Returns the time zone from the configuration or a default value.

        This property retrieves the "time_zone" key from the configuration dictionary.
        If the key is missing, it returns the (french) default time zone.

        Returns:
            str: The time zone from the configuration or the default value.
        """
        return self.configuration.get("time_zone") or (
            TimezoneFinder().timezone_at(
                lng=self.geos.centroid.x, lat=self.geos.centroid.y
            )
            or "Europe/Paris"
        )

    @precached_property
    def geos(self) -> FeatureCollection:
        """
        Converts METRONOME area config to GeoJSON FeatureCollection.

        Returns:
            FeatureCollection: GeoJSON representation of area config.

        Raises:
            ConfigurationError: when conversion fails.
        """
        try:
            return FeatureCollection(features=self.configuration["geos"])
        except Exception as e:
            # Raise a more specific error with clear context for better understanding
            raise ConfigurationError(
                "Failed to create GeoJSON FeatureCollection"
            ) from e

    @precached_property
    def mask_config(self) -> dict:
        """
        Returns a dictionary containing metadata and configuration information about the
        mask.

        This property constructs a dictionary that includes:
            - File path to the mask file.
            - Mask ID, name, and configuration-related hashes.
            - Geospatial information (`geos`) associated with the mask.

        Returns:
            dict: A dictionary containing mask configuration information.
        """
        settings = Settings()
        mask_file = settings.mask_dirname / f"{self.id}.nc"
        return {
            "file": mask_file,
            "id": self.id,
            "name": self.name,
            "config_hash": self.global_hash,
            "config_language": self.language,
            "mask_hash": self.geos.hash,
            "geos": self.geos,
            "resource_handler": {
                "role": f"mask_{self.id}",
                "fatal": False,
                "kind": "promethee_mask",
                "promid": self.id,
                "version": self.geos.hash,
                "namespace": "vortex.cache.fr",
                "experiment": settings.experiment,
                "vapp": settings.vapp,
                "vconf": settings.vconf,
                "block": "masks",
                "format": "netcdf",
                "local": mask_file,
            },
        }

    @precached_property
    def processed_periods(self) -> PeriodCollection:
        """
        Returns a PeriodCollection object containing the processed periods.

        This property leverages the `PeriodCollection` class to retrieve the processed
        periods based on the configuration and bulletin datetime.

        Returns:
            PeriodCollection: A PeriodCollection object representing the processed
                periods.
        """
        return PeriodCollection(**self.configuration).processed_periods(
            self.rules.bulletin_datetime
        )

    @precached_property
    def processed_hazards(self) -> Dict[str, dict]:
        """
        Extracts hazards (single string ID) from production and validates format.

        Returns:
            Dict[str, dict]: Dictionary containing processed hazards with their IDs as
                keys.
        """
        processed_hazards = {}
        for hazard in self.configuration["hazards"]:
            # Add a deep copy of the valid hazard to the processed dictionary
            processed_hazards[hazard["id"]] = deepcopy(hazard)

        return processed_hazards

    @precached_property
    def all_configurations(self) -> List[dict]:
        """
        Get all component configurations in Promethee format.

        Retrieves all component configurations from the 'prod' dictionary,
        transforms them to Promethee's structure using appropriate methods,
        and adds production information if available. Handles potential errors.

        Returns:
            List[dict]: List of all component configurations in Promethee format.
        """
        components = []
        for component_config in self.configuration["components"]:
            try:
                if component_config["data"]["type"] == TypeComponent.RISK:
                    components += self._risk_configuration(component_config)
                else:
                    components += self._synthesis_configuration(component_config)
            except ConfigurationError as excpt:
                LOGGER.error("Configuration Error caught.", excpt=excpt, exc_info=True)

        return components

    def _base_configuration(self, component_config: dict) -> dict:
        """
        Extracts essential configuration information from a component's configuration.

        This function takes a component's full configuration and returns a subset
        containing key information for processing and handling.

        Args:
            component_config: The complete component configuration dictionary.

        Returns:
            dict: A dictionary containing the base component configuration details.
        """
        config_geos = [
            zone.id
            for zone in self.geos.features
            if zone.id in component_config["data"].get("geos_descriptive", [])
        ]

        output = {
            "id": component_config["id"],
            "type": component_config["data"]["type"],
            "name": component_config["name"],
            "customer": component_config.get("customer", "unknown"),
            "customer_name": component_config.get("customer_name", "unknown"),
            "production_id": self.id,
            "production_name": self.name,
            "product_comment": component_config["data"].get("product_comment", True),
            "compass_split": component_config["data"].get("compass_split", True),
            "altitude_split": component_config["data"].get("altitude_split", True),
            "geos_descriptive": config_geos,
        }

        # Optionally include altitude ranges if available
        if alt_min := component_config["data"].get("alt_min"):
            output["alt_min"] = alt_min
        if alt_max := component_config["data"].get("alt_max"):
            output["alt_max"] = alt_max

        return output

    def _hazard_df(self, hazard_idx: int, hazard: dict, columns: list) -> pd.DataFrame:
        """Creates a pandas DataFrame from a hazard dictionary.

        This function transforms a dictionary containing hazard data (`hazard`)
        into a structured pandas DataFrame (`hazard_df`). The DataFrame includes
        columns specified in the `columns` list, along with additional columns
        for organization and indexing (hazard ID, name, level index, configuration
        index, etc.).

        Args:
            hazard_idx: The order (index) of this hazard.
            hazard: The dictionary containing the hazard definition.
            columns: A list of column names to include in the DataFrame.

        Returns:
            The reshaped hazard data as a pandas DataFrame.
        """
        hazard_df = pd.DataFrame(columns=columns)

        for level_idx, level in enumerate(hazard["levels"]):
            for config_idx, config in enumerate(level["configs"]):
                config_geos = [
                    zone.id for zone in self.geos.features if zone.id in config["geos"]
                ]
                for geo, period in product(config_geos, config["periods"]):
                    # Create a new row with relevant data
                    new_line_df = pd.DataFrame(
                        {
                            "hazard_id": hazard["id"],
                            "period": period,
                            "hazard_name": hazard["label"],
                            "geo": geo,
                            "hazard_idx": hazard_idx,
                            "level_idx": level_idx,
                            "config_idx": config_idx,
                        },
                        index=[0],
                    )

                    # Concatenate the new row to the DataFrame
                    hazard_df = pd.concat([hazard_df, new_line_df], ignore_index=True)

        return hazard_df

    def _risk_configuration(self, component_config: dict) -> List[dict]:
        """
        Reshape component configuration from Metronome to Promethee format.

        This function takes a component configuration dictionary in Metronome's format
        and transforms it into a list of dictionaries following Promethee's structure.

        Args:
            component_config: The component configuration dictionary in
                Metronome's format.

        Returns:
            List[dict]: A list of dictionaries representing the reshaped components in
                Promethee's structure.
        """
        # Create an empty DataFrame to store hazard information
        component_df = pd.DataFrame(
            columns=[
                "hazard_id",
                "period",
                "hazard_name",
                "geo",
                "hazard_idx",
                "level_idx",
                "config_idx",
            ]
        )

        # Process each hazard in the component configuration
        for hazard_idx, hazard in enumerate(component_config["data"]["hazards"]):
            try:
                # Call a separate function to process each hazard data
                haz_df = self._hazard_df(hazard_idx, hazard, component_df.columns)
                # Concatenate the processed hazard data to the main DataFrame
                component_df = pd.concat([component_df, haz_df], ignore_index=True)
            except Exception:
                # Log errors if any occur during hazard processing
                LOGGER.error(
                    "Failed to reshape hazard.",
                    hazard_id=hazard.get("id"),
                    exc_info=True,
                )

        # Set the DataFrame index and sort for efficient lookups
        component_df = component_df.set_index(
            ["hazard_id", "period", "hazard_name", "geo"]
        ).sort_index()

        # Create a dictionary to group hazards based on specific criteria
        grouped_components_dict = {}
        for idx in component_df.index.unique():
            key = idx[:3] + tuple(component_df.loc[idx].values.reshape(-1))
            grouped_components_dict.setdefault(key, []).append(idx[3])

        # List to store the reshaped components in Promethee's structure
        components = []

        # Get the base configuration for the component
        local_component_config = self._base_configuration(component_config)

        # Iterate through each key-value pair in the grouped dictionary
        for key, value in grouped_components_dict.items():
            new_compo = {
                "hazard_id": key[0],
                "period": key[1],
                "geos": value,
                "hazard_name": key[2],
                "levels": [],
            }

            # Update the new component dictionary with the base configuration
            new_compo.update(local_component_config)

            # Retrieve specific values from the DataFrame based on the current key and
            # geo-location
            levels_indices = component_df.loc[
                (key[0], key[1], key[2], value[0])
            ].values.reshape((-1, 3))

            # Iterate through the retrieved hazard levels and configurations
            for hidx, lidx, cidx in levels_indices:
                # Extract information from the hazard level and configuration
                current_level = component_config["data"]["hazards"][hidx]["levels"][
                    lidx
                ]
                current_config = current_level["configs"][cidx]

                # Create a new dictionary for the current level with level name and data
                # model
                current_level_config = {"level": current_level["level"]}
                current_level_config.update(current_config["dataModel"])

                # Append the level configuration dictionary to the "levels" list of the
                # new component
                new_compo["levels"] += [current_level_config]

            # Add the new component dictionary with reshaped hazard information to the
            # results list
            components += [new_compo]

        return components

    def _synthesis_configuration(self, component_config: dict) -> List[dict]:
        """
        Reshape text component config (Metronome) to Promethee format.

        Converts a text component configuration dictionary from Metronome's format
        into a list of dictionaries following Promethee's structure for weather data.

        Args:
            component_config: Component configuration (Metronome format).

        Returns:
            List[dict]: List of configurations following Promethee's structure.
        """
        # Create an empty DataFrame to store weather data
        component_df = pd.DataFrame(
            columns=["period", "geo", "weather_idx", "config_idx"]
        )

        # Process each weather condition and configuration
        for weather_idx, weather in enumerate(component_config["data"]["weather"]):
            for config_idx, config in enumerate(weather["configs"]):
                config_geos = [
                    zone.id for zone in self.geos.features if zone.id in config["geos"]
                ]

                for period, geo in product(config["periods"], config_geos):
                    # Create a new DataFrame row for each combination
                    component_df = pd.concat(
                        [
                            component_df,
                            pd.DataFrame(
                                {
                                    "period": period,
                                    "geo": geo,
                                    "weather_idx": weather_idx,
                                    "config_idx": config_idx,
                                },
                                index=[0],
                            ),
                        ],
                        ignore_index=True,
                    )

        # Set DataFrame index and sort for efficient lookups
        component_df = component_df.set_index(["period", "geo"]).sort_index()

        # Group weather data by period and geolocation
        grouped_components_dict = {}
        for idx in component_df.index.unique():
            grouped_components_dict.setdefault(
                (idx[0], *component_df.loc[idx].values.reshape(-1)), []
            ).append(idx[1])

        # List to store the reshaped components
        components = []

        # Get the base configuration for the component
        local_component_config = self._base_configuration(component_config)

        # Process each group of weather data
        for key, value in grouped_components_dict.items():
            new_compo = {"period": key[0], "geos": value, "weather": []}
            new_compo.update(local_component_config)

            weather_indices = component_df.loc[(key[0], value[0])]
            if isinstance(weather_indices, pd.Series):
                weather_indices = weather_indices.to_frame().T

            for weather_idx, config_idx in weather_indices.values:
                current_weather = component_config["data"]["weather"][weather_idx]
                current_config = current_weather["configs"][config_idx]
                new_compo["weather"] += [
                    {
                        "id": current_weather["id"],
                        "condition": (
                            None
                            if current_config["dataModel"] is None
                            else current_config["dataModel"]["text"]
                        ),
                    }
                ]

            components += [new_compo]

        return components

    def process(self):
        """
        Processes the current object's configuration and components,
        creating a structured output for further processing.

        Raises:
            ConfigurationError: If unexpected component types are encountered
                               or there are no valid components in the configuration.

        Returns:
            tuple: A 3-tuple containing:
                - single_prod_config: A dictionary containing processed data
                                              for a single product configuration,
                                              including:
                    - id: The ID of the product
                    - name: The name of the product
                    - config_hash: The global configuration hash
                    - mask_hash: The mask configuration hash
                    - components: A list of dictionaries representing processed
                                         components
                - compo_ok: The number of valid components processed
                - compo_nok: The number of components that failed processing
        """
        prod_config = {
            "id": self.id,
            "name": self.name,
            "config_language": self.language,
            "config_time_zone": self.time_zone,
            "config_hash": self.global_hash,
            "mask_hash": self.mask_config["mask_hash"],
            "components": [],
        }

        # Process each component configuration and create corresponding component
        # objects
        sort_prod = 0
        for component_config in self.all_configurations:
            component_class = (
                RiskComponent
                if component_config["type"] == TypeComponent.RISK
                else SynthesisComponent
            )
            component = component_class(
                rules=self.rules,
                configuration=component_config,
                configuration_datetime=Datetime(self.configuration.get("date_config")),
                mask_config=self.mask_config,
                data_config=self.data_config,
                processed_periods=self.processed_periods,
                processed_hazards=self.processed_hazards,
                geos=self.geos,
            )

            # Extract processed data from the component and append it
            processed, error_compo = component.process()
            prod_config["components"].extend(processed)

            # Update the data configuration
            self.data_config.update(component.data_config)
            # prepare coefficient for sorting production (by surface)
            box = component.box
            sort_prod += (box[0][0] - box[0][1]) * (box[1][1] - box[1][0])

        prod_config.update({"sort": sort_prod})

        # Validate the presence of valid components
        nb_ok = len(prod_config["components"])
        if nb_ok == 0:
            raise ConfigurationError(
                f"No valid components found for {len(self.all_configurations)} "
                f"configurations."
            )

        return (
            prepare_json(prod_config),
            nb_ok,
            len(self.all_configurations),
            error_compo,
        )
