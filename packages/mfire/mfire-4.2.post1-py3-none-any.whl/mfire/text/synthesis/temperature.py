import re
import string
from typing import ClassVar, Optional

import mfire.utils.mfxarray as xr
from mfire.localisation.area_algebra import compute_iol
from mfire.settings import TEXT_ALGO
from mfire.text.synthesis.builder import SynthesisBuilder
from mfire.text.synthesis.reducer import SynthesisReducer
from mfire.utils.date import Datetime
from mfire.utils.exception import LocalisationError
from mfire.utils.unit_converter import unit_conversion
from mfire.utils.xr import da_set_up


class TemperatureReducer(SynthesisReducer):
    """Classe RiskReducer pour le module temperature.

    La méthode "compute" ici prend en entrée un "WeatherComposite" contenant
    exactement un "field" "temperature".

    Le résumé en sortie a la structure suivante:
    self.reduction = {
        "general": {
            "start": <Datetime: date de début>,
            "stop": <Datetime: date de fin>,
            "tempe": {
                "units": <str: unités>,
                "mini": {
                    "low": <float: valeur basse des minimales>,
                    "high": <float: valeur haute des minimales>,
                },
                "maxi": {
                    "low": <float: valeur basse des maximales>,
                    "high": <float: valeur haute des maximales>,
                }
            }
        },
        "meta": {
            "production_datetime": <Datetime: date de début de production>,
        }
    }
    """

    PARAM_NAME: ClassVar[str] = "tempe"

    def init_reduction(self):
        self.reduction: dict = {
            "general": {
                "start": "",
                "stop": "",
                "tempe": {
                    "units": "",
                    "mini": {"low": None, "high": None},
                    "maxi": {"low": None, "high": None},
                },
            },
            "meta": {"production_datetime": ""},
        }

    def generate_reduction(self, t_da: xr.DataArray, masks_da: xr.DataArray) -> dict:
        """_reduction_

        Args:
            t_da: Temperature data
            masks_da: Mask DataArray

        Returns:
            Reduced information
        """
        reduction = TemperatureSummary(self, t_da, masks_da).generate_reduction()

        return reduction

    def compute_general_reduction(self):
        """Used to populate the "general" section of the reduction data structure

        Generates a reduction for all the zones, for the whole period,
        following the level 2 guidelines
        (http://confluence.meteo.fr/pages/viewpage.action?pageId=333535918):
        * A maximum of 3 descriptive zones
        * a maximum of 3°C per descriptive zone
        """

        start = []
        stop = []

        masks_da = self.parent.geos_descriptive(self.geo_id)

        # computing the temperature dataset and only keeping
        # the useful variable
        # @todo : we could try to convert to int here in order not to
        # round() further down
        param_da = self.weather_data[self.PARAM_NAME].astype("float16")

        # trying to retrieve the Units from the WeatherComposite
        # if it fails, we get the default values
        units = self.parent.units.get(
            self.PARAM_NAME,
            TEXT_ALGO[self.parent.id][self.parent.algorithm]["params"][self.PARAM_NAME][
                "default_units"
            ],
        )
        param_da = unit_conversion(param_da, units)

        # we remove the axis for the risk_component from the list of available
        # descriptive zones, because we dont want an output looking like that :
        # "températures mini de 7 à 9 ° sur toute la zone et de 10 à 12° dans
        # le Sud"
        masks_da = masks_da.drop_sel(id=self.geo_id, errors="ignore")
        masks_da = da_set_up(masks_da, param_da)

        # computing each grid points min and max value for the period
        tn_da = param_da.min("valid_time", keep_attrs=True)
        tx_da = param_da.max("valid_time", keep_attrs=True)

        tn_reduction = self.generate_reduction(tn_da, masks_da)
        tx_reduction = self.generate_reduction(tx_da, masks_da)

        self.reduction["general"]["tempe"]["mini"] = tn_reduction
        self.reduction["general"]["tempe"]["maxi"] = tx_reduction
        self.reduction["general"]["tempe"]["unit"] = units

        start.append(Datetime(param_da.valid_time.min().values))
        stop.append(Datetime(param_da.valid_time.max().values))

        self.reduction["general"]["start"] = min(start)
        self.reduction["general"]["stop"] = min(stop)

    def post_process_general_reduction(self):
        """Does various operations on the reduction dict in order to"""

    def add_metadata(self):
        self.reduction["meta"][
            "production_datetime"
        ] = self.parent.parent.production_datetime

    def compute_reduction(self) -> dict:
        self.init_reduction()
        self.compute_general_reduction()
        self.post_process_general_reduction()
        self.add_metadata()

        return self.reduction


