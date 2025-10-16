import os
from pathlib import Path
from unittest.mock import patch

import pytest

from mfire.configuration.rules import Rules
from mfire.settings import Settings
from mfire.settings.constants import ROOT_DIR
from mfire.utils.date import Datetime
from mfire.utils.dict import recursive_replace
from mfire.utils.json import JsonFile
from tests.configuration.factories import ProcessorFactory


class TestProcessor:
    inputs_dir: Path = Path(__file__).parent / "inputs"

    @patch("os.environ", {"MFIRE_DISABLE_PRECACHING": True})
    def test_init_drafting_datetime(self):
        assert ProcessorFactory(
            drafting_datetime=Datetime(2023, 3, 2, 6)
        ).drafting_datetime == Datetime(2023, 3, 2, 6)

        assert ProcessorFactory(
            drafting_datetime="20230302T060000"
        ).drafting_datetime == Datetime(2023, 3, 2, 6)

        with pytest.raises(ValueError, match="Invalid drafting_datetime format: XYZ"):
            ProcessorFactory(drafting_datetime="XYZ")

    @patch("os.environ", {"MFIRE_DISABLE_PRECACHING": True})
    def test_init_rules(self):
        processor = ProcessorFactory(rules="alpha")
        assert isinstance(processor.rules, Rules)
        assert processor.rules.name == "alpha"

    @patch("os.environ", {"MFIRE_DISABLE_PRECACHING": True})
    def test_prod_config(self):
        assert ProcessorFactory(
            prod_configs=[("a", {"b": "c"}), ("d", {"e": "f"})]
        ).prod_config == {"a": {"b": "c"}, "d": {"e": "f"}}

    @patch("os.environ", {"MFIRE_DISABLE_PRECACHING": True})
    def test_mask_config(self):
        assert ProcessorFactory(
            mask_configs=[("a", {"b": "c"}), ("d", {"e": "f"})]
        ).mask_config == {"a": {"b": "c"}, "d": {"e": "f"}}

    def test_version_config(self, assert_equals_result):
        assert_equals_result(
            ProcessorFactory(
                configurations_factory=[{"date_config": Datetime(2023, 1, 1)}]
            ).version_config
        )

    @pytest.mark.parametrize("experiment", ["TEST", "DBLE", "OPER"])
    def test_data_config(self, experiment, assert_equals_result):
        Settings().set(experiment=experiment)
        data_configs = [
            {
                ("france_jj1_2023-03-01T00:00:00+00:00_maj00", "NEIPOT1__SOL"): [
                    {"a": "b", "c": "d"}
                ]
            },
            {("france_jj1_2023-03-01T00:00:00+00:00_maj00", "NEIPOT1__SOL"): ...},
            {("france_jj1_2023-03-01T00:00:00+00:00_maj00", "EAU24__SOL"): []},
            {("france_jj1_2023-02-28T00:00:00+00:00_maj20", "NEIPOT1__SOL"): []},
            {("france_jj1_2023-02-28T00:00:00+00:00_maj20", "FF__HAUTEUR10"): []},
            {("france_h36_2023-02-28T00:00:00+00:00_maj20", "GIVRECABLE__P001"): []},
        ]
        assert_equals_result(
            ProcessorFactory(
                configurations_factory=[], data_configs=data_configs
            ).data_config
        )

    def test_global_hash(self, assert_equals_result):
        assert_equals_result(ProcessorFactory(configurations_factory=[]).global_hash)

    @pytest.mark.parametrize(
        "configuration_path", ["small_config.tgz", "small_config.json"]
    )
    def test_process(self, configuration_path, assert_equals_file):
        os.makedirs("configs", exist_ok=True)
        ProcessorFactory(
            configuration_path=self.inputs_dir / configuration_path
        ).process()

        prod_config = JsonFile(Settings().prod_config_filename)
        prod_config.dump(recursive_replace(prod_config.load(), f"{ROOT_DIR}/", ""))

        assert_equals_file(Settings().prod_config_filename)
        assert_equals_file(Settings().mask_config_filename)
        assert_equals_file(Settings().data_config_filename)
        assert_equals_file(Settings().version_config_filename)

    @pytest.mark.parametrize(
        "configuration_path", ["small_config.json", "small_config.tgz"]
    )
    def test_configurations(self, configuration_path, assert_equals_result):
        assert_equals_result(
            ProcessorFactory(
                configuration_path=self.inputs_dir / configuration_path
            ).configurations
        )

    @pytest.mark.parametrize(
        "test_file", [{"extension": "json", "content": '"Hello"'}], indirect=True
    )
    def test_configurations_fails(self, test_file):
        assert len(ProcessorFactory(configuration_path=test_file).configurations) == 0
