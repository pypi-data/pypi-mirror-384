from functools import cached_property
from typing import Dict, List, Optional

from mfire.settings import get_logger
from mfire.text.base.geo import BaseGeo
from mfire.utils.date import Datetime, Timedelta

# Logging
LOGGER = get_logger(name="base_reducer.mod", bind="base_reducer")


class BaseReducer(BaseGeo):
    """Classe de base pour implémenter un wind_reducers.
    Il adopte le design pattern du constructeur:
    - il existe un produit "summary" à construire (ici un dictionnaire)
    - une méthode "reset" qui permet de recommencer le processus de construction
    - un ensemble de méthode qui permettent d'ajouter des caractéristiques au "summary"
    - une méthode "compute" qui exécute l'ensemble des étapes et renvoie le "summary"

    '/!\' Dans les classes héritant de BaseReducer,
    il est impératif de détailler au niveau de cette docstring principale
    le schéma du dictionnaire de résumé issu de la méthode "compute".
    """

    infos: dict = {}
    geo_id: Optional[str] = None
    reduction: Optional[Dict | List[Dict]] = None

    def reset(self):
        super().reset()
        self.reduction = None

    def compute_reduction(self) -> Dict | List[Dict]:
        return {}

    def compute(self) -> Dict | List[Dict]:
        """
        Make computation and returns the reduced data.

        Returns:
            Dict | List[Dict]: Reduced data
        """
        self.reduction = {}
        self.reduction = self.compute_reduction()

        self.post_process()

        return self.reduction

    def post_process(self):
        """Make a post-process operation in the reduction."""

    @cached_property
    def times(self) -> List[Datetime]:
        return [Datetime(d) for d in self.weather_data["valid_time"].to_numpy()]

    @cached_property
    def first_time(self) -> Datetime:
        """Returns the first time of the production.

        Returns:
            First time of production.
        """
        if len(self.times) == 1:
            LOGGER.warning("There is only one valid_time to compute weather text.")
            return self.times[0] - Timedelta(hours=1)
        return self.times[0] - (self.times[1] - self.times[0])
