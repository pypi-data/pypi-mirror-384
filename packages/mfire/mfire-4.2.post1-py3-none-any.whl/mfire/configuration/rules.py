from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import field_validator, model_validator

from mfire.composite.base import BaseModel, precached_property
from mfire.composite.serialized_types import s_datetime
from mfire.settings import LOCAL, RULES_DIR, Settings, get_logger
from mfire.utils.date import Datetime, Timedelta
from mfire.utils.exception import ConfigurationError, ConfigurationWarning
from mfire.utils.string import TagFormatter, split_var_name

# Logging
LOGGER = get_logger(name=__name__)


class Rules(BaseModel):
    """
    This class represents common data rules in the Promethee system.

    Data rules in Promethee define how to retrieve and process data based
    on various criteria like current datetime, geometry used or time steps to provide

    These rules are specified in CSV files containing information about:

    * **grib_param:** Defines how to extract parameters from GRIB files.
    * **agg_param:** Defines relationships between accumulated parameters
      (e.g., "RR6_SOL") and their corresponding base parameters (e.g., "RR_SOL").
    * **param_link:** Defines linked parameters (e.g., "FF", "RAF", and "DD").
    * **geometries:** Defines features of specific geometries (e.g., "EURW1S100").

    Attributes:
        name: Name of the common rules.
        path (Optional[Path]): Path to the directory containing the CSV rule files.
            Defaults to the value in the `RULES_DIR` constant.
        drafting_datetime: Datetime when these rules were created.
            Defaults to the current datetime.
    """

    name: str
    path: Optional[Path] = RULES_DIR
    drafting_datetime: Optional[s_datetime] = None

    @field_validator("path")
    def validate_path(cls, v: Path) -> Path:
        """
        Validates the provided path. Checks if the given path exists and is a
        directory. Raises an exception if not found.

        Args:
            v: The path to validate.

        Raises:
            FileNotFoundError: If the given path doesn't exist.

        Returns:
            Path: The validated path.
        """

        if not v.is_dir():
            raise FileNotFoundError(f"Directory not found: {v}")

        return v

    @model_validator(mode="after")
    def validate_name_and_directory(self) -> Rules:
        """
        Root validator ensuring that the given name has a corresponding directory.
        This validator checks if the directory formed by combining the provided path and
        name exists. If not, it raises a FileNotFoundError.

        Raises:
            FileNotFoundError: If the directory corresponding to the given name doesn't
                exist.

        Returns:
            Rules if a good directory was given or None otherwise.
        """

        rules_dirname = Path(self.path) / self.name
        if not rules_dirname.is_dir():
            raise FileNotFoundError(f"Directory not found: {rules_dirname}")

        return self

    @precached_property
    def bulletin_datetime(self) -> Optional[Datetime]:
        """
        Property returning the bulletin datetime (reference datetime + 1 hour).

        Returns:
            Bulletin datetime.
        """
        return (
            self.drafting_datetime.rounded
            if self.drafting_datetime is not None
            else None
        )

    def _df(self, file_kind: str, index_col: int | List[int] = None) -> pd.DataFrame:
        """
        Retrieves or creates a pandas DataFrame for the specified file kind. Reads
        CSV, cleans (drops all-NA cols), sorts, returns.

        Args:
            file_kind: The kind of CSV file (e.g., "rules", "data").
            index_col: Column(s) to use as the index
                for the DataFrame (as per `pd.read_csv`). Defaults to None.

        Returns:
            The retrieved or newly created DataFrame.
        """
        return (
            pd.read_csv(self._filename(file_kind), index_col=index_col)
            .dropna(axis=1, how="all")
            .sort_index()
        )

    @precached_property
    def grib_param_df(self) -> pd.DataFrame:
        return self._df("grib_param", index_col=[0, 1])

    @precached_property
    def family_param_df(self) -> pd.DataFrame:
        return self._df("family_param", index_col=0)

    @precached_property
    def param_link_df(self) -> pd.DataFrame:
        return self._df("param_link", index_col=0)

    @precached_property
    def geometries_df(self) -> pd.DataFrame:
        return self._df("geometries", index_col=0)

    def _full_df(
        self, file_kind: str, days_back: int, concat_axis: int = 0
    ) -> Optional[pd.DataFrame]:
        """
        Loads, concatenates, and prepares a DataFrame for the specified file kind.

        This function opens the relevant CSV file (`file_kind`), concatenates data for
        today and the specified number of previous days (`days_back`), and performs
        cleaning and transformation steps. It then returns the prepared DataFrame.

        Args:
            file_kind: The kind of CSV file (e.g., "rules").
            days_back: The number of days before today to include in the concatenation.
            concat_axis: The axis along which to concatenate DataFrames
                (0 for columns, 1 for rows). Defaults to 0 (concatenating columns).

        Returns:
            The prepared DataFrame.
        """
        if self.bulletin_datetime is None:
            return None

        # Load the base DataFrame for the specified file kind
        raw_df = self._df(file_kind, index_col=0)

        # Concatenate DataFrames for today and the specified number of previous days
        full_df = pd.concat(
            [self._apply_date(raw_df, days_offset=-i) for i in range(days_back)],
            axis=concat_axis,
        )

        # Cleaning and transformation steps (assuming these are the intended steps)
        if "dispo_time" in full_df and "geometry" in full_df:
            full_df = full_df[full_df["dispo_time"] <= self.bulletin_datetime]
            full_df["mesh_size"] = full_df["geometry"].apply(
                lambda s: self.geometries_df.loc[s, "mesh_size"]
            )
            full_df = full_df.sort_values(
                by=["mesh_size", "dispo_time"], ascending=[True, False]
            )
            full_df["terms"] = full_df.apply(
                lambda x: [
                    Datetime(x["start"] + Timedelta(hours=x["step"]) * i)
                    for i in range(
                        int((x["stop"] - x["start"]) / Timedelta(hours=x["step"])) + 1
                    )
                ],
                axis=1,
            )

        return full_df

    @precached_property
    def source_files_df(self) -> Optional[pd.DataFrame]:
        return self._full_df("source_files", concat_axis=0, days_back=3)

    @precached_property
    def preprocessed_files_df(self) -> Optional[pd.DataFrame]:
        df = self._full_df("preprocessed_files", concat_axis=0, days_back=2)
        if df is not None and "params" not in df:
            df["params"] = df.index.to_frame().map(
                lambda x: set(self.files_links_df[x].dropna().index)
            )
        return df

    @precached_property
    def files_links_df(self) -> Optional[pd.DataFrame]:
        return self._full_df("files_links", concat_axis=1, days_back=2)

    @precached_property
    def files_ids(self) -> Optional[set]:
        source_files_df = self.source_files_df
        preprocessed_files_df = self.preprocessed_files_df
        if source_files_df is None or preprocessed_files_df is None:
            return source_files_df or preprocessed_files_df
        return set(source_files_df.index).union(preprocessed_files_df.index)

    @precached_property
    def bounds(self) -> List[Tuple[str, List[float]]]:
        """
        Retrieves bounds (lon_min, lat_min, lon_max, lat_max) for each geometry.

        This function iterates through the geometries and retrieves the corresponding
        bounds  as a list of floats. It returns a list of tuples, where each tuple
        contains the geometry name and its associated bounds.

        Returns:
            List[Tuple[str, List[float]]]: A list of tuples containing geometry names
                and bounds.
        """
        bound_names = ["lon_min", "lat_min", "lon_max", "lat_max"]
        return [
            (geometry, self.geometries_df.loc[geometry, bound_names].tolist())
            for geometry in self.geometries_df.index
        ]

    def _filename(self, file_kind: str) -> Path:
        """Retrieves the full filepath for the given file type.

        This function searches for the CSV file in two locations:

          1. The rules directory for the specific model or configuration
          2. The common directory

        It returns the full filepath of the found file. If the file is not found in
        either location, it raises a FileNotFoundError.

        Args:
            file_kind: The kind of CSV file to locate (e.g. "rules",
                "parameters").

        Returns:
            Path: The full filepath of the located file.

        Raises:
            FileNotFoundError: If the file is not found in either directory.
        """
        if (specific_path := self.path / self.name / f"{file_kind}.csv").is_file():
            return specific_path
        if (common_path := self.path / f"{file_kind}.csv").is_file():
            return common_path
        raise FileNotFoundError(
            f"CSV file {file_kind}.csv not found in either rules directory or "
            f"common directory."
        )

    def _apply_date(
        self, dataframe: pd.DataFrame, days_offset: int = 0
    ) -> pd.DataFrame:
        """
        Applies a date offset and reformats the DataFrame columns and index accordingly.

        Args:
            dataframe: The DataFrame to apply the date offset to.
            days_offset: The number of days to offset the date by. Defaults to 0 (no
                offset).

        Returns:
            New DataFrame with the applied date offset and reformatted columns and
            index.
        """

        def convert_date(
            offset_date: Datetime, dataframe: pd.DataFrame
        ) -> List(pd.DataFrame):
            def convert_col(col: str) -> pd.DataFrame:
                cols = pd.DataFrame()
                new_col = offset_date.format_bracket_str(col)
                cols[new_col] = dataframe[col].apply(offset_date.format_bracket_str)
                return cols

            return [convert_col(col) for col in dataframe.columns]

        # Calculate the new date to apply, considering midnight
        offset_date = (self.bulletin_datetime + Timedelta(days=days_offset)).midnight

        # Process columns: format with the offset date in brackets
        dataframe_copy = pd.concat(convert_date(offset_date, dataframe), axis=1)

        # Process index: format with the offset date in brackets
        dataframe_copy.index = pd.Index(
            map(offset_date.format_bracket_str, dataframe.index)
        )

        if "date" not in dataframe:
            return dataframe_copy

        def datetimize(column: str, offset_datetime: Datetime):
            dataframe_copy[column] = (
                dataframe_copy[column].apply(
                    lambda n: (
                        Timedelta(hours=int(n))
                        if np.isfinite(n)
                        else Timedelta(hours=0)
                    )
                )
                + offset_datetime
            )

        # Handle columns 'date', 'dispo_time'
        for column in ["date", "dispo_time"]:
            datetimize(column, offset_date)

        # Handle columns 'start', 'stop'
        for column in ["start", "stop"]:
            datetimize(column, dataframe_copy["date"])
        return dataframe_copy

    def file_info(self, file_id: str) -> pd.Series:
        """Retrieves file information from either source or preprocessed DataFrames.

        This function checks for the file ID in either source_files_df or
        preprocessed_files_df. If found, it returns a deep copy of the corresponding
        file information as a pandas Series. Otherwise, it returns an empty Series.

        Args:
            file_id: The ID of the file to search for.

        Returns:
            pd.Series: The file information as a pandas Series, or an empty Series
                if the file ID is not found.
        """
        if file_id in self.source_files_df.index:
            return deepcopy(self.source_files_df.loc[file_id])
        if file_id in self.preprocessed_files_df.index:
            return deepcopy(self.preprocessed_files_df.loc[file_id])
        return pd.Series([], dtype=np.uint8)

    def best_preprocessed_file(
        self, term: Datetime, geometries: List[str], params: set[str]
    ) -> Optional[Tuple[str, Datetime]]:
        """
        Locates the most suitable preprocessed file based on specified criteria. This
        function searches the preprocessed files DataFrame for a file that meets given
        conditions.

        Args:
            term: The specific time for which data is needed.
            geometries: An iterable of valid geometry names.
            params: An iterable of required parameter names.

        Returns:
            Tuple containing file ID and stop time, or None if no suitable file is
            found.
        """
        available_files_df = self.preprocessed_files_df[
            (self.preprocessed_files_df.start <= term)
            & (self.preprocessed_files_df.stop >= term)
            & (self.preprocessed_files_df.geometry.isin(geometries))
        ]
        for file_id in available_files_df.index:
            if term not in available_files_df.loc[file_id, "terms"]:
                continue
            if not {split_var_name(param)[0] for param in params}.issubset(
                available_files_df.loc[file_id, "params"]
            ):
                continue
            return file_id, available_files_df.loc[file_id, "stop"]

    def best_preprocessed_files(
        self, start: Datetime, stop: Datetime, geometries: List[str], params: set[str]
    ) -> List[Tuple[str, str, str]]:
        """
        Identifies preprocessed files covering the specified period, geometries and
        parameters.

        This function searches for preprocessed files that meet the following criteria:

            - Start time before or equal to the given `stop` datetime.
            - End time after or equal to the given `start` datetime.
            - Covers at least one of the specified `geometries`.
            - Includes all the required `params`.

        The function first validates the date order and raises errors if `start` is
        after `stop` or the bulletin datetime is after `stop`. It then filters the
        candidate files based on geometries and start/stop times. If no files are
        found, a `ConfigurationError` is raised.

        The function finds the most suitable file for a time window. It starts at the
        later of `start`, the bulletin datetime, or the minimum start time of
        available files. It then continues finding subsequent files until the `stop`
        datetime is reached.

        Args:
            start: The start datetime of the desired period.
            stop: The end datetime of the desired period.
            geometries: A list of valid geometry names.
            params: A set of required parameter names.

        Returns:
            List[Tuple[str, str, str]]: A list of tuples containing:
                - Filename of the preprocessed file.
                - Start datetime covered by the file (as string).
                - Stop datetime covered by the file (as string).

        Raises:
            ConfigurationError: If `start` is after `stop`, or if no files cover the
                requested period and parameters.
            ConfigurationWarning: If the bulletin datetime is after `stop`.
        """

        # Validate date order
        if start > stop:
            raise ConfigurationError(
                f"Invalid date range: start {start} after stop {stop}"
            )
        if self.bulletin_datetime > stop:
            raise ConfigurationWarning(
                f"Bulletin datetime {self.bulletin_datetime} after stop {stop}"
            )

        # Filter candidate files based on geometries and start/stop times
        files_df = self.preprocessed_files_df[
            (self.preprocessed_files_df.stop >= start)
            & self.preprocessed_files_df.geometry.isin(geometries)
        ]

        # Check if any files are available for the requested period
        if files_df.empty or stop < files_df.start.min():
            raise ConfigurationError(f"No data available for period {start} to {stop}")

        # Define the starting point for file search (considering bulletin datetime)
        bulletin_start = self.bulletin_datetime
        if bulletin_start < stop:
            bulletin_start += Timedelta(hours=1)
        term = max(bulletin_start, start, files_df.start.min())

        current_best_file = self.best_preprocessed_file(term, geometries, params)
        if current_best_file is None:
            # Handle edge case where no file covers the initial "correct_start"
            return self.best_preprocessed_files(
                term + Timedelta(hours=1), stop, geometries, params
            )

        current_stop = min(current_best_file[1], stop)
        results = [(current_best_file[0], str(term), str(current_stop))]

        # Find subsequent files until reaching stop or limit
        if current_stop < files_df.stop.max():
            try:
                results.extend(
                    self.best_preprocessed_files(
                        current_stop + Timedelta(hours=1), stop, geometries, params
                    )
                )
            except ConfigurationError:
                pass

        return results

    def _rh(
        self, file_id: str, term: Datetime, var_name: str, alternate: tuple = None
    ) -> dict:
        """
        Generates the configuration dictionary for a specific resource.

        This function takes a file ID, optionally a term (for source resources),
        and optionally a parameter (for preprocessed resources), and constructs
        a dictionary containing configuration information for the resource handler.

        Args:
            file_id: The ID of the file containing the resource information.
            term: Term (date/time) for source resources.
            var_name: The parameter name for preprocessed resources.
            alternate: An alternate configuration (local path, role)
                to use instead of generating one based on the provided file information.

        Returns:
            dict: The configuration dictionary for the resource handler.

        Raises:
            ConfigurationError: resource handle cannot be configured with given data.
        """

        # Retrieve basic information about the file
        file_info = self.file_info(file_id)

        # Define resource-specific columns
        resource_columns = [
            "kind",
            "model",
            "date",
            "geometry",
            "cutoff",
            "origin",
            "nativefmt",
        ]

        # Create a settings object and initialize the configuration dictionary
        settings = Settings()
        rh_dict = file_info[resource_columns].to_dict()

        # Convert date to string format
        rh_dict["date"] = str(Datetime(rh_dict["date"]))

        # Fill in configuration details based on file information
        rh_dict["vapp"] = file_info.get("vapp", settings.vapp)
        rh_dict["vconf"] = file_info.get("vconf", settings.vconf)
        rh_dict["experiment"] = file_info.get("experiment", settings.experiment)
        rh_dict["block"] = file_info["block"]
        rh_dict["namespace"] = file_info["namespace"]
        rh_dict["format"] = rh_dict["nativefmt"]

        # Configure source resource handler
        if file_id in self.source_files_df.index and term is not None:
            rh_dict["term"] = (term - Datetime(rh_dict["date"])).total_hours
            role_name = f"{file_id} {term}"
        # Configure preprocessed resource handler
        elif file_id in self.preprocessed_files_df.index and var_name is not None:
            rh_dict["param"] = var_name
            rh_dict["begintime"] = Timedelta(
                file_info["start"] - file_info["date"]
            ).total_hours
            rh_dict["endtime"] = Timedelta(
                file_info["stop"] - file_info["date"]
            ).total_hours
            rh_dict["step"] = int(file_info["step"])
            role_name = f"{file_id} {var_name}"
        else:
            raise ConfigurationError(
                f"Cannot configure resource handler for file_id '{file_id}' with "
                f"provided inputs. Expected either a source file with a valid term or "
                f"a preprocessed file with a valid variable name."
            )

        # Define role name or use alternate configuration
        if alternate is None:
            # Generate local path using settings and TagFormatter
            local_path = settings.data_dirname / TagFormatter().format_tags(
                LOCAL[file_info["kind"]], rh_dict
            )
            rh_dict["local"] = local_path
            rh_dict["role"] = role_name
        else:
            # Use provided alternate configuration
            rh_dict["alternate"], rh_dict["local"] = alternate

        # Set default resource handler settings
        rh_dict["fatal"] = False
        rh_dict["now"] = True

        return rh_dict

    def resource_handler(
        self, file_id: str, term: Optional[s_datetime], var_name: Optional[str]
    ) -> List[dict]:
        """
        Generates a list of resource handler configurations with potential alternates.

        This function retrieves the configuration for a resource identified by file_id
        (considering the optional `term` for source resources and `param` for
        preprocessed resources), and expands it to include configurations for
        potential alternate files up to the maximum allowed by Settings alternate_max.
        The role and local path of the main resource handler configuration are used for
        alternates to avoid redundancy.

        Args:
            file_id: The ID of the file containing the resource information.
            term: The term (date/time) for source resources.
            var_name: The parameter name for preprocessed resources.

        Returns:
            A list of resource handler configurations (dictionaries).
        """
        main_resource_handler = self._rh(file_id, term=term, var_name=var_name)
        resource_handlers = [main_resource_handler]

        current_alternate_id = file_id
        for _ in range(Settings().alternate_max):
            current_alternate_id = self.file_info(current_alternate_id)["alternate"]
            if current_alternate_id not in self.files_ids:
                break

            resource_handlers.append(
                self._rh(
                    current_alternate_id,
                    term=term,
                    var_name=var_name,
                    alternate=(
                        main_resource_handler["role"],
                        main_resource_handler["local"],
                    ),
                )
            )

        return resource_handlers

    def source_files_terms(
        self, data_config: dict, file_id: str, var_name: str
    ) -> dict:
        """
        Identifies source files and terms required for a preprocessed file.

        This function takes a preprocessed file ID, a parameter name, an optional
        accumulation period, and retrieves information about the source files and
        corresponding terms needed to generate the preprocessed data. It also
        computes and stores the source file configurations in the `data_config`
        dictionary under the 'sources' key.

        Args:
            data_config: The data configuration dictionary.
            file_id: The ID of the preprocessed file.
            var_name: The complete parameter name.

        Returns:
            dict: A dictionary containing source file IDs as keys and a dictionary
                with the following structure as values:
                    - "terms": A list of terms (in hours since source file date)
                              needed from the source file.
                    - "step": The step size (in hours) of the source file.
        """
        param, accum = split_var_name(var_name)

        preprocessed_info = self.file_info(file_id)
        current_start = preprocessed_info["start"]

        # Handle accumulation for preprocessed files
        preproc_stop = preprocessed_info["stop"]
        preproc_step = Timedelta(hours=int(preprocessed_info["step"]))
        virtual_stop = preproc_stop + Timedelta(hours=accum if accum else 0)
        virtual_range = range(1, int((virtual_stop - preproc_stop) / preproc_step) + 1)
        virtual_terms = [preproc_stop + preproc_step * i for i in virtual_range]

        source_files_dict = {"geometries": set()}
        for source_file_id in self.files_links_df.loc[param, file_id].split(","):
            source_file_id = source_file_id.strip()
            # Check if we've reached the virtual stop due to accumulation
            if virtual_stop <= current_start:
                break

            source_info = self.file_info(source_file_id)
            source_files_dict[source_file_id] = {
                "terms": [
                    (term - Datetime(source_info["date"])).total_hours
                    for term in source_info["terms"]
                    if (
                        term >= current_start
                        and term in preprocessed_info["terms"] + virtual_terms
                    )
                ],
                "step": int(source_info["step"]),
            }
            current_start = source_info["terms"][-1] + preproc_step

            # Update source file configuration in data_config (for parallelism)
            if source_file_id not in data_config["sources"]:
                data_dict = {}  # Intermediate dictionary for parallelism
                for term in source_info["terms"]:
                    term_int = (term - Datetime(source_info["date"])).total_hours
                    data_dict[term_int] = self.resource_handler(
                        source_file_id, term, None
                    )

                data_config["sources"][source_file_id] = data_dict
            for data in data_config["sources"][source_file_id].values():
                for source in data:
                    source_files_dict["geometries"].add(source["geometry"])

        return source_files_dict
