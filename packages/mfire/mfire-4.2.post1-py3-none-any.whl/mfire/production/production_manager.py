from __future__ import annotations

import tarfile
from collections import defaultdict
from pathlib import Path
from typing import List, Optional, Tuple

from mfire.composite.base import BaseModel
from mfire.composite.component import AbstractComponentComposite
from mfire.composite.production import ProductionComposite
from mfire.production.adapter import CDPAdapter
from mfire.production.production import CDPProduction
from mfire.settings import Settings, get_logger
from mfire.utils import Tasks
from mfire.utils.json import JsonFile

LOGGER = get_logger(name="production.mod", bind="production")


class ProductionManager(BaseModel):
    """
    This class manages the implementation of promethee products by
    loading the metronome configuration file.
    """

    productions: List[ProductionComposite]

    @property
    def components(self) -> List[AbstractComponentComposite]:
        components = []
        for production in self.productions:
            components.extend(production.components)
        return components

    @classmethod
    def load(cls, filename: Path) -> ProductionManager:
        config = JsonFile(filename).load()
        if isinstance(config, list):
            return cls(productions=config)
        if isinstance(config, dict):
            return cls(productions=list(config.values()))
        LOGGER.error(
            "Failed to retrieve productions from configuration file. "
            "JsonFile does not contain objects of type list or dict."
        )
        return cls(productions=[])

    @staticmethod
    def compute_single(
        production: ProductionComposite,
    ) -> List[Tuple[str, CDPProduction]]:
        """
        Computes a single risk_component, produces the text associated with it and
        export it to the corresponding output model.

        Args:
            production: production to compute.

        Returns:
            BaseOutputProduction: Final data of the computation.
        """
        result, texts = [], production.compute()
        for component, text in zip(production.sorted_components, texts):
            if text is None:
                result.append((production.id, None))
                continue

            adapter = CDPAdapter(component=component, texts=text)
            result.append((production.id, adapter.compute()))

        return result

    @staticmethod
    def concat_and_dump(
        production_id: str, productions: List[CDPProduction]
    ) -> Optional[Path]:
        if not productions:
            LOGGER.warning("Productions empty or None", production_id=production_id)
            return None
        LOGGER.debug("Concat starting", production_id=production_id)
        concat_production = CDPProduction.concat(productions)
        LOGGER.debug("Concat done", production_id=production_id)
        LOGGER.debug("Dumping starting", production_id=production_id)
        filename = concat_production.dump(Settings().output_dirname)
        LOGGER.debug("Dumping done", production_id=production_id)
        return filename

    def compute(self, nproc: int = 1):
        """
        Computes components, related texts and exports the data

        Args:
            nproc: Numbers of CPU to use. Defaults to 1.
        """

        productions_filenames = []

        result = defaultdict(lambda: [])

        settings = Settings()

        def append_to_result(production_result: List[Tuple[str, CDPProduction]]):
            """callback function to append a value to the data dict.

            Args:
                production_result: Key-Value pair to add to the data dict.
            """
            for component_result in production_result:
                component_id, component_text = component_result
                if component_text is not None:
                    result[component_id].append(component_text)

        tasks = Tasks(nproc)
        sorted_prods = sorted(self.productions, key=lambda p: p.sort, reverse=True)
        for production in sorted_prods:
            tasks.append(
                self.compute_single,
                task_name=production.name,
                args=(production,),
                callback=append_to_result,
            )

        tasks.run(name="component", timeout=settings.timeout * 1.5)
        tasks.clean()
        LOGGER.debug("Step 1 (multiproc) done")

        # step 2: concatenating and dumping results
        LOGGER.debug("Step 2 (multiproc) starting")
        for production_id, productions_list in result.items():
            tasks.append(
                self.concat_and_dump,
                task_name=production_id,
                args=(production_id, productions_list),
                callback=productions_filenames.append,
            )
        tasks.run(name="production", timeout=settings.timeout // 2)
        LOGGER.debug("Step 2 (multiproc) done.")

        # step 3 : archiving all the results in a single tar file
        LOGGER.debug("Step 3 starting")

        archive_name = settings.output_archive_filename
        with tarfile.open(archive_name, "w:gz") as tar:
            for filename in productions_filenames:
                if filename is None:
                    continue
                # On ajoute le fichier en utilisant son path global
                # Par contre on lui donne le nom local
                tar.add(filename.absolute(), arcname=filename.name)
        LOGGER.debug("Step 3 done")


__all__ = ["ProductionManager"]