class TemperatureSummary:
    REQUIRED_DENSITY = 0.05  # minimum proportion of points for a valid zone
    MAX_RANGE = 4  # maximum difference of temperature in a descriptive zone (#40117)
    NO_TERM = ""
    has_ignored_values = False  # set to True when a value has been skipped

    def __init__(
        self, reducer: TemperatureReducer, t_da: xr.DataArray, masks: xr.DataArray
    ):
        self.reducer = reducer
        self.t_da = t_da
        self.masks = masks
        self.filtered_mask_da = da_set_up(self.masks, self.t_da)

    @property
    def is_localisation_available(self) -> bool:
        """Tells us whether we will be able to localize the temperature brackets.
        It is in no way an indication of the quality of the localisation available, only
        that it will not crash...

        Returns:
            bool: true if we will be able to localize, false otherwise
        """
        return len(self.masks["id"]) > 0

    def get_best_zone(self, da: xr.DataArray) -> string:
        """Finds the zone most corresponding to the xr.DataArray da

        Args:
            da: temperatures for which we find to find a best matching zone

        Returns:
            Name of the zone (the 'areaName' of its corresponding mask)

        Raises:
            LocalisationError: when iol AND iou fail
        """

        # compute_IoU computes its score by making the sum of all the values >0
        # This obviously does not bode very well with negative temperatures :P
        # we figured that the easiest fix was to set all temperatures to 1
        # so that the IoU would not be influenced by higher values
        bool_da = da.where(da.isnull(), 1)

        iol_da = compute_iol(self.masks, bool_da.squeeze() > 0)[0]

        if iol_da is None:
            raise LocalisationError
        # IoL can return several locations, we only use the first
        localisation_str = iol_da.areaName.values[0]
        # This id cant be used in other brackets localisation
        selected_masks_ids = iol_da.id.data[0]

        # when we have data with a very coarse grid (e.g GLOD025),
        # several zones may have an identical mask,
        # because there is only so many different conbination out of a couple of points.
        # So we remove the mask we've selected from the list of available masks,
        # to avoid phrases looking like "de 10 à 12° sur l'A47 et 13° sur l'A47"
        if selected_masks_ids is not None:
            self.masks = self.masks.drop_sel(id=selected_masks_ids)

        return localisation_str, ""

    def is_zone_valid(self, test_da: xr.DataArray) -> bool:
        """
        Returns whether the number of points in zone_da is high enough compared to the
        number of points in ref_da.

        Args:
            test_da: the zone we want to test.

        Returns:
            True if the number of points is high enough. False otherwise
        """
        return self.zone_coverage(test_da) >= self.REQUIRED_DENSITY

    def get_max_range(self, da: Optional[xr.DataArray] = None) -> int:
        """Returns the difference between the max and min values of a DataArray

        Args:
            da: the DataArray for which we want the range

        Returns:
            Range of values for da
        """
        if da is None:
            da = self.t_da

        return (da.max() - da.min()).data

    def get_t_within_values(
        self, t_da: xr.DataArray, min_val: int, max_val: int
    ) -> xr.DataArray:
        """
        Returns a subset of t_da with the data in the bracket [min_val; max_val[.

        Args:
            t_da: a xr.xr.DataArray containing all the values.
            min_val: lower bound for the accepted value (included).
            max_val: higher bound for the accepted values (excluded).

        Returns:
            The subset of t_da.
        """

        tmp_da = t_da.where(t_da >= min_val).where(t_da < max_val)

        return tmp_da

    def get_best_range(
        self, mini: int, maxi: int, t_range: int = MAX_RANGE
    ) -> xr.DataArray:
        """Returns the best range of t_range values between t_min and t_max

        Args:
            mini: Minimal value.
            maxi: Maximal value.
            t_range: The range of values to find.

        Returns:
            The most representative da or returns None if no not enough values are
            available.
        """

        best_zone = None
        best_score = 0

        while mini <= maxi and mini + t_range <= maxi:
            t_range = min(t_range, maxi - mini)  # we can't go past maxi !

            tmp_da = self.t_da.where(self.t_da >= mini).where(
                self.t_da <= mini + t_range
            )

            score = self.zone_coverage(tmp_da)

            if score > best_score and self.is_zone_valid(tmp_da):
                best_score = score
                best_zone = tmp_da

            mini += 1

        return best_zone

    def zone_coverage(self, zone_da: xr.DataArray) -> float:
        """Computes the proportion of ref_da points present in zone_da

        Args:
            zone_da: zone to score

        Returns:
            float: _description_
        """
        return float(zone_da.count() / self.t_da.count())

    def get_higher_range(self) -> xr.DataArray:
        """
        Finds the DataArray containing the highest range of °c that is representative
        enough.

        Returns:
            Higher range DataArray.
        """

        t_max = self.t_da.max().data
        original_t_max = t_max
        t_min = self.t_da.min().data
        max_da = self.t_da.where(self.t_da > t_max - self.MAX_RANGE)

        # making sure the da does not consist manly of extreme, isolated values
        while not self.is_zone_valid(max_da) and t_max > t_min:
            t_max -= 1
            max_da = self.t_da.where(self.t_da > t_max - self.MAX_RANGE)
            max_da = max_da.where(max_da <= t_max)

        # if at least one °C is skipped in the end phrase,
        # we need to use the term "globally"
        if original_t_max != t_max:
            self.has_ignored_values = True

        return max_da

    def get_lower_range(
        self,
        t_min: Optional[xr.DataArray] = None,
        t_max: Optional[xr.DataArray] = None,
        t_range: int = MAX_RANGE,
    ) -> xr.DataArray:
        """
        Finds the DataArray containing the lowest range of °c that is representative
        enough

        Args:
            t_min: Minimal values to consider.
            t_max: Maximal values to consider.
            t_range: Range of the values to return. Defaults to MAX_RANGE.

        Returns:
            Lower range xr.DataArray.
        """

        if t_max is None:
            t_max = self.t_da.max()
        if t_min is None:
            t_min = self.t_da.min()

        original_t_min = t_min

        # we ignore da consisting mainly of extreme isolated values
        is_zone_valid = False
        min_da = None

        while (not is_zone_valid) and t_max > t_min:
            # we dont want range to accidentaly overlap
            t_range = min(t_range, t_max - t_min)

            min_da = self.t_da.where(self.t_da >= t_min)
            min_da = min_da.where(min_da < t_min + t_range)

            is_zone_valid = self.is_zone_valid(min_da)
            if not is_zone_valid:
                t_min += 1

        # if at least one °C is skipped in the end phrase,
        # we need to use the term "globally"
        if original_t_min != t_min:
            self.has_ignored_values = True

        return min_da

    def find_best_brackets(self) -> list:
        """finds the DataArray(s) that best divide the temperature in a maximum of 3
        brackets of MAX_RANGE values each

        Returns:
            list: list containing the das representing the brackets, in the
            following order : higher values, lower values, mid values
        """

        brackets = []
        t_min = self.t_da.min()

        # No matter how many zones we'll describe, there will always be
        # at least one. We arbitrarily decide to start with the highest values
        max_t_da = self.get_higher_range()
        brackets.append(max_t_da)

        # we don't want to have overlapping values in the following descriptions
        t_max = max_t_da.min() - 1

        if t_max - t_min <= self.MAX_RANGE:
            t_range = t_max - t_min
        else:
            t_range = self.MAX_RANGE

        # Making sure there are enough values left for another bracket
        if t_range > 0:
            min_t_da = self.get_lower_range(t_max=t_max.data)

            if min_t_da.count() == 0:
                return brackets

            brackets.append(min_t_da)

        return brackets

    def _get_overall_term(self, brackets, rounded_min, rounded_max):
        if self.has_ignored_values:
            if len(brackets) == 1:
                # term to use when some values are skipped and there
                # is only one interval
                return (
                    self.reducer._("proche")
                    if rounded_min == rounded_max
                    else self.reducer._("environ")
                )
            # term to use when some values are not described
            return self.reducer._("globalement de")

        # 1er cas : "de 2 à 4 °C sur xxx, jusqu'à 8 à 10 dans le YYY"
        # de 1 à YYY, jusqu'à 12 sur le XXX"
        # "de 5 à 8 °C dans le ZZZ"
        # 2eme cas : only one interval and only one value in it : "1°C dans le ZZZ"
        return (
            # default term used when no value is skipped and there are two intervals
            self.reducer._("de")
            if len(brackets) == 2 or rounded_min != rounded_max
            else self.NO_TERM
        )

    def generate_reduction(self) -> dict:
        """
        Generates a dict containing the data used to best summarize
        the temperature field t_da with these constraints
        * there can only be a maximum 3 zones used in the description
        * there can only be a maximum of MAX_RANGE temperature difference
          in a descriptive zone

        Returns:
            Reduced information
        """
        if not self.is_localisation_available:
            return {
                "high": {
                    "min": int(self.t_da.min().data),
                    "max": int(self.t_da.max().data),
                    "overall": "",
                }
            }

        reduction = {}
        brackets_name = ["high", "low"]

        brackets = self.find_best_brackets()

        for i, bracket in enumerate(brackets):
            rounded_min = int(bracket.min().data.round(0))
            rounded_max = int(bracket.max().data.round(0))
            try:
                zone_name, zone_type = self.get_best_zone(bracket)
            except LocalisationError:
                return {
                    "high": {
                        "min": int(self.t_da.min().data),
                        "max": int(self.t_da.max().data),
                        "overall": "",
                    }
                }

            reduction[brackets_name[i]] = {
                "location": zone_name,
                "location_type": zone_type,
                "min": rounded_min,
                "max": rounded_max,
                "overall": self._get_overall_term(brackets, rounded_min, rounded_max),
            }
        return reduction


