import os
import shutil
import tarfile
from pathlib import Path

import pytest

from mfire.settings.constants import LANGUAGES
from mfire.settings.settings import Settings
from mfire.tasks import core
from mfire.utils.dict import recursive_format
from mfire.utils.json import JsonFile


class TestCore:
    inputs_dir: Path = Path(__file__).parent / "inputs" / "core"

    @pytest.mark.validation
    @pytest.mark.parametrize("language", LANGUAGES)
    def test_core(self, language, tmp_path_cwd, assert_equals_result):
        Settings().set(timeout=2000)
        os.makedirs(Settings().config_filename.parent)
        shutil.copy(
            self.inputs_dir / "prod_task_config_psym.json",
            tmp_path_cwd / Settings().prod_config_filename,
        )
        with tarfile.open(self.inputs_dir / "data_psym.tgz") as tar:
            tar.extractall(tmp_path_cwd)

        prod_task_config = JsonFile(Settings().prod_config_filename)
        prod_task_result = recursive_format(
            prod_task_config.load(),
            {
                "language": language,
                "altitudes_dirname": str(Settings().altitudes_dirname),
            },
        )
        prod_task_config.dump(prod_task_result)

        core.main(["--disable_random"])
        with tarfile.open("output.tgz") as tar:
            tar.extractall("output")

        result, count = {}, 0
        for filename in Path("output").iterdir():
            content = JsonFile(filename).load()
            content.pop("DateProduction")
            result[filename.name[:23]] = content
            count += 1

        assert_equals_result(result)
        assert count == 4
