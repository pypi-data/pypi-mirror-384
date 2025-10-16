import json
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np
import pytest

from mfire.settings import UNITS_TABLES
from mfire.settings.constants import (
    LANGUAGES,
    LOCALE_DIR,
    RULES_NAMES,
    TEMPLATES_FILENAME,
)
from mfire.utils.date import Datetime, Timedelta
from mfire.utils.template import TemplateRetriever
from tests.configuration.factories import RulesFactory

PREPROCESSED_COLUMNS = {
    "kind",
    "model",
    "date",
    "time_ref",
    "geometry",
    "cutoff",
    "origin",
    "nativefmt",
    "start",
    "stop",
    "step",
    "dispo_time",
    "block",
    "namespace",
    "alternate",
}

SOURCES_COLUMNS = PREPROCESSED_COLUMNS.union({"vapp", "vconf", "experiment"})


class TestConstants:
    def _parse_json(self, filename: Path):
        try:
            with open(filename) as f:
                return json.load(f)
        except ValueError:
            return None

    def _check(self, val: Any, read_func: Optional[Callable] = None):
        if isinstance(val, Path):
            assert val.is_file(), f"File {val} does not exist"
            if read_func:
                assert read_func(val) is not None, f"File {val} can't be read"
        elif isinstance(val, dict):
            for v in val.values():
                self._check(v, read_func=read_func)

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_templates_filenames(self, language):
        for template_filename in TEMPLATES_FILENAME.values():
            self._check(
                LOCALE_DIR / language / template_filename,
                read_func=TemplateRetriever.read,
            )

    def test_units_tables(self):
        self._check(UNITS_TABLES)

    def test_files_links_content(self):
        """
        Tests the content of the `files_links` and `source_files` DataFrames.

        This test ensures that:

            1. All columns listed in `PREPROCESSED_COLUMNS` are present in the
               `preprocessed_files_df` DataFrame of each created `Rules` object.
            2. All columns listed in `SOURCES_COLUMNS` are present in the
               `source_files_df` DataFrame of each created `Rules` object.
            3. All file IDs listed in the `filename` column of `source_files`
               are also present in the `files_links` DataFrame for the corresponding
               `Rules` object. Handles cases where file IDs in `files_links` might be
               NaN or comma-separated strings.
        """
        for rules_name in RULES_NAMES:
            for td in range(25):
                rules = RulesFactory(
                    name=rules_name,
                    drafting_datetime=Datetime(2023, 3, 1) + Timedelta(hours=td),
                )

                assert PREPROCESSED_COLUMNS.issubset(rules.preprocessed_files_df)
                assert SOURCES_COLUMNS.issubset(rules.source_files_df)

                # Check for presence of all file IDs in source_files
                file_ids = set(
                    rules.files_links_df[
                        rules.preprocessed_files_df.index
                    ].values.flatten()
                )
                source_file_ids = []
                for file_id in file_ids:
                    if isinstance(file_id, float):
                        assert np.isnan(file_id)
                        continue
                    source_file_ids.extend(file_id.split(","))

                assert set(source_file_ids).issubset(rules.source_files_df.index)
