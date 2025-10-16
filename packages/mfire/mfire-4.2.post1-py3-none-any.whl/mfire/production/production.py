"""Gestion du fichier de sortie via l'objet OutputProduction"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import ConfigDict, field_validator

from mfire.composite.base import BaseModel
from mfire.composite.serialized_types import s_datetime
from mfire.production.component import CDPComponents
from mfire.settings import get_logger
from mfire.utils import MD5
from mfire.utils.date import Datetime
from mfire.utils.json import JsonFile

LOGGER = get_logger(name="output.production.mod", bind="production.base")


class CDPProduction(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    ProductionId: str
    ProductionName: str
    CustomerId: Optional[str] = None
    CustomerName: Optional[str] = None
    DateBulletin: s_datetime
    DateProduction: s_datetime
    DateConfiguration: s_datetime
    Components: CDPComponents

    @field_validator(
        "DateBulletin", "DateProduction", "DateConfiguration", mode="before"
    )
    def init_dates(cls, v: str) -> Datetime:
        """
        Validates the dates and converts them to `Datetime` objects.

        Args:
            v: The date string.

        Returns:
            Datetime: The `Datetime` object.
        """
        return Datetime(v)

    @field_validator("CustomerId", "CustomerName", mode="before")
    def init_customer(cls, v: str) -> str:
        """
        Validates the customer ID and name, and returns "unknown" if they are None.

        Args:
            v: The customer ID or name.

        Returns:
            str: The customer ID or name, or "unknown" if it is None.
        """
        return v or "unknown"

    @property
    def hash(self) -> str:
        """Hash of the object

        Returns:
            str: hash
        """
        return MD5(obj=self.model_dump()).hash

    def dump(self, dump_dir: Path) -> Optional[Path]:
        """
        Dumps self to a JSON file.

        Args:
            dump_dir: Working directory where to dump

        Returns:
            Path of the created file if success otherwise None
        """
        filename = dump_dir / f"prom_{self.ProductionId}_{self.hash}.json"
        filename.parent.mkdir(parents=True, exist_ok=True)
        JsonFile(filename).dump(self.model_dump(exclude_none=True))
        if filename.is_file():
            return filename

        LOGGER.error(f"Failed to dump {filename}.")
        return None

    @classmethod
    def concat(cls, productions: List[CDPProduction]) -> Optional[CDPProduction]:
        """
        Concatenates a list of CDP productions.

        Args:
            productions: The list of CDP productions to concatenate.

        Returns:
            The concatenated CDP production, or `None` if the list is empty.
        """
        if len(productions) == 0:
            return None
        production = productions.pop(0)
        for other_production in productions:
            production += other_production
        return production

    def __add__(self, other: CDPProduction) -> CDPProduction:
        return CDPProduction(
            ProductionId=self.ProductionId,
            ProductionName=self.ProductionName,
            CustomerId=self.CustomerId,
            CustomerName=self.CustomerName,
            DateBulletin=self.DateBulletin,
            DateProduction=self.DateProduction,
            DateConfiguration=self.DateConfiguration,
            Components=self.Components + other.Components,
        )
