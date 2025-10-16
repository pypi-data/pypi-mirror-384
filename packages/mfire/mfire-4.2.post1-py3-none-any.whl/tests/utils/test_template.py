from configparser import ConfigParser
from pathlib import Path

import pandas as pd
import pytest

from mfire.utils.json import JsonFile
from mfire.utils.template import (
    CentroidTemplateRetriever,
    CsvTemplateRetriever,
    IniTemplateRetriever,
    JsonTemplateRetriever,
    Template,
    TemplateRetriever,
)
from tests.functions_test import assert_identically_close


class TestTemplate:
    def test_format(self):
        # Jinja template
        my_tpl = Template("significati{% if feminine %}ve{% else %}f{% endif %}\n")
        assert my_tpl.format(feminine=True) == "significative\n"
        assert my_tpl.format(feminine=False) == "significatif\n"

        # No formatting
        my_str = (
            "This is a {adj} template made by {template_author_name} in "
            "{template_date_year}!!"
        )
        my_tpl = Template(my_str)
        assert my_tpl.format() == my_str

        # Basic formatting
        my_dict = {
            "template": {
                "author": {"name": "toto", "age": 30},
                "date": {"month": "may", "year": 2022},
            },
            "adj": "beautiful",
        }
        assert (
            my_tpl.format(**my_dict)
            == "This is a beautiful template made by toto in 2022!!"
        )

        # Default formatting
        my_tpl = Template(
            "This is a {adj|basic quick} template made by {author_auth1|default "
            "author} and {author_auth2|you}"
        )
        assert (
            my_tpl.format(author={"auth1": "me", "auth2": None})
            == "This is a basic quick template made by me and you"
        )

        # Test with more than needed keys
        my_tpl = Template("Hello, {var1}")
        kwargs = {"var1": "good morning {var2}", "var2": "today"}
        assert my_tpl.format(**kwargs) == "Hello, good morning today"


class TestTemplateRetriever:
    path = Path("test.json")
    content = {
        "A": "toto",
        "B": ["tata", "titi", "tutu"],
        "D": {"E": "tyty", "F": ["a", "b"]},
    }

    def test_init(self):
        tpl_rtr = TemplateRetriever(self.content)
        assert tpl_rtr.table == self.content
        assert tpl_rtr.get(("D", "F"), pop_method="first") == "a"

        assert tpl_rtr.get("A") == "toto"
        assert tpl_rtr.get("B") in ["tata", "titi", "tutu"]
        assert tpl_rtr.get("B", pop_method="first") == "tata"
        assert tpl_rtr.get("B", pop_method="last") == "tutu"

        pop_method = "-".join
        assert tpl_rtr.get("B", pop_method=pop_method) == "tata-titi-tutu"

        assert tpl_rtr.get("C", default="tete") == "tete"
        assert tpl_rtr.get("C") is None
        assert tpl_rtr.get(("D", "E")) == "tyty"

        assert tpl_rtr.get(("D", "F"), pop_method=lambda _: 1 / 0) is None
        assert (
            tpl_rtr.get(("D", "F"), pop_method=lambda _: 1 / 0, default="tete")
            == "tete"
        )

        assert (
            "{'A': 'toto', 'B': ['tata', 'titi', 'tutu'], 'D': {'E': 'tyty', "
            "'F': ['a', 'b']}}" in str(tpl_rtr)
        )

    def test_read_file(self):
        assert TemplateRetriever.read_file(self.path) == TemplateRetriever(
            {"filename": self.path}
        )

    @pytest.mark.parametrize(
        "test_file", [{"extension": "json", "content": "{}"}], indirect=True
    )
    def test_read_with_json(self, test_file):
        assert isinstance(TemplateRetriever.read(test_file), JsonTemplateRetriever)

    @pytest.mark.parametrize("test_file", [{"extension": "ini"}], indirect=True)
    def test_read_with_ini(self, test_file):
        assert isinstance(TemplateRetriever.read(test_file), IniTemplateRetriever)

    @pytest.mark.parametrize(
        "test_file", [{"extension": "csv", "content": ","}], indirect=True
    )
    def test_read_with_csv(self, test_file):
        assert isinstance(TemplateRetriever.read(test_file), CsvTemplateRetriever)

    @pytest.mark.parametrize(
        "test_file", [{"extension": "csv", "content": ",A,\nweights,1,"}], indirect=True
    )
    def test_read_with_centroid(self, test_file):
        assert isinstance(TemplateRetriever.read(test_file), CentroidTemplateRetriever)

    @pytest.mark.parametrize(
        "test_file", [{"extension": "txt"}, {"extension": "yaml"}], indirect=True
    )
    def test_read_with_other_extensions(self, test_file):
        assert isinstance(TemplateRetriever.read(test_file), TemplateRetriever)


