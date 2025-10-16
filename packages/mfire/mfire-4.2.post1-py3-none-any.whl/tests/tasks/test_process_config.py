import os
import shutil
from pathlib import Path

import pytest

from mfire.settings import SETTINGS_DIR
from mfire.settings.settings import Settings
from mfire.tasks import process_config
from mfire.utils.dict import recursive_remove_key, recursive_replace
from mfire.utils.json import JsonFile


class TestProcessConfig:
    inputs_dir: Path = Path(__file__).parent / "inputs" / "process_config"

    @staticmethod
    def generate_config_files(
        rules, conf_file_path: Path, draft_date: str, tmp_path_cwd
    ) -> Path:
        os.makedirs(Settings().config_filename.parent)
        shutil.copy(conf_file_path, Settings().config_filename)
        process_config.main(["-d", draft_date, "-r", rules])

        # We have to change the altitude dir_name and remove configuration_datetime
        # key to be able to compare
        conf_dir_path: Path = tmp_path_cwd / "configs"
        prod_task_config = JsonFile(conf_dir_path / "prod_task_config.json")
        prod_task_result = recursive_replace(
            prod_task_config.load(),
            str(SETTINGS_DIR / "geos" / "altitudes"),
            "altitudes_dirname",
        )
        prod_task_result = recursive_remove_key(
            prod_task_result, "configuration_datetime"
        )
        prod_task_config.dump(prod_task_result)

        return conf_dir_path

    @pytest.mark.validation
    @pytest.mark.parametrize("rules", ["alpha", "psym_archive"])
    def test_process_config(self, rules, tmp_path_cwd, assert_equals_file):
        # Test data, mask and prod conf files generated from small_config.tgz
        conf_dir_path: Path = self.generate_config_files(
            rules, self.inputs_dir / "small_config.tgz", "20230401T070000", tmp_path_cwd
        )

        assert_equals_file(conf_dir_path / "data_task_config.json")
        assert_equals_file(conf_dir_path / "mask_task_config.json")
        assert_equals_file(conf_dir_path / "prod_task_config.json")

    @pytest.mark.validation
    @pytest.mark.parametrize("rules", ["alpha", "psym_archive"])
    def test_process_config_v2(self, rules, tmp_path_cwd, assert_equals_file):
        # Test only prod conf files generated from small_config.tgz.
        # The conf contained in small_config2.tgz has only one period described by:
        #     - start: -8
        #     - stop: 5
        #     - productionTime_until: 9
        # So at the 5am's run, production_time = start_time = stop_time = 5 which
        # matches with valid_time slices in the expected prod_task_config.json.
        conf_dir_path: Path = self.generate_config_files(
            rules,
            self.inputs_dir / "small_config2.tgz",
            "20240425T050000",
            tmp_path_cwd,
        )

        assert_equals_file(conf_dir_path / "prod_task_config.json")
