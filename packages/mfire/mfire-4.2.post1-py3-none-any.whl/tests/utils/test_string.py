import numpy as np
import pytest

from mfire.utils.string import (
    TagFormatter,
    _,
    capitalize,
    capitalize_all,
    clean_french_text,
    clean_text,
    concatenate_string,
    decapitalize,
    get_synonym,
    is_vowel,
    join_var_name,
    split_var_name,
    strip_string,
)


class TestStringUtilsFunctions:
    def test_get_synonym(self):
        np.random.seed(42)
        assert get_synonym("d'environ", language="fr") == "de l'ordre de"
        assert get_synonym("fort", language="fr") == "marqué"
        assert get_synonym("abc", language="fr") == "abc"

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Hello Hey", "Hello Hey"),
            (" Hello\nHey ", "Hello\nHey"),
            ("\nHello Hey\n", "Hello Hey"),
        ],
    )
    def test_strip_string(self, text, expected):
        assert strip_string(text) == expected

    def test_decapitalize(self):
        assert (
            decapitalize("Première phrase. Deuxième phrase.")
            == "première phrase. Deuxième phrase."
        )

    def test_capitalize(self):
        assert (
            capitalize("première phrase. deuxième phrase.") == "Première phrase. "
            "deuxième phrase."
        )

    @pytest.mark.parametrize(
        "string,expected",
        [
            ("phrase 1 .   \n    phrase 2  .", "Phrase 1.\nPhrase 2."),
            ("", ""),
            ("phrase 1.", "Phrase 1."),
            ("phrase 1. phrase 2.       Phrase 3.", "Phrase 1. Phrase 2. Phrase 3."),
            ("10.0 cm", "10.0 cm."),
        ],
    )
    def test_capitalize_all(self, string, expected):
        assert capitalize_all(string) == expected

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("rafales. ", "Rafales."),
            ("rafales..", "Rafales."),
            ("rafales.    .", "Rafales."),
            ("rafales,.", "Rafales."),
            ("rafales,     .", "Rafales."),
            ("text1  text2", "Text1 text2."),
            ("text1.  text2", "Text1. Text2."),
            ("text1   ;   text2", "Text1 ; text2."),
            ("text1     text2", "Text1 text2."),
        ],
    )
    def test_clean_text(self, text, expected):
        assert clean_text(text, language="fr") == expected

    @pytest.mark.parametrize(
        "text,expected",
        [
            # Syntax correction
            ("d  '  au moins", "d'au moins"),
            ("vent de ouest", "vent d'ouest"),
            ("vent de Ouest", "vent d'Ouest"),
            ("jusqu'à au jeudi", "jusqu'au jeudi"),
            ("jusqu'à le jeudi", "jusqu'au jeudi"),
            ("jusqu'à en début de soirée", "jusqu'en début de soirée"),
            ("risque dès en début de journée", "risque dès le début de journée"),
            (
                "risque dès en première partie de journée",
                "risque dès la première partie de journée",
            ),
            ("risque dès en fin de nuit", "risque dès la fin de nuit"),
            ("risque que en début de nuit", "risque qu'en début de nuit"),
            (
                "rafales à partir de en ce milieu de nuit",
                "rafales à partir du milieu de nuit",
            ),
            (
                "rafales à partir de en début de nuit",
                "rafales à partir du début de nuit",
            ),
            (
                "rafales à partir de en milieu de cette nuit",
                "rafales à partir du milieu de cette nuit",
            ),
            (
                "rafales à partir de en fin de nuit",
                "rafales à partir de la fin de nuit",
            ),
            (
                "rafales à partir de en première partie de la nuit",
                "rafales à partir de la première partie de la nuit",
            ),
            ("rafales à partir de aujourd'hui", "rafales à partir d'aujourd'hui"),
            ("risque jusqu'en début de période", "risque en début de période"),
            ("risque à partir de la fin de période", "risque en fin de période"),
        ],
    )
    def test_clean_french_text(self, text, expected):
        assert clean_french_text(text) == expected

    def test_concatenate_string(self):
        assert concatenate_string([], last_delimiter=" et ") == ""
        assert concatenate_string(["test1"], last_delimiter=" et ") == "test1"
        assert (
            concatenate_string(["test1"], last_delimiter=" et ", last_punctuation=".")
            == "test1."
        )
        assert (
            concatenate_string(["test1", "test2", "test3"], last_delimiter=" et ")
            == "test1, test2 et test3"
        )

    @pytest.mark.parametrize(
        "var_name,full_var_name,expected",
        [
            ("EAU24__SOL", True, ("EAU__SOL", 24)),
            ("FF__HAUTEUR", True, ("FF__HAUTEUR", 0)),
            ("EAU24__SOL", False, ("EAU", "SOL", 24)),
            ("FF__HAUTEUR", False, ("FF", "HAUTEUR", 0)),
        ],
    )
    def test_split_var_name(self, var_name, full_var_name, expected):
        assert split_var_name(var_name, full_var_name=full_var_name) == expected

    @pytest.mark.parametrize(
        "args,expected",
        [
            (("EAU", "SOL", 24), "EAU24__SOL"),
            (("FF", "HAUTEUR", 0), "FF__HAUTEUR"),
            (("RAF", "HAUTEUR", None), "RAF__HAUTEUR"),
        ],
    )
    def test_join_var_name(self, args, expected):
        assert join_var_name(*args) == expected

    def test_translation(self):
        assert _("en dessous de", "fr") == "en dessous de"
        assert _("en dessous de", "en") == "under"
        assert _("en dessous de", "es") == "por debajo"

    def test_is_vowel(self):
        for vowel in ["a", "e", "i", "o", "u", "y", "é", "è", "à", "ù"]:
            assert is_vowel(vowel)
        for no_vowel in ["b", "c", "ç", "ñ"]:
            assert not is_vowel(no_vowel)
        with pytest.raises(ValueError):
            is_vowel("Phrase non acceptée")


class TestTagFormatter:
    @pytest.mark.parametrize(
        "text,tags,expected",
        [
            ("Datetime: [key:ymdhm]", {}, "Datetime: [key:ymdhm]"),
            ("Datetime: [key:ymd]", {"key": 1618617600}, "Datetime: 20210417"),
            (
                "Datetime: [key:ymdhm]",
                {"key": "20230301T0600"},
                "Datetime: 202303010600",
            ),
            (
                "Datetime: [key:vortex]",
                {"key": "20230301T0600"},
                "Datetime: 20230301T060000",
            ),
            # Error in the date
            (
                "Datetime: [key:ymdhm]",
                {"key": "20231301T0600"},
                "Datetime: [key:ymdhm]",
            ),
        ],
    )
    def test_format_tags(self, text, tags, expected):
        tag_formatter = TagFormatter()
        assert tag_formatter.format_tags(text, tags=tags) == expected