class TestJsonTemplateRetriever:
    json_content = {
        "A": "toto",
        "B": ["tata", "titi", "tutu"],
        "D": {"E": "tyty", "F": ["a", "b"]},
    }

    def _check_get(self, tpl_rtr):
        assert isinstance(tpl_rtr, JsonTemplateRetriever)

        assert tpl_rtr.get("A") == "toto"
        assert tpl_rtr.get("B") in ["tata", "titi", "tutu"]
        assert tpl_rtr.get("B", pop_method="first") == "tata"
        assert tpl_rtr.get("B", pop_method="last") == "tutu"

        pop_method = "-".join
        assert tpl_rtr.get("B", pop_method=pop_method) == "tata-titi-tutu"

        assert tpl_rtr.get("C", default="tete") == "tete"
        assert tpl_rtr.get("C") is None
        assert tpl_rtr.get(("D", "E")) == "tyty"

        assert tpl_rtr.get(("D", "F"), pop_method="first") == "a"
        assert tpl_rtr.get(("D", "F"), pop_method=lambda _: 1 / 0) is None
        assert (
            tpl_rtr.get(("D", "F"), pop_method=lambda _: 1 / 0, default="tete")
            == "tete"
        )

    @pytest.mark.parametrize("test_file", [{"extension": "json"}], indirect=True)
    def test_init_and_read_file(self, test_file):
        tpl_rtr1 = JsonTemplateRetriever(self.json_content)
        self._check_get(tpl_rtr1)

        JsonFile(test_file).dump(self.json_content)
        tpl_rtr2 = TemplateRetriever.read(test_file)
        assert tpl_rtr2 is not None
        self._check_get(tpl_rtr2)

        assert tpl_rtr1 == tpl_rtr2

        # Test with not existing file
        assert TemplateRetriever.read("file_does_not_exist.json") is None


class TestIniTemplateRetriever:
    @property
    def init_content(self):
        config = ConfigParser()
        config["DEFAULT"]["A"] = "toto"
        config["DEFAULT"]["B"] = "tata"
        config.add_section("D")
        config["D"]["E"] = "tyty"
        return config

    def _check_get(self, tpl_rtr):
        assert isinstance(tpl_rtr, IniTemplateRetriever)

        assert tpl_rtr.get("A") == "toto"
        assert tpl_rtr.get("B") == "tata"
        assert tpl_rtr.get("C", default="tete") == "tete"
        assert tpl_rtr.get("C") is None
        assert tpl_rtr.get(("D", "E")) == "tyty"

    @pytest.mark.parametrize("test_file", [{"extension": "ini"}], indirect=True)
    def test_init_and_read_file(self, test_file):
        tpl_rtr1 = IniTemplateRetriever(self.init_content)
        self._check_get(tpl_rtr1)

        with open(test_file, "w") as f:
            self.init_content.write(f)
            f.close()

        tpl_rtr2 = TemplateRetriever.read(test_file)
        self._check_get(tpl_rtr2)

        assert tpl_rtr1 == tpl_rtr2

        # Test with not existing file
        assert TemplateRetriever.read("file_does_not_exist.ini") is None


class TestCsvTemplateRetriever:
    csv_content = pd.DataFrame(
        [[0, 0, "toto"], [0, 1, "tata"], [1, 0, "titi"], [1, 1, "tutu"]],
        columns=["A", "B", "template"],
    ).set_index(["A", "B"])

    def _check_get(self, tpl_rtr):
        assert isinstance(tpl_rtr, CsvTemplateRetriever)
        assert tpl_rtr.get((0, 0)) == "toto"
        assert tpl_rtr.get((0, 1)) == "tata"
        assert tpl_rtr.get((1, 0)) == "titi"
        assert tpl_rtr.get((1, 1)) == "tutu"
        assert tpl_rtr.get((1, 2), default="wrong key again") == "wrong key again"
        assert tpl_rtr.get((1, 2)) is None

    @pytest.mark.parametrize("test_file", [{"extension": "csv"}], indirect=True)
    def test_init_and_read_file(self, test_file):
        tpl_rtr1 = CsvTemplateRetriever(self.csv_content)
        self._check_get(tpl_rtr1)

        self.csv_content.to_csv(test_file)
        tpl_rtr2 = TemplateRetriever.read(test_file, index_col=["A", "B"])
        self._check_get(tpl_rtr2)

        assert tpl_rtr1 == tpl_rtr2

        # Test with not existing file
        assert TemplateRetriever.read("file_does_not_exist.csv") is None


class TestCentroidTemplateRetriever:
    csv_weights = [0.7, 0.25]
    csv_content = pd.DataFrame(
        [[0, 0, "toto"], [0, 1, "tata"], [1, 0, "titi"], [1, 1, "tutu"]],
        columns=["A", "B", "template"],
    )

    def _check_get_with_weights(self, tpl_rtr: TemplateRetriever):
        assert isinstance(tpl_rtr, CentroidTemplateRetriever)

        assert tpl_rtr.get([1, 2]) == "tutu"
        assert tpl_rtr.get([-1, 0.8]) == "tata"

        assert_identically_close(
            tpl_rtr.get([1, 2], return_centroid=True), ("tutu", [1.0, 1.0])
        )
        assert_identically_close(
            tpl_rtr.get([-1, 0.8], return_centroid=True), ("tata", [0.0, 1.0])
        )

        assert tpl_rtr.get_by_dtw([1, 1, 1, 0, 0, 0, 0]) == {
            "distance": 0.0,
            "path": [(0, 0), (1, 0), (2, 0), (3, 1), (4, 1), (5, 1), (6, 1)],
            "template": "titi",
            "centroid": (1, 0),
        }

    def test_init_and_read_file_without_weights(self):
        tpl_rtr = CentroidTemplateRetriever(
            self.csv_content.set_index(["A", "B"]), col="template"
        )
        self._check_get_with_weights(tpl_rtr)

        # Test with not existing file
        assert (
            TemplateRetriever.read("file_does_not_exist.csv", force_centroid=True)
            is None
        )

        # Test default value with bad key
        assert tpl_rtr.get("test", default="Default") == "Default"

    @pytest.mark.parametrize("test_file", [{"extension": "csv"}], indirect=True)
    def test_init_and_read_file_with_weights(self, test_file):
        df = self.csv_content.copy()
        df.loc["weights"] = self.csv_weights + [None]
        df.to_csv(test_file)

        tpl_rtr = TemplateRetriever.read(test_file)
        self._check_get_with_weights(tpl_rtr)
