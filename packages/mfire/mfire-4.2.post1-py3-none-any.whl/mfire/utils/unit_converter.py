import ast
import re
from collections.abc import Iterable
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import pint

import mfire.utils.mfxarray as xr
from mfire.settings import UNITS_TABLES, get_logger

# Logging
LOGGER = get_logger(name="unit_converter", bind="unit_converter")

# Defining pint handler
pint_handler = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
# Loading specific unit for us (and specific conversion rules).
pint_handler.load_definitions(UNITS_TABLES["pint_extension"])


def from_decimal_to_sexagesimal_degree(val: float) -> Tuple[str, int, int, int]:
    """
    Returns an angle threshold expressed in decimal format as sexagesimal degrees
    (sign, degree, minute, second).

    Args:
        val: Threshold of the angle in decimal format.

    Returns:
        Angle threshold in sexagesimal format as a tuple (sign, degree, minute, second).
    """
    sign = "+" if val >= 0 else "-"  # Determine the sign
    absolute_degree = abs(val)
    degree = int(absolute_degree)
    decimal = absolute_degree - degree
    minute = int(decimal * 60)
    second = int((decimal * 60 - minute) * 60)
    return sign, degree, minute, second


def from_decimal_to_sexagesimal_latitude(val: float) -> str:
    """
    Returns a characteristic string of the latitude expressed in sexagesimal form.

    Args:
        val: Threshold of the latitude in decimal.

    Returns:
        Characteristic string of the latitude expressed in sexagesimal form.
    """
    sign, degree, minute, second = from_decimal_to_sexagesimal_degree(val)
    sense = "Sud" if sign == "-" else "Nord"
    latitude = f"{degree:02d}°{minute:02d}'{second:02d}\" {sense}"
    return latitude


def from_decimal_to_sexagesimal_longitude(val: float) -> str:
    """
    Returns a characteristic string of the longitude expressed in sexagesimal format.

    Args:
        val: Threshold of the longitude in decimal.

    Returns:
        Characteristic string of the longitude expressed in sexagesimal format.
    """
    sign, degree, minute, second = from_decimal_to_sexagesimal_degree(val)
    sense = "Ouest" if sign == "-" else "Est"
    longitude = "%02d°%02d'%02d\" %s" % (degree, minute, second, sense)
    return longitude


