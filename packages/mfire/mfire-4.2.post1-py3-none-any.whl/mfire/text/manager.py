from typing import Annotated, Optional
from zoneinfo import ZoneInfo

from pydantic import SkipValidation

from mfire.composite.base import BaseComposite
from mfire.composite.component import (
    RiskComponentComposite,
    SynthesisComponentComposite,
)
from mfire.settings import get_logger
from mfire.text.risk.builder import RiskBuilder
from mfire.text.synthesis.temperature import TemperatureBuilder
from mfire.text.synthesis.weather import WeatherBuilder
from mfire.text.synthesis.wind import WindBuilder

LOGGER = get_logger(name="text_manager.mod", bind="text_manager")


class Manager(BaseComposite):
    """
    Class for dispatching the text generation according to the given risk_component's
    type.
    """

    parent: (
        Annotated[RiskComponentComposite, SkipValidation]
        | Annotated[SynthesisComponentComposite, SkipValidation]
    )
    geo_id: str
    risk_builder: Optional[RiskBuilder] = None

    builders: dict = {
        "risk": RiskBuilder,
        "tempe": TemperatureBuilder,
        "weather": WeatherBuilder,
        "wind": WindBuilder,
    }

    def _compute_synthesis(self) -> str:
        """
        Compute in the case of text synthesis

        Returns:
            str: The computed text synthesis.
        """
        # Add the text title with the date
        zone_info = ZoneInfo(self.time_zone)
        start = max(
            self.parent.period.start, self.parent.production_datetime
        ).astimezone(zone_info)
        stop = self.parent.period.stop.astimezone(zone_info)

        text = self._(
            "DU {start_date} À {start_hour}H AU {stop_date} À {stop_hour}H :"
        ).format(
            start_date=f"{start.weekday_name(self.language)} "
            f"{start.strftime('%d')}".upper(),
            start_hour=start.strftime("%H"),
            stop_date=f"{stop.weekday_name(self.language)} "
            f"{stop.strftime('%d')}".upper(),
            stop_hour=stop.strftime("%H"),
        )
        text += "\n"

        has_checked_one_condition = False
        for weather in self.parent.weathers:
            computed_text = self.builders[weather.id](
                geo_id=self.geo_id, parent=weather
            ).compute()
            if computed_text is not None:
                text += computed_text + "\n"
                has_checked_one_condition = True
        if not has_checked_one_condition:
            text += self._("RAS")

        return text

    def _compute_risk(self) -> str:
        """
        Compute in the case of risk text

        Returns:
            str: The computed risk text.
        """
        self.risk_builder = self.builders["risk"](
            parent=self.parent, geo_id=self.geo_id
        )
        res: str = self.risk_builder.compute()
        return res

    def compute(self) -> str:
        """
        Produces a text according to the given risk_component type.

        Returns:
            Text corresponding to the risk_component and the given geo_id.
        """
        return (
            self._compute_synthesis()
            if isinstance(self.parent, SynthesisComponentComposite)
            else self._compute_risk()
        )
