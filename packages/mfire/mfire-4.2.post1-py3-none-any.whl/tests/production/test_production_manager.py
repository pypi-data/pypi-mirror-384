import shutil
from pathlib import Path
from unittest.mock import patch

import numpy as np

from mfire.production.production_manager import ProductionManager
from mfire.settings import Settings
from mfire.utils.date import Datetime
from mfire.utils.json import JsonFile
from tests.composite.factories import (
    ProductionCompositeFactory,
    RiskComponentCompositeFactory,
    SynthesisComponentCompositeFactory,
)


class TestProductionManager:
    inputs_dir: Path = Path(__file__).parent / "inputs"

    def _copy_files(self, path: Path):
        for filename in [
            "small_conf.json",
            "altitude.nc",
            "field.nc",
            "mask.nc",
            "ds_ff.nc",
            "ds_raf.nc",
            "ds_dd.nc",
            "wwmf.nc",
        ]:
            shutil.copy(self.inputs_dir / filename, path / filename)

    def test_components(self):
        prod_manager = ProductionManager(
            productions=[
                ProductionCompositeFactory(
                    components=2 * [RiskComponentCompositeFactory()]
                    + 2 * [SynthesisComponentCompositeFactory()]
                )
            ]
            + [
                ProductionCompositeFactory(
                    components=3 * [RiskComponentCompositeFactory()]
                    + 4 * [SynthesisComponentCompositeFactory()]
                )
            ]
        )
        assert len(prod_manager.components) == 11

    @patch("mfire.utils.date.Datetime.now")
    def test_compute_single(self, mock_date, tmp_path_cwd, assert_equals_result):
        np.random.seed(42)
        mock_date.return_value = Datetime(2023, 3, 1)
        self._copy_files(tmp_path_cwd)
        manager = ProductionManager.load(filename=tmp_path_cwd / "small_conf.json")

        assert_equals_result(manager.compute_single(manager.productions[0]))

    def test_compute_single_and_not_sorted_components(self):
        """Test the production manager's sorting of results during computation."""
        geo_name = {"id1": "Zone 1", "id2": "Zone 2"}
        production = ProductionCompositeFactory(
            # Text1 is associated to risk and Text2 to synthesis since it
            # will be sorted in production compute method
            compute_factory=lambda: [{"id1": "Text1"}, {"id2": "Text2"}],
            components=[
                SynthesisComponentCompositeFactory(
                    area_name_factory=lambda x: geo_name[x]
                ),
                RiskComponentCompositeFactory(area_name_factory=lambda x: geo_name[x]),
            ],
        )
        result = ProductionManager(productions=[production]).compute_single(production)
        assert result[0][1].Components.Aleas[0].DetailComment == "Text1"
        assert result[1][1].Components.Text[0].SyntText == "Text2"

    def test_compute(self, tmp_path_cwd, assert_equals_result):
        Settings().set(disable_parallel=True)

        self._copy_files(tmp_path_cwd)
        manager = ProductionManager.load(filename=tmp_path_cwd / "small_conf.json")
        manager.compute(nproc=1)

        # On récupère le fichier produit
        output_dir = tmp_path_cwd / "output"
        output_filename = next(
            f for f in output_dir.iterdir() if f.name.startswith("prom_Test_config")
        )

        data = JsonFile(output_filename).load()

        # On pop ce qui retourne l'heure à laquelle PROMETHEE a ete produit.
        data.pop("DateProduction")

        # On va enlever les commentaires detailles (c'est pas le but du module de
        # tester qu'ils sont correct)
        data["Components"]["Aleas"][0].pop("DetailComment")
        data["Components"]["Aleas"][1].pop("DetailComment")

        assert_equals_result(data)