def from_degree_to_direction(val: float) -> str:
    """
    Returns a string representing the characteristic wind direction based on the wind
    direction expressed in degrees. The wind direction is represented both
    numerically and in cardinal form.

    Args:
        val: Wind direction in degrees.

    Returns:
        String representing the wind direction.
    """
    direction = int((((val + 11.25) // 22.5) * 225) % 3600)  # en dixième de degrés

    translations = {
        0: "Nord",
        225: "NNE",
        450: "NE",
        675: "ENE",
        900: "Est",
        1125: "ESE",
        1350: "SE",
        1575: "SSE",
        1800: "Sud",
        2025: "SSO",
        2250: "SO",
        2475: "OSO",
        2700: "Ouest",
        2925: "ONO",
        3150: "NO",
        3375: "NNO",
    }
    return translations[direction]


ANGLES_DICT = {
    "degreDecimal": {
        "direction": from_degree_to_direction,
        "degreSexagesimal": from_decimal_to_sexagesimal_degree,
    }
}

LAT_LON_DICT = {
    "latDecimal": {"latSexagesimal": from_decimal_to_sexagesimal_latitude},
    "lonDecimal": {"lonSexagesimal": from_decimal_to_sexagesimal_longitude},
}


def from_knots_to_beaufort(
    val: float | Iterable[float],
) -> Optional[float | Iterable[float]]:
    """
    Converts a speed expressed in knots to the Beaufort scale.

    Args:
        val: Speed expressed in knots.

    Returns:
        Speed expressed in the Beaufort scale.
    """
    seuils = [1, 4, 7, 11, 17, 22, 28, 34, 41, 48, 56, 64]
    return np.digitize(val, seuils, right=True)


def from_beaufort_to_description(val: float | Iterable):
    """
    Returns a descriptive term for the Beaufort force passed as a parameter.

    Args:
        val: Speed expressed as a Beaufort force.

    Returns:
        String describing the force.
    """
    if isinstance(val, Iterable):
        return np.vectorize(from_beaufort_to_description)(val)

    translations = {
        0: "Calme",
        1: "Très légère brise",
        2: "Légère brise",
        3: "Petite brise",
        4: "Jolie brise",
        5: "Bonne brise",
        6: "Vent frais",
        7: "Grand vent frais",
        8: "Coup de vent",
        9: "Fort coup de vent",
        10: "Tempête",
        11: "Violente tempête",
        12: "Ouragan",
    }

    try:
        return translations[val]
    except KeyError:
        return "Inconnu"


def from_knots_to_description(val: float | Iterable):
    """
    Provides the description of wind expressed in knots.
    By extension (via pint), it allows for conversions in the metric system.

    Args:
        val: Value of the wind speed expressed in knots.

    Returns:
        Description of the wind speed according to the Beaufort scale.
    """
    return from_beaufort_to_description(from_knots_to_beaufort(val))


# Points defining the knots <-> Beaufort conversion function
beauforts = [0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5]
# Points defining the knots <-> Beaufort conversion function
kts = [0, 0.5, 3.5, 6.5, 10.5, 16.5, 21.5, 27.5, 33.5, 40.5, 47.5, 55.5, 63.5]


def from_kt_to_beaufort(x: float) -> Optional[float]:
    """
    Converts a speed expressed in knots to Beaufort scale. This function provides a
        continuous, piecewise linear conversion where the rounded data matches the
        expected Beaufort threshold.

    Args:
        x: Speed expressed in knots

    Returns:
        Speed expressed in Beaufort.
    """
    try:
        i = next(i for i, kt in enumerate(kts) if x <= kt)
    except StopIteration:
        return None

    return beauforts[i - 1] + (x - kts[i - 1]) * (beauforts[i] - beauforts[i - 1]) / (
        kts[i] - kts[i - 1]
    )


def from_beaufort_to_kt(x: float) -> Optional[float]:
    """
    Converts a speed expressed in Beaufort scale to knots. This function is the
    reciprocal function of `from_kt_to_beaufort`.

    Args:
        x: Speed expressed in Beaufort.

    Returns:
        Speed expressed in knots.
    """
    try:
        i = next(i for i, beaufort in enumerate(beauforts) if x <= beaufort)
    except StopIteration:
        return None

    return kts[i - 1] + (x - beauforts[i - 1]) * (kts[i] - kts[i - 1]) / (
        beauforts[i] - beauforts[i - 1]
    )


SPEED_DICT = {
    "kt": {"B": from_knots_to_beaufort, "description": from_knots_to_description},
    "B": {"kt": from_beaufort_to_kt, "description": from_beaufort_to_description},
}


near_zero = 1000000000 * np.finfo(np.float64).eps
palmer_a = np.log10(200)
palmer_b = 1.6
palmer_c = np.log10(3600000)


def from_kg_per_m2_per_second_to_dbz(
    x: float | np.ndarray, a: float = palmer_a, b: float = palmer_b, c: float = palmer_c
) -> np.ndarray:
    """
    Converts a precipitation rate to radar reflectivity using the Marshall-Palmer
    relationship.

    Args:
        x: Precipitation rate expressed in kg/m^2/s.
        a: Coefficient 'a' of the Marshall-Palmer relationship.
        b: Coefficient 'b' of the Marshall-Palmer relationship.
        c: Coefficient 'c' of the Marshall-Palmer relationship.

    Returns:
        Reflectivity expressed in dBZ.
    """

    # Temporarily ignore divide-by-zero warnings
    save_settings = np.seterr(divide="ignore")

    try:
        x = np.where(x > near_zero, x, near_zero)
        z = np.where(x > near_zero, 10 * (a + b * (np.log10(x) + c)), 0)
    finally:
        # Restore the original error settings
        np.seterr(**save_settings)
    return z


def from_dbz_to_kg_per_m2_per_second(
    x: float | np.ndarray, a: float = 200.0, b: float = 1.6
) -> float:
    """
    Converts radar reflectivity to precipitation rate using the Marshall-Palmer
    relationship.

    Args:
        x: Reflectivity expressed in dBZ.
        a: Coefficient 'a' of the Marshall-Palmer relationship (default a=200).
        b: Coefficient 'b' of the Marshall-Palmer relationship (default b=1.6).

    Returns:
        Precipitation rate expressed in kg/m^2/s.
    """

    return ((10 ** (x / 10.0)) / a) ** (1 / b) / 3600000.0


kg_m2s = "kg/m2s"
RADAR_DICT = {
    "dBZ": {kg_m2s: from_dbz_to_kg_per_m2_per_second},
    kg_m2s: {"dBZ": from_kg_per_m2_per_second_to_dbz},
}


# Conversion de codes temps sensible
# Dataframe contenant les code WWMF et les code W1
DF_WWMF_TO_W1 = pd.read_csv(UNITS_TABLES["wwmf_w1"], converters={2: ast.literal_eval})

W1_TO_WWMF = [
    (-1, "Inconnu", -1, "Inconnu"),
    (0, "RAS", 0, "Clair"),
    (1, "Brume ou brouillard peu dense", 31, "Brume/brouillard"),
    (2, "Brouillard dense par place", 32, "Brouillard"),
    (3, "Brouillard dense généralisé", 33, "Brouillard dense"),
    (4, "Brume ou brouillard givrant peu dense", 38, "Brouillard givrant"),
    (5, "Brouillard givrant dense par place", 38, "Brouillard givrant"),
    (6, "Brouillard givrant dense généralisé", 39, "Brouillard dense givrant"),
    (7, "Bruine", 40, "Bruine"),
    (8, "Bruine ou pluie verglaçante", 59, "Pluie verglaçante"),
    (9, "Pluie faible par place", 51, "Pluie faible"),
    (10, "Pluie faible ou modérée généralisée", 52, "Pluie modérée"),
    (11, "Pluie forte généralisée", 53, "Pluie forte"),
    (12, "Pluie localement orageuse", 53, "Pluie forte"),
    (13, "Neige faible par place", 61, "Neige faible"),
    (14, "Pluie et neige mêlées", 58, "Pluie et neige mêlées"),
    (15, "Neige collante", -1, "Inconnu"),
    (16, "Neige faible ou modérée généralisée", 62, "Neige modérée"),
    (17, "Neige forte généralisée", 63, "Neige forte"),
    (18, "Rares averses de pluie", 71, "Rares averses"),
    (19, "Averses de pluie", 70, "Averses"),
    (20, "Averses de pluie et neige mêlées", 77, "Averses de pluie et neige mêlées"),
    (21, "Rares averses de neige", 81, "Rares averses de neige"),
    (22, "Averses de neige", 80, "Averses de neige"),
    (23, "Averses de grêle", 85, "Averses de grêle"),
    (24, "Orages possibles", 91, "Orages possibles"),
    (25, "Orages probables", 93, "Orages avec pluie"),
    (26, "Violents orages possibles", 99, "Orages violents"),
    (27, "Violents orages probables", 99, "Orages violents"),
    (28, "Orages de grêle possibles", 98, "Orages avec grêle"),
    (29, "Orages de grêle probables", 98, "Orages avec grêle"),
    (30, "Averses sur le relief", -1, "Inconnu"),
    (31, "Orages sur le relief", -1, "Inconnu"),
    (32, "Averses localement orageuses", 92, "Averses orageuses"),
    (33, "Bancs de brouillard en plaine", -1, "Inconnu"),
]


def from_w1_to_wwmf(
    w1: float | Iterable | xr.DataArray,
) -> float | Iterable | xr.DataArray:
    """
    Convert W1 code to WWMF code.

    Args:
        w1: W1 code to be converted.

    Returns:
        Converted WWMF code.
    """

    # Check the type of the input W1 code.
    if isinstance(w1, xr.DataArray):
        # If the input W1 code is a xr.DataArray, convert each element of the array.
        result = w1.where(w1.isnull(), 0)
        for code in np.unique(w1):
            if not np.isnan(code):
                result = result.where(w1 != code, from_w1_to_wwmf(code))
        result.attrs["units"] = "wwmf"
        return result
    if isinstance(w1, Iterable):
        # If the input W1 code is an iterable, convert each element of the iterable.
        return [from_w1_to_wwmf(code) for code in w1]
    if np.isnan(w1):
        # If the input W1 code is NaN, return NaN.
        return np.nan

    # Find the corresponding WWMF code based on the input W1 code.
    try:
        return next(
            output_code
            for input_code, _, output_code, _ in W1_TO_WWMF
            if input_code == w1
        )
    except StopIteration:
        LOGGER.error(f"Invalid W1 code given: {w1}")
        return -1


def from_wwmf_to_w1(wwmf: int | Iterable) -> int | Iterable:
    """
    Converts WWMF code to W1 code.

    Args:
        wwmf: WWMF code to be converted.

    Returns:
        Converted W1 code.
    """

    if not isinstance(wwmf, Iterable):
        wwmf = [wwmf]

    w1_code = []  # Initialize an empty list to store the W1 codes

    for x in wwmf:
        # Check if the WwMF code exists in the "Code WWMF" column of the DF_WWMF_TO_W1
        # DataFrame
        if x not in DF_WWMF_TO_W1["Code WWMF"].values:
            LOGGER.error(f"We did not find the translation for this code {x}")

        # Retrieve the corresponding W1 code from the "Code W1" column of DF_WWMF_TO_W1
        # DataFrame
        else:
            w1_code += DF_WWMF_TO_W1.loc[
                DF_WWMF_TO_W1["Code WWMF"] == x, "Code W1"
            ].to_list()[0]

    # Remove any duplicate W1 codes by converting the list into a set and then back
    # into a list
    w1_code = list(set(w1_code))

    return w1_code


WWMF_DICT = {
    "w1": {"wwmf": from_w1_to_wwmf},  # Theoriquement on a pas ce sens la
    "wwmf": {"w1": from_wwmf_to_w1},
}

# Conversion dictionary
CONVERT_DICT = {**RADAR_DICT, **SPEED_DICT, **ANGLES_DICT, **LAT_LON_DICT, **WWMF_DICT}

# Both are needed to go out of pint if needed (or to specify the context)
not_pint_unit = [
    "B",
    "description",
    "dBZ",
    "direction",
    "degreSexagesimal",
    "latSexagesimal",
    "lonSexagesimal",
    "wwmf",
    "w1",
]
contextual_unit = [
    "kg/m^2",
    "kg/m2",
    "kg m**-2",
    "kg/m^2/s",
    "kg/m2/s",
    kg_m2s,
    "kg m**-2 s**-1",
]


def pint_converter(
    input_value: float | xr.DataArray, input_unit: str, output_unit: str, *context
) -> float | xr.DataArray:
    """
    Convert a threshold from one unit to another using the pint library.

    Args:
        input_value: Value to be converted.
        input_unit: The unit of the input threshold.
        output_unit: The desired unit for the conversion.
        *context: Additional context arguments to be passed to the pint library.

    Returns:
        float or xr.DataArray: The converted threshold.

    Notes:
        This function handles a specific issue with the '%' symbol in the pint library
        where it triggers an AttributeError. This issue is currently unsolved (#429).
    """

    # Very specific case to handle '%' symbol
    # Unsolved issue #429 in the pint library :
    # it triggers a AttributeError: 'NoneType' object has no attribute 'evaluate'
    if input_unit == "%":
        input_unit = "percent"
    if output_unit == "%":
        output_unit = "percent"

    th = pint_handler(input_unit) * input_value
    if isinstance(th, xr.DataArray):
        th.values = th.data.to(output_unit, *context).m
        th.attrs["units"] = output_unit
        return th
    return th.to(output_unit, *context).m


def find_input_units(
    input_value: float | xr.DataArray, input_units: str, output_units: str
) -> Tuple[Optional[float | xr.DataArray], Optional[str]]:
    """
    Try to find an adapted input unit for given output unit

    Args:
        input_value: Input value to be converted.
        input_units: The current units of the input threshold.
        output_units: The desired units for the output threshold.

    Returns:
        The converted value and its corresponding input_unit, or (None, None) if
        conversion fails.
    """
    for pos, val in CONVERT_DICT.items():
        if output_units in val:
            try:
                return pint_converter(input_value, input_units, pos), pos
            except AttributeError:
                LOGGER.error(f"Impossible to convert {input_units} to {pos}")
    return None, None


def find_output_units(
    input_value: float | xr.DataArray, input_units: str, output_units: str
):
    """
    Try to find an adapted input unit for given output unit

    Args:
        input_value: Input threshold to be converted.
        input_units: The current input_unit of the input threshold.
        output_units: The desired input_unit for the output threshold.

    Returns:
        The converted threshold and its corresponding input_unit, or (None, None) if
        conversion fails.
    """
    for pos in CONVERT_DICT[input_units]:
        try:
            return pint_converter(input_value, output_units, pos), pos
        except AttributeError:
            LOGGER.error(f"Impossible to convert {output_units} to {pos}")

    return None, None


CONTEXTS = {
    "precipitation": (
        r"^tp$",
        r"[P|p]recipitation",
        r"rprate",
        r"PRECIP\d*__SOL",
        r"EAU\d*__SOL",
    ),
    "snow": (r"[S|s]no[w|m]", r"p3099", r"NEIPOT\d*__SOL"),
}


def get_unit_context(name: str) -> Optional[str]:
    """Returns the context associated to a list of parameter's names.

    Args:
        name: List of possible parameter's name.

    Returns:
        str: Context name associated to the given names. None
            if no context found.
    """
    for context, patterns in CONTEXTS.items():
        for pattern in patterns:
            reg = re.compile(pattern=pattern)
            if reg.search(name):
                return context
    return None


def unit_conversion(
    input_value: Tuple[float, str] | xr.DataArray,
    output_units: str,
    context: Optional[str] = None,
) -> float | xr.DataArray:
    """
    Main function for conversion.

    Args:
        input_value: Either a tuple containing the value to convert and the unit or the
            DataArray
        output_units: Output units.
        context: Possible context for DataArray.

    Returns:
        The input_value converted.

    Raises:
        ValueError: Raised when conversion failed.
    """
    is_da = isinstance(input_value, xr.DataArray)
    if is_da:
        input_units = input_value.units
    else:
        input_value, input_units = input_value

    if input_units == output_units:
        return input_value

    try:
        if input_units in not_pint_unit or output_units in not_pint_unit:
            if input_units not in CONVERT_DICT:
                input_value, input_units = find_input_units(
                    input_value, input_units, output_units
                )
            if output_units not in CONVERT_DICT[input_units]:
                transitory_thr, transitory_out_units = find_output_units(
                    input_value, input_units, output_units
                )
                return pint_converter(
                    transitory_thr, transitory_out_units, output_units
                )
            return CONVERT_DICT[input_units][output_units](input_value)

        if context is None and is_da:
            context = get_unit_context(str(input_value.name))

        if context is not None and (
            input_units in contextual_unit or output_units in contextual_unit
        ):
            return pint_converter(input_value, input_units, output_units, context)
        return pint_converter(input_value, input_units, output_units)

    except Exception as excpt:
        raise ValueError(
            f"Error when trying to convert units with input_value={input_value}, "
            f"input units={input_units} and output_units={output_units}."
        ) from excpt