class TemperatureBuilder(SynthesisBuilder):
    """
    BaseBuilder class that must build texts for temperature
    """

    reducer_class: type = TemperatureReducer

    @property
    def template_name(self) -> str:
        return "temperature"

    def post_process(self):
        """
        Make a post-process operation on the text.
        """
        # pattern used to fix intervals with only one value
        pattern = re.compile(
            r" ([-]{0,1}\d+) " + self._("à") + r" ([-]{0,1}\d+)\u00A0°C"
        )

        # Removes duplicate temperature for intervals with a single value, e.g: "de 12
        # à 12° dans le Vercors" => "12° dans le Vercors
        for match in pattern.finditer(self.text):
            interval_text = match.group(0)
            t1 = match.group(1)
            t2 = match.group(2)
            if t1 == t2:
                self.text = self.text.replace(interval_text, f" {t2}\u00a0°C")

            super().post_process()

    @property
    def template_key(self) -> str:
        """
        Get the template key.

        Returns:
            str: The template key.
        """

        # First iteration, only manages ranges of temperatures.
        # If one description only has a range of 1°C, its template will
        # give us something wonky,like "from 13°C to 13°C" :(
        # On the plus side, the code is really short :D
        tn = self.reduction["general"]["tempe"]["mini"]
        tx = self.reduction["general"]["tempe"]["maxi"]
        return f"P1_Z0_{len(tn)}_MIN_{len(tx)}_MAX"
