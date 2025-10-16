import os
from pathlib import Path

import pytest

from mfire.settings import RULES_NAMES, Settings
from mfire.settings.constants import CUR_DIR
from mfire.tasks.CLI import CLI, _get_version
from mfire.utils.date import Datetime


class TestCLI:
    """Teste les arguments passés aux différentes tâches"""

    log_basename: str = "toto.json"

    @pytest.fixture
    def local_working_dir(self, tmp_path_factory: pytest.TempPathFactory) -> Path:
        return tmp_path_factory.mktemp(self.__class__.__name__)

    def log_filename(self, dirname: Path) -> Path:
        return Path(dirname) / self.log_basename

    def test_empty(self):
        args = CLI().parse_args([])
        assert args.alternate_max is None
        assert args.altitudes_dirname is None
        assert args.timeout is None
        assert args.config_filename is None
        assert args.data_config_filename is None
        assert args.data_dirname is None
        assert isinstance(args.draftdate, Datetime)
        assert args.eccodes_definition_path is None
        assert args.experiment is None
        assert args.log_file_level is None
        assert args.log_file_name is None
        assert args.log_level is None
        assert args.mask_config_filename is None
        assert args.mask_dirname is None
        assert args.nproc == os.cpu_count()
        assert args.output_dirname is None
        assert args.prod_config_filename is None
        assert args.rules == RULES_NAMES[0]
        assert args.vapp is None
        assert args.vconf is None
        assert args.version_config_filename is None
        assert args.working_dir is None

        settings = Settings()
        settings_dir = Path(__file__).absolute().parent.parent / "mfire/settings"
        assert settings.altitudes_dirname == settings_dir / "geos/altitudes"
        assert settings.alternate_max == 2
        assert settings.config_filename == CUR_DIR / "configs/global_config.tgz"
        assert (
            settings.mask_config_filename == CUR_DIR / "configs/mask_task_config.json"
        )
        assert (
            settings.data_config_filename == CUR_DIR / "configs/data_task_config.json"
        )
        assert (
            settings.prod_config_filename == CUR_DIR / "configs/prod_task_config.json"
        )
        assert (
            settings.version_config_filename == CUR_DIR / "configs/version_config.json"
        )
        assert settings.data_dirname == CUR_DIR / "data"
        assert settings.mask_dirname == CUR_DIR / "mask"
        assert settings.output_dirname == CUR_DIR / "output"
        assert settings.log_level == "WARNING"
        assert settings.log_file_name is None
        assert settings.log_file_level == "WARNING"
        assert settings.vapp == "promethee"
        assert settings.vconf == "msb"
        assert settings.experiment == "TEST"

        Settings.clean()

    def test_local_working_dir(self, local_working_dir: Path):
        args = CLI().parse_args(f"--working-dir {local_working_dir}".split())
        assert args.alternate_max is None
        assert args.altitudes_dirname is None
        assert args.timeout is None
        assert args.config_filename is None
        assert args.data_config_filename is None
        assert args.data_dirname is None
        assert isinstance(args.draftdate, Datetime)
        assert args.eccodes_definition_path is None
        assert args.experiment is None
        assert args.log_file_level is None
        assert args.log_file_name is None
        assert args.log_level is None
        assert args.mask_config_filename is None
        assert args.mask_dirname is None
        assert args.nproc == os.cpu_count()
        assert args.output_dirname is None
        assert args.prod_config_filename is None
        assert args.rules == RULES_NAMES[0]
        assert args.vapp is None
        assert args.vconf is None
        assert args.version_config_filename is None
        assert args.working_dir == str(local_working_dir)

        config_filename = local_working_dir / "configs/global_config.tgz"
        mask_config_filename = local_working_dir / "configs/mask_task_config.json"
        data_config_filename = local_working_dir / "configs/data_task_config.json"
        prod_config_filename = local_working_dir / "configs/prod_task_config.json"
        version_config_filename = local_working_dir / "configs/version_config.json"
        data_dirname = local_working_dir / "data"
        mask_dirname = local_working_dir / "mask"
        output_dirname = local_working_dir / "output"

        assert os.environ.get("mfire_config_filename") == str(config_filename)
        assert os.environ.get("mfire_mask_config_filename") == str(mask_config_filename)
        assert os.environ.get("mfire_data_config_filename") == str(data_config_filename)
        assert os.environ.get("mfire_prod_config_filename") == str(prod_config_filename)
        assert os.environ.get("mfire_version_config_filename") == str(
            version_config_filename
        )
        assert os.environ.get("mfire_data_dirname") == str(data_dirname)
        assert os.environ.get("mfire_mask_dirname") == str(mask_dirname)
        assert os.environ.get("mfire_output_dirname") == str(output_dirname)

        settings = Settings()
        settings_dir = Path(__file__).absolute().parent.parent / "mfire/settings"
        assert settings.altitudes_dirname == settings_dir / "geos/altitudes"
        assert settings.alternate_max == 2
        assert settings.config_filename == config_filename
        assert settings.mask_config_filename == mask_config_filename
        assert settings.data_config_filename == data_config_filename
        assert settings.prod_config_filename == prod_config_filename
        assert settings.version_config_filename == version_config_filename
        assert settings.data_dirname == data_dirname
        assert settings.mask_dirname == mask_dirname
        assert settings.output_dirname == output_dirname
        assert settings.log_level == "WARNING"
        assert settings.log_file_name is None
        assert settings.log_file_level == "WARNING"
        assert settings.vapp == "promethee"
        assert settings.vconf == "msb"
        assert settings.experiment == "TEST"

        Settings.clean()

    def test_casual_settings(self, local_working_dir: Path):
        config_filename = "my_config.json"
        cmd = (
            f"--working-dir {local_working_dir} --config-filename {config_filename} "
            f"--log-file-name {self.log_filename(local_working_dir)} --log-level INFO "
            "-n 4 --draftdate 20211231T080000 -r psym"
        )
        args = CLI().parse_args(cmd.split())
        assert args.alternate_max is None
        assert args.altitudes_dirname is None
        assert args.timeout is None
        assert args.config_filename == config_filename
        assert args.data_config_filename is None
        assert args.data_dirname is None
        assert args.draftdate == "20211231T080000"
        assert args.eccodes_definition_path is None
        assert args.experiment is None
        assert args.log_file_level is None
        assert args.log_file_name == str(self.log_filename(local_working_dir))
        assert args.log_level == "INFO"
        assert args.mask_config_filename is None
        assert args.mask_dirname is None
        assert args.nproc == 4
        assert args.output_dirname is None
        assert args.prod_config_filename is None
        assert args.rules == "psym"
        assert args.vapp is None
        assert args.vconf is None
        assert args.version_config_filename is None
        assert args.working_dir == str(local_working_dir)

        mask_config_filename = local_working_dir / "configs/mask_task_config.json"
        data_config_filename = local_working_dir / "configs/data_task_config.json"
        prod_config_filename = local_working_dir / "configs/prod_task_config.json"
        version_config_filename = local_working_dir / "configs/version_config.json"
        data_dirname = local_working_dir / "data"
        mask_dirname = local_working_dir / "mask"
        output_dirname = local_working_dir / "output"

        assert os.environ.get("mfire_config_filename") == config_filename
        assert os.environ.get("mfire_mask_config_filename") == str(mask_config_filename)
        assert os.environ.get("mfire_data_config_filename") == str(data_config_filename)
        assert os.environ.get("mfire_prod_config_filename") == str(prod_config_filename)
        assert os.environ.get("mfire_version_config_filename") == str(
            version_config_filename
        )
        assert os.environ.get("mfire_data_dirname") == str(data_dirname)
        assert os.environ.get("mfire_mask_dirname") == str(mask_dirname)
        assert os.environ.get("mfire_output_dirname") == str(output_dirname)
        assert os.environ.get("mfire_log_file_name") == str(
            self.log_filename(local_working_dir)
        )
        assert os.environ.get("mfire_log_level") == "INFO"

        settings = Settings()
        settings_dir = Path(__file__).absolute().parent.parent / "mfire/settings"
        assert settings.altitudes_dirname == settings_dir / "geos/altitudes"
        assert settings.alternate_max == 2
        assert settings.config_filename == Path(config_filename)
        assert settings.mask_config_filename == mask_config_filename
        assert settings.data_config_filename == data_config_filename
        assert settings.prod_config_filename == prod_config_filename
        assert settings.version_config_filename == version_config_filename
        assert settings.data_dirname == data_dirname
        assert settings.mask_dirname == mask_dirname
        assert settings.output_dirname == output_dirname
        assert settings.log_level == "INFO"
        assert settings.log_file_name == self.log_filename(local_working_dir)
        assert settings.log_file_level == "WARNING"
        assert settings.vapp == "promethee"
        assert settings.vconf == "msb"
        assert settings.experiment == "TEST"

        Settings.clean()

    def test_eccodes_definition_path(self):
        args = CLI().parse_args(["-e", "path"])
        assert args.alternate_max is None
        assert args.altitudes_dirname is None
        assert args.timeout is None
        assert args.config_filename is None
        assert args.data_config_filename is None
        assert args.data_dirname is None
        assert isinstance(args.draftdate, Datetime)
        assert args.eccodes_definition_path == "path"
        assert args.experiment is None
        assert args.log_file_level is None
        assert args.log_file_name is None
        assert args.log_level is None
        assert args.mask_config_filename is None
        assert args.mask_dirname is None
        assert args.nproc == os.cpu_count()
        assert args.output_dirname is None
        assert args.prod_config_filename is None
        assert args.rules == RULES_NAMES[0]
        assert args.vapp is None
        assert args.vconf is None
        assert args.version_config_filename is None
        assert args.working_dir is None

        settings = Settings()
        settings_dir = Path(__file__).absolute().parent.parent / "mfire/settings"
        assert settings.altitudes_dirname == settings_dir / "geos/altitudes"
        assert settings.alternate_max == 2
        assert settings.config_filename == CUR_DIR / "configs/global_config.tgz"
        assert (
            settings.mask_config_filename == CUR_DIR / "configs/mask_task_config.json"
        )
        assert (
            settings.data_config_filename == CUR_DIR / "configs/data_task_config.json"
        )
        assert (
            settings.prod_config_filename == CUR_DIR / "configs/prod_task_config.json"
        )
        assert (
            settings.version_config_filename == CUR_DIR / "configs/version_config.json"
        )
        assert settings.data_dirname == CUR_DIR / "data"
        assert settings.mask_dirname == CUR_DIR / "mask"
        assert settings.output_dirname == CUR_DIR / "output"
        assert settings.log_level == "WARNING"
        assert settings.log_file_name is None
        assert settings.log_file_level == "WARNING"
        assert settings.vapp == "promethee"
        assert settings.vconf == "msb"
        assert settings.experiment == "TEST"

        Settings.clean()

    def test_get_version_with_empty_file(self, test_file):
        # empty file
        with pytest.raises(RuntimeError, match="VERSION file is malformed"):
            _get_version(test_file)

    @pytest.mark.parametrize("test_file", [{"content": "1st line"}], indirect=True)
    def test_get_version_with_malformed_str(self, test_file):
        with pytest.raises(RuntimeError, match="VERSION string is malformed"):
            _get_version(test_file)

    @pytest.mark.parametrize("test_file", [{"content": "1.2.dev1"}], indirect=True)
    def test_get_version(self, test_file):
        assert _get_version(test_file) == "1.2.dev1"
