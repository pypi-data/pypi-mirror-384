from typing import Dict, List, Tuple

from mfire.configuration.rules import Rules
from mfire.settings import get_logger
from mfire.utils import mfxarray as xr
from mfire.utils import xr as xr_utils
from mfire.utils.exception import ConfigurationError, GribError

# Logging
LOGGER = get_logger(name=__name__)


grib_param_dtypes: dict = {
    "discipline": int,
    "parameterCategory": int,
    "productDefinitionTemplateNumber": int,
    "parameterNumber": int,
    "typeOfFirstFixedSurface": str,
    "level": int,
    "typeOfStatisticalProcessing": int,
    "derivedForecast": int,
    "percentileValue": int,
    "scaledValueOfLowerLimit": int,
    "scaledValueOfUpperLimit": int,
    "lengthOfTimeRange": int,
    "units": str,
}
prefiltering_condition: dict = {"PrometheeTimeRangeFromStep": bool}
mandatory_grib_param: list = [
    "subCentre",
    "dataTime",
    "name",
    "units",
    "startStep",
    "endStep",
    "stepRange",
]
optional_grib_param: list = ["dtype"]


def grib_params(rules: Rules, param: str, model: str) -> Dict[str, str]:
    """
    Retrieves GRIB parameter information for a specific rule,parameter and model.

    This method extracts a dictionary containing key-value pairs representing the
    GRIB parameter information associated with the provided `grib_param` and
    `model_name`. The parameter and model names should follow the Promethee standard
    defined in the 'RULES' CSV configuration file.

    Args:
        rules: to get  RULES csv standard
        param: Param's name following the Promethee standard
        model: Model's name following the Promethee standard

    Returns:
        Dict[str, str]: A dictionary containing key-value pairs of extracted GRIB
            parameter information, or an empty dictionary if information is not
            found.
    """
    try:
        # Select data for the specific grib_param and model_name
        return rules.grib_param_df.loc[(param, model)].dropna().to_dict()
    except KeyError:
        # Handle case where specific combination is not found
        LOGGER.warning(
            f"Combination ({param}, {model}) not found in grib_param_df. "
            f"Model 'default' is used to retrieve '{param}'."
        )
        return rules.grib_param_df.loc[(param, "default")].dropna().to_dict()


def backend_kwargs(
    rules: Rules, param: str, model: str
) -> Dict[str, List[str] | Dict[str, str] | str]:
    """
    Constructs the core backend keyword arguments dictionary for the cfgrib engine.

    This method retrieves the necessary configuration information from the internal
    GRIB parameter DataFrame and constructs a dictionary containing the core
    keyword arguments required by the `cfgrib` engine.

    Args:
        rules: Rules to consider
        param: Name of the GRIB parameter following the Promethee standard.
        model: The name of the model following the Promethee standard.

    Returns:
        Dictionary containing the core backend keyword arguments for the cfgrib engine.

    Raises:
        ConfigurationError: raised when grib param key not referenced.
    """

    raw_dico = grib_params(rules, param=param, model=model)
    # Extract and validate parameter keys and values
    param_keys = {}
    prefiltering_keys = {}
    for key, value in raw_dico.items():
        if key in optional_grib_param:
            continue
        if key in grib_param_dtypes:
            value_type = grib_param_dtypes[key]
            param_keys[key] = value_type(value)
        elif key in prefiltering_condition:
            value_type = prefiltering_condition[key]
            prefiltering_keys[key] = value_type(value)
        else:
            raise ConfigurationError(
                f"Grib param key '{key}' not referenced in the grib_param_dtypes"
                f" or in prefilteting condition"
            )

    return {
        "read_keys": list(param_keys.keys()) + mandatory_grib_param,
        "filter_by_keys": param_keys,
        "prefiltering_keys": prefiltering_keys,
        # to avoid ERROR
        "indexpath": "",
    }


def get_param_dtype(rules: Rules, param: str, model: str) -> str:
    """Gives the supposed dtype of a given param in the given model

    Args:
        rules: to get  RULES csv standard
        param: Param's name frollowing the Promethee standard (defined
            in the RULES csv configuration file)
        model: Model name following the Promethee standard (defined in
            the RULES csv standard)

    Returns:
        str: Expected dtype of the variable
    """
    return grib_params(rules, param=param, model=model).get("dtype", "float32")


