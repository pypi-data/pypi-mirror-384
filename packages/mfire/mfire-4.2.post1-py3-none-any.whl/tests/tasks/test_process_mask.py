import os
import shutil
from pathlib import Path

import pytest

from mfire.settings.constants import LANGUAGES
from mfire.settings.settings import Settings
from mfire.tasks import process_mask
from mfire.tasks.process_mask import create_mask
from mfire.utils import recursive_format
from mfire.utils.json import JsonFile


class TestProcessMask:
    inputs_dir: Path = Path(__file__).parent / "inputs" / "process_mask"

    def test_mask_31(self, tmp_path, assert_equals_file):
        data = JsonFile(self.inputs_dir / "mask_config_31.json").load()
        conf = recursive_format(data, {"output_folder": str(tmp_path)})
        create_mask(conf)
        assert_equals_file(tmp_path / "carre.nc")

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_mask_cei11(self, language, tmp_path, assert_equals_file):
        data = JsonFile(self.inputs_dir / f"mask_config_cei11_{language}.json").load()
        conf = recursive_format(data, {"output_folder": str(tmp_path)})
        create_mask(conf)
        assert_equals_file(tmp_path / "CEI_11.nc")

    @pytest.mark.validation
    def test_process_mask(self, tmp_path_cwd, assert_equals_file):
        os.makedirs(Settings().config_filename.parent)
        mask_config_file = self.inputs_dir / "mask_config_validation.json"
        shutil.copy(mask_config_file, Settings().mask_config_filename)
        process_mask.main([])

        for mask_id in JsonFile(mask_config_file).load().keys():
            assert_equals_file(tmp_path_cwd / "mask" / f"{mask_id}.nc")
