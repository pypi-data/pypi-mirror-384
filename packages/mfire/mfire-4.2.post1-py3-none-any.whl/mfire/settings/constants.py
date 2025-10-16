from pathlib import Path
from typing import Optional, Sequence

# Global variables
LANGUAGES = ["fr", "en", "es"]

# Paths
CUR_DIR = Path(".")
ROOT_DIR = Path(__file__).absolute().parents[2]
SETTINGS_DIR = Path(__file__).absolute().parent
LOCALE_DIR = Path(__file__).absolute().parents[1] / "locale"

# Rules
RULES_DIR = SETTINGS_DIR / "rules"
RULES_NAMES = tuple(
    d.name for d in RULES_DIR.iterdir() if d.is_dir() and not d.name.startswith("__")
)

# downscaled parameters
# DD added for synthese text
DOWNSCALABLE_PARAMETERS = [
    "PRECIP__SOL",
    "PTYPE__SOL",
    "LPN__SOL",
    "FF__HAUTEUR10",
    "RAF__HAUTEUR10",
    "RISQUE_ORAGE__SOL",
    "T__HAUTEUR2",
    "WWMF__SOL",
    "EAU__SOL",
    "HU__HAUTEUR2",
    "NEIPOT__SOL",
    "DD__HAUTEUR10",
]
DOWNSCALE_SOURCE = "T_AS__HAUTEUR2"
DOWNSCALE_REPLACE = "T__HAUTEUR2"

TEMPLATES_FILENAME = {
    "compass": "compass.json",
    "date": "date.json",
    "period": "period.csv",
    "synonyms": "synonyms.json",
    "wwmf_labels": "wwmf_labels.csv",
    "nebulosity_following_labels": "synthesis/nebulosity_following_labels.csv",
    "risk/ME": "risk/ME.json",
    "risk/snow": "risk/snow.json",
    "risk/rain": "risk/rain.json",
    "risk/monozone": "risk/monozone.csv",
    "risk/multizone": "risk/multizone.json",
    "risk/rep_value_generic": "risk/rep_value.json",
    "risk/rep_value_altitude": "risk/rep_value_altitude.json",
    "risk/rep_value_lpn": "risk/rep_value_lpn.json",
    "synthesis/temperature": "synthesis/temperature.json",
    "synthesis/weather": "synthesis/weather.json",
    "synthesis/wind": "synthesis/wind.json",
}

# Data conf
LOCAL = {
    "gridpoint": "[date:stdvortex]/[block]/[geometry:area]/[term:fmth].[format]",
    "promethee_gridpoint": (
        "[date:stdvortex]/[model]/[geometry:area]/"
        "[param].[begintime:fmth]_[endtime:fmth]_[step:fmth].[format]"
    ),
}

# Units
_units_dir = SETTINGS_DIR / "units"
UNITS_TABLES = {
    "pint_extension": _units_dir / "pint_extension.txt",
    "wwmf_w1": _units_dir / "wwmf_w1_correspondence.csv",
}

# Default altitudes min and max
ALT_MIN = -500
ALT_MAX = 10000

# Default dimensions used
Dimension = Optional[str | Sequence[str]]
SPACE_DIM = ("latitude", "longitude")
TIME_DIM = ("valid_time",)

# RiskLocalisation default values
N_CUTS = 3
GAIN_THRESHOLD = 0.001
