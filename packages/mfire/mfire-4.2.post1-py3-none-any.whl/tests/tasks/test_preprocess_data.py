import os
import shutil
import tarfile
from pathlib import Path

import pytest

from mfire.settings.settings import Settings
from mfire.tasks import preprocess_data


class TestPreprocessData:
    inputs_dir: Path = Path(__file__).parent / "inputs" / "preprocess_data"

    @pytest.mark.validation
    @pytest.mark.parametrize("rules", ["psym"])
    def test_preprocess_data(self, rules, tmp_path_cwd, assert_equals_file):
        os.makedirs(Settings().config_filename.parent, exist_ok=True)
        shutil.copy(
            self.inputs_dir / f"data_task_config_{rules}.json",
            Settings().data_config_filename,
        )
        with tarfile.open(self.inputs_dir / f"data_{rules}.tgz") as tar_file:
            tar_file.extractall(tmp_path_cwd)
        preprocess_data.main([])

        filenames = [
            "DD__HAUTEUR10.0006_0048_0001",
            "DD__HAUTEUR10.0051_0096_0003",
            "EAU1__SOL.0006_0048_0001",
            "EAU3__SOL.0006_0048_0001",
            "EAU6__SOL.0006_0048_0001",
            "EAU24__SOL.0006_0048_0001",
            "EAU__SOL.0006_0048_0001",
            "EAU__SOL.0051_0096_0003",
            "FF__HAUTEUR10.0006_0048_0001",
            "FF__HAUTEUR10.0051_0096_0003",
            "LPN__SOL.0006_0048_0001",
            "LPN__SOL.0051_0096_0003",
            "NEIPOT1__SOL.0006_0048_0001",
            "NEIPOT6__SOL.0006_0048_0001",
            "NEIPOT24__SOL.0006_0048_0001",
            "NEIPOT__SOL.0006_0048_0001",
            "NEIPOT__SOL.0051_0096_0003",
            "PRECIP__SOL.0006_0048_0001",
            "PRECIP__SOL.0051_0096_0003",
            "RAF__HAUTEUR10.0006_0048_0001",
            "RAF__HAUTEUR10.0051_0096_0003",
            "T__HAUTEUR2.0006_0048_0001",
            "T__HAUTEUR2.0051_0096_0003",
            "WWMF__SOL.0006_0048_0001",
            "WWMF__SOL.0051_0096_0003",
        ]

        for filename in filenames:
            path = Path("data/20230401T0000/promethee/FRANXL1S100") / (
                f"{filename}.netcdf"
            )
            assert path.exists(), f"{filename} was not computed"
            assert_equals_file(path)