def grib_filter(
    rules: Rules, param: str, model: str, step: int
) -> Tuple[dict, str, str]:
    """
    Retrieve info to select only one message in a grib.

    Args:
        rules: Rules to consider.
        param: Param's name following the Promethee standard (defined in the RULES csv
            configuration file).
        model: Model name following the Promethee standard (defined in the RULES csv
            standard).
            step: Step size to apply.
        step: Step size to apply.

    Returns:
        Tuple containing respectively a dictionary of filter message info, the expected
        datatype and the expected unit.

    Raises:
        Exception: raised when backend kwargs were not retrieved.
    """
    try:
        backend = backend_kwargs(rules, param, model)
        dtype = get_param_dtype(rules, param, model)
    except Exception:
        LOGGER.error(
            "Failed to retrieve backend_kwargs for (param, model)"
            f" = ({param}, {rules.name}).",
            exc_info=True,
        )
        raise

    # Case of not instant param with lengthOfTimeRange
    if backend["prefiltering_keys"].pop("PrometheeTimeRangeFromStep", None):
        backend["filter_by_keys"]["lengthOfTimeRange"] = int(step)

    units = backend["filter_by_keys"].pop("units", None)
    return backend, dtype, units


def load_single_grib_param(
    rules: Rules, file_id: Tuple, file_conf: dict
) -> Tuple[Tuple, xr.DataArray]:
    """
    Loads and processes a single parameter, step, and grid from a GRIB file. This
    function extracts the specified parameter from the provided GRIB file using
    the `cfgrib` engine.

    Args:
        rules: to get  RULES csv standard
        file_id: Tuple containing unique identification information for the file.
        file_conf: Dictionary containing configuration options for processing the GRIB
            file. It includes the following keys:

            - `grib_filename`: Name of the raw GRIB file.
            - param: Name of the param
            - model: nwp model producer
            - step : duration of the data
            - `grib_attrs`: A dictionary containing attribute
                corrections to be applied to the extracted data.

    Returns:
        A tuple containing:
            - `file_id`: The original `file_id`.
            - `dataarray`: The extracted and processed data as a
              xarray DataArray.

    Raises:
        GribError: raised when the parameter extraction failed.
    """
    dataarray = None
    # la valeur peut etre dans step ou term ( selon version)
    file_conf.setdefault(
        "step",
        file_conf.get(
            "backend_kwargs", {"filter_by_keys": {"lengthOfTimeRange": None}}
        )["filter_by_keys"]["lengthOfTimeRange"],
    )
    grib_args, dtype, units = grib_filter(
        rules, file_conf["param"], file_conf["model"], file_conf["step"]
    )
    file_conf["grib_attrs"] = {"units": units}
    log_kwargs = {
        "file_id": file_id,
        "grib_filename": file_conf["grib_filename"],
        "grib_filter": grib_args.get("filter_by_keys"),
        "func": "load_single_grib_param",
    }
    grib_args.pop("prefiltering_keys")

    try:
        # Open dataarray with cfgrib engine and load data
        with xr.open_dataarray(
            file_conf["grib_filename"], engine="cfgrib", backend_kwargs=grib_args
        ) as tmp_da:
            dataarray = xr_utils.rounding(tmp_da.load())
    except Exception as e:
        raise GribError(f"Failed to extract parameter from file.\n{log_kwargs}") from e

    # Data type casting and handling potential errors
    try:
        if dtype in ["int8", "int16"]:
            dataarray = dataarray.fillna(0)
        dataarray = dataarray.astype(dtype)
    except TypeError as e:
        LOGGER.warning(
            f"Failed to cast dtype {dtype} to the extracted dataarray: {e}",
            **log_kwargs,
        )

    # Apply attribute corrections from configuration
    for attr_key, attr_value in file_conf["grib_attrs"].items():
        # Check if attribute exists and needs correction
        if dataarray.attrs.get(attr_key, "unknown") != attr_value:
            # Handle special case for 'units' attribute with logging
            if attr_key == "units" and attr_value is not None:
                LOGGER.debug(
                    f"Found 'units' = {dataarray.attrs[attr_key]} while '{attr_value}' "
                    f"expected. Changing 'units' to '{attr_value}'.",
                    **log_kwargs,
                )
            dataarray.attrs[attr_key] = attr_value
    # add "valid_time" dimension and set standard attributes
    dataarray = dataarray.expand_dims(dim={"valid_time": 1}, axis=0)
    dataarray["valid_time"] = dataarray.valid_time.assign_attrs(
        {"standard_name": "time", "long_name": "time"}
    )
    # clean some info
    var_to_delete = {"heightAboveGround", "time", "step", "surface"}
    drop_var = set(dataarray.coords).intersection(var_to_delete)
    dataarray = dataarray.drop_vars(list(drop_var))

    return file_id, dataarray
