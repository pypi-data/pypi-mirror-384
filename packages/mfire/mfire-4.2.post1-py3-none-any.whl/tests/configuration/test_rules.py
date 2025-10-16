from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from mfire.utils.date import Datetime
from mfire.utils.exception import ConfigurationError, ConfigurationWarning
from tests.configuration.factories import RulesFactory


@patch("os.environ", {"MFIRE_DISABLE_PRECACHING": True})
class TestRules:
    """Classe qui teste les fichiers de configuration des données météos"""

    @pytest.mark.parametrize("test_file", [{"name": "file"}], indirect=True)
    def test_init_path(self, test_file):
        with pytest.raises(FileNotFoundError, match="Directory not found: dir"):
            RulesFactory(path=Path("dir"))
        with pytest.raises(
            FileNotFoundError, match=f"Directory not found: {test_file}"
        ):
            RulesFactory(path=test_file)

    @pytest.mark.parametrize("test_file", [{"name": "file"}], indirect=True)
    def test_validate_name_and_directory(self, tmp_path, test_file):
        with pytest.raises(
            FileNotFoundError, match=f"Directory not found: {tmp_path}/dir"
        ):
            RulesFactory(path=tmp_path, name="dir")
        with pytest.raises(
            FileNotFoundError, match=f"Directory not found: {test_file}"
        ):
            RulesFactory(path=test_file.parent, name=test_file.name)

    def test_bulletin_datetime(self):
        assert RulesFactory(drafting_datetime=None).bulletin_datetime is None
        assert RulesFactory(
            drafting_datetime=Datetime(2023, 3, 1, 6, 30, 15)
        ).bulletin_datetime == Datetime(2023, 3, 1, 6)

    def test_grib_param_df(self, tmp_path):
        grib_param_df = RulesFactory().grib_param_df
        assert isinstance(grib_param_df, pd.DataFrame)
        assert len(grib_param_df) == 347

        (tmp_path / "alpha").mkdir()
        with pytest.raises(
            FileNotFoundError, match="CSV file grib_param.csv not found"
        ):
            _ = RulesFactory(path=tmp_path).grib_param_df

    def test_family_param_df(self, tmp_path):
        family_param_df = RulesFactory().family_param_df
        assert isinstance(family_param_df, pd.DataFrame)
        assert len(family_param_df) == 8

        (tmp_path / "alpha").mkdir()
        with pytest.raises(
            FileNotFoundError, match="CSV file family_param.csv not found"
        ):
            _ = RulesFactory(path=tmp_path).family_param_df

    def test_param_link_df(self, tmp_path):
        param_link_df = RulesFactory().param_link_df
        assert isinstance(param_link_df, pd.DataFrame)
        assert len(param_link_df) == 23

        (tmp_path / "alpha").mkdir()
        with pytest.raises(
            FileNotFoundError, match="CSV file param_link.csv not found"
        ):
            _ = RulesFactory(path=tmp_path).param_link_df

    def test_geometries_df(self, tmp_path):
        geometries_df = RulesFactory().geometries_df
        assert isinstance(geometries_df, pd.DataFrame)
        assert len(geometries_df) == 7

        (tmp_path / "alpha").mkdir()
        with pytest.raises(
            FileNotFoundError, match="CSV file geometries.csv not found"
        ):
            _ = RulesFactory(path=tmp_path).geometries_df

    def test_source_files_df(self, assert_equals_result):
        assert RulesFactory(drafting_datetime=None).source_files_df is None
        assert_equals_result(RulesFactory().source_files_df)

    def test_preprocessed_files_df(self, assert_equals_result):
        assert RulesFactory(drafting_datetime=None).preprocessed_files_df is None
        assert_equals_result(RulesFactory().preprocessed_files_df)

    def test_files_links_df(self, assert_equals_result):
        assert RulesFactory(drafting_datetime=None).files_links_df is None
        assert_equals_result(RulesFactory().files_links_df)

    def test_files_ids(self, assert_equals_result):
        assert RulesFactory(drafting_datetime=None).files_ids is None
        assert_equals_result(RulesFactory().files_ids)

    def test_bounds(self, assert_equals_result):
        assert_equals_result(RulesFactory().bounds)

    @pytest.mark.parametrize(
        "file_id",
        [
            "petaroute_jj1_2023-03-01T00:00:00+00:00_18",
            "france_jj1_2023-02-28T00:00:00+00:00_maj20",
            "truc",
        ],
    )
    def test_file_info(self, file_id, assert_equals_result):
        assert_equals_result(RulesFactory().file_info(file_id))

    @pytest.mark.parametrize(
        "term,geometries,params,expected",
        [
            # Given term is before the minimal start
            (Datetime(2022, 3, 1), ["eurw1s100"], set(), None),
            # Given term is after the maximal stop
            (Datetime(2024, 3, 1), ["eurw1s100"], set(), None),
            # No given geometries
            (Datetime(2023, 3, 1), [], set(), None),
            # No exact term
            (Datetime(2023, 3, 1, 6, 30), ["eurw1s100"], set(), None),
            # Parameter is not a subset
            (Datetime(2023, 3, 1, 1), ["eurw1s100"], {"TRUC__MUCHE"}, None),
            (Datetime(2023, 3, 1, 1), ["eurw1s100"], {"TRUC24__MUCHE"}, None),
            # Normal result
            (
                Datetime(2023, 3, 1, 1),
                ["eurw1s100"],
                set(),
                ("france_jj1_2023-03-01T00:00:00+00:00_maj00", Datetime(2023, 3, 3)),
            ),
            (
                Datetime(2023, 3, 1, 1),
                ["eurw1s100"],
                {"LPN__SOL"},
                ("france_jj1_2023-03-01T00:00:00+00:00_maj00", Datetime(2023, 3, 3)),
            ),
        ],
    )
    def test_best_preprocessed_file(self, term, geometries, params, expected):
        assert (
            RulesFactory().best_preprocessed_file(term, geometries, params) == expected
        )

    @pytest.mark.parametrize(
        "start,stop",
        [
            (Datetime(2023, 3, 1), Datetime(2023, 3, 1, 10)),
            (Datetime(2023, 3, 1, 1), Datetime(2023, 3, 4, 6)),
            (Datetime(2023, 3, 4), Datetime(2023, 3, 20)),
        ],
    )
    def test_best_preprocessed_files(self, start, stop, assert_equals_result):
        assert_equals_result(
            RulesFactory().best_preprocessed_files(
                start=start,
                stop=stop,
                geometries=["eurw1s100", "globd025"],
                params=set(),
            )
        )

    def test_best_preprocessed_files_fails(self):
        rules = RulesFactory()
        # start > stop
        with pytest.raises(ConfigurationError, match="Invalid date range"):
            rules.best_preprocessed_files(
                Datetime(2023, 3, 2), Datetime(2023, 3, 1), ..., ...
            )
        # bulletin_datetime > stop
        with pytest.raises(ConfigurationWarning, match="Bulletin datetime"):
            rules.best_preprocessed_files(
                Datetime(2020, 3, 1), Datetime(2020, 3, 2), ..., ...
            )
        # preprocessed_files_df.stop < start
        with pytest.raises(ConfigurationError, match="No data available"):
            rules.best_preprocessed_files(
                Datetime(2023, 3, 6), Datetime(2023, 3, 7), ["eurw1s100"], ...
            )
        # No geometry
        with pytest.raises(ConfigurationError, match="No data available"):
            rules.best_preprocessed_files(
                Datetime(2023, 3, 1), Datetime(2023, 3, 2), [], ...
            )
        # stop < files_df.start.min()
        with pytest.raises(ConfigurationError, match="No data available"):
            rules.best_preprocessed_files(
                Datetime(2023, 3, 1), Datetime(2023, 3, 1, 14), ["globd025"], ...
            )

    @pytest.mark.parametrize(
        "file_id,term,var_name",
        [
            ("france_jj1_2023-02-28T00:00:00+00:00_maj20", None, "EAU1__SOL"),
            ("france_j2j3_2023-02-28T00:00:00+00:00_maj18", None, "FF__HAUTEUR10"),
            ("france_h36_2023-02-28T00:00:00+00:00_maj03", None, "GIVRECABLE__P001"),
            (
                "petaroute_jj1_2023-03-01T00:00:00+00:00_18",
                Datetime(2023, 3, 2),
                "EAU24__SOL",
            ),
            (
                "france_jj1_2023-02-28T00:00:00+00:00_maj20",
                Datetime(2023, 3, 2),
                "EAU1__SOL",
            ),
            (
                "france_j2j3_2023-02-28T00:00:00+00:00_maj18",
                Datetime(2023, 3, 2),
                "FF__HAUTEUR10",
            ),
            (
                "france_h36_2023-02-28T00:00:00+00:00_maj03",
                Datetime(2023, 3, 2),
                "GIVRECABLE__P001",
            ),
        ],
    )
    def test_resource_handler(self, file_id, term, var_name, assert_equals_result):
        assert_equals_result(RulesFactory().resource_handler(file_id, term, var_name))

    def test_resource_handler_fails(self):
        with pytest.raises(
            ConfigurationError, match="Cannot configure resource handler"
        ):
            RulesFactory().resource_handler(
                "petaroute_jj1_2023-03-01T00:00:00+00:00_18", None, "EAU24__SOL"
            )

    @pytest.mark.parametrize(
        "file_id,var_name",
        [
            ("france_jj1_2023-02-28T00:00:00+00:00_maj08", "EAU24__SOL"),
            ("france_jj1_2023-02-28T00:00:00+00:00_maj20", "EAU1__SOL"),
            ("france_j2j3_2023-02-28T00:00:00+00:00_maj18", "FF__HAUTEUR10"),
            ("france_h36_2023-02-28T00:00:00+00:00_maj03", "GIVRECABLE__P001"),
        ],
    )
    def test_source_files_terms(self, file_id, var_name, assert_equals_result):
        data_config = {"sources": {}}
        source_files_terms = RulesFactory().source_files_terms(
            data_config, file_id, var_name
        )
        assert_equals_result(
            {"data_config": data_config, "source_files_terms": source_files_terms}
        )
