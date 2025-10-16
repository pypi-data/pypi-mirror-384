from __future__ import annotations

import gettext
import re
import unicodedata
from typing import List, Optional, Tuple

from mfire.settings.constants import LOCALE_DIR
from mfire.settings.settings import Settings
from mfire.utils.template import TemplateRetriever


def _(text: str, language: str) -> str:
    return gettext.translation(
        "mfire", localedir=LOCALE_DIR, languages=[language]
    ).gettext(text)


def get_synonym(word: str, language: str) -> str:
    """
    Returns a random synonym of the given word.

    Args:
        word: The word for which a synonym is desired.
        language: Selected language.

    Returns:
        A random synonym of the given word.
    """
    iter_synonyms = next(
        (
            seq
            for seq in TemplateRetriever.table_by_name("synonyms", language)
            if word in seq
        ),
        (word,),
    )
    return Settings().random_choice(iter_synonyms)


def decapitalize(string: str) -> str:
    """
    Decapitalizes only the first letter of a string.

    Args:
        string: The input string.

    Returns:
        str: The decapitalized string.
    """
    return string[:1].lower() + string[1:]


def capitalize(string: str) -> str:
    """
    Capitalizes only the first letter of a string.

    Args:
        string: The input string.

    Returns:
        str: The capitalized string.
    """
    return string[:1].upper() + string[1:]


def strip_string(string: str, chars: Optional[list[str]] = None) -> str:
    """Strip a string except an optional list of characters.

    Args:
        string: The input string.
        chars: A list of characters to not strip.

    Returns:
        Cleaned string.

    """
    if chars is None:
        chars = []

    s_string: str = string.strip()

    for c in chars:
        if c.strip != "":  # Check if c is removed by the str.strip
            continue
        if string.startswith(c):
            s_string = c + s_string
        if string.endswith(c):
            s_string = s_string + c

    return s_string


def capitalize_all(string: str) -> str:
    """
    Capitalizes all sentences in a string.

    Args:
        string: The input string.

    Returns:
        str: The string with all sentences capitalized.
    """

    strings = []
    for line in string.split("\n"):
        line += " "
        strings.append(
            concatenate_string(
                filter(None, (capitalize(s.strip()) for s in line.split(". "))),
                delimiter=". ",
                last_delimiter=". ",
                last_punctuation=".",
            )
        )

    return concatenate_string(
        filter(None, strings), delimiter="\n", last_delimiter="\n", last_punctuation=""
    )


def concatenate_string(
    iterator: List[str] | iter,
    last_delimiter: str,
    delimiter: str = ", ",
    last_punctuation: str = "",
) -> str:
    """
    Concatenates a list of strings with specified delimiters.

    Args:
        iterator: The list or iterator of strings to concatenate.
        last_delimiter: The delimiter before the last string.
        delimiter: The delimiter between strings. Defaults to ", ".
        last_punctuation: The punctuation to add at the end. Defaults to "".

    Returns:
        The concatenated string.
    """

    list_it = [it for it in iterator if it]
    if not list_it:
        return ""

    return (
        delimiter.join(list_it[:-1]) + last_delimiter + list_it[-1]
        if len(list_it) > 1
        else f"{list_it[0]}"
    ) + last_punctuation


def clean_text(text: str, language: str) -> str:
    """
    Cleans text according to the language specified in Settings.language.

    Args:
        text: The text to clean.
        language: Selected language.

    Returns:
        The cleaned text.
    """
    funcs = {
        "fr": clean_french_text,
        "en": clean_english_text,
        "es": clean_spanish_text,
    }
    text = funcs[language](text)

    # make some basic cleans
    text = text.strip()
    text = re.sub(r"\. *\.", ".", text)  # Replaces ".." or ".   ." with "."
    text = re.sub(r"\, *\.", ".", text)  # Replaces ",." or ",   ." with "."
    text = re.sub(" +\xa0", " ", text)
    text = re.sub(" +", " ", text)
    text = re.sub("\xa0 +", " ", text)
    return capitalize_all(text).strip()


def clean_spanish_text(text: str) -> str:
    """Cleans up Spanish text.

    Args:
        text: The input text.

    Returns:
        str: The cleaned text.
    """
    return text


def clean_english_text(text: str) -> str:
    """Cleans up English text.

    Args:
        text: The input text.

    Returns:
        str: The cleaned text.
    """
    return text


def clean_french_text(text: str) -> str:
    """
    Cleans up French text by replacing certain patterns.

    Args:
        text: The input text.

    Returns:
        str: The cleaned text.
    """
    text = re.sub(r"[  ]*'[  ]*", "'", text)

    text = re.sub(r"jusqu.à au", "jusqu'au", text)
    text = re.sub(r"jusqu.à le", "jusqu'au", text)
    text = re.sub(r"jusqu.à en", "jusqu'en", text)
    text = re.sub(r"(\W)dès en début", r"\1dès le début", text)
    text = re.sub(r"(\W)dès en première", r"\1dès la première", text)
    text = re.sub(r"(\W)dès en fin", r"\1dès la fin", text)
    text = re.sub(r"(\W)que en", r"\1qu'en", text)
    text = re.sub(r"(\W)de en ce", r"\1du", text)
    text = re.sub(r"(\W)de en début", r"\1du début", text)
    text = re.sub(r"(\W)de en milieu", r"\1du milieu", text)
    text = re.sub(r"(\W)de en fin", r"\1de la fin", text)
    text = re.sub(r"(\W)de en première", r"\1de la première", text)
    text = re.sub(r"(\W)de[  ]([aeiouyAEIOUY])", r"\1d'\2", text)

    text = text.replace("jusqu'en début de période", "en début de période")
    text = text.replace("à partir de la fin de période", "en fin de période")

    return text


def split_var_name(
    var_name: str, full_var_name: bool = True
) -> Tuple[str, str, int] | Tuple[str, int]:
    """Parses a variable name (<prefix><accum>__<vertical_level>) and extracts
    components.

    Args:
        var_name: The variable name to parse.
        full_var_name: Controls return format (default: True).

    Returns:
        Extracted components based on `full_var_name`.
    """
    prefix, accum, vert_level = re.match(
        r"^([a-zA-Z_]+)(\d*)__(.*)$", var_name
    ).groups()

    if accum == "":
        accum = 0

    return (
        (f"{prefix}__{vert_level}", int(accum))
        if full_var_name
        else (prefix, vert_level, int(accum))
    )


def join_var_name(prefix: str, vertical_level: str, accum: Optional[int]) -> str:
    """
    Constructs a variable name following the pattern: <prefix><accum>__<vertical_level>.

    This function joins the provided `prefix`, optional `accum` (accumulation value),
    and `vertical_level` into a single string using double underscores as separators.
    If `accum` is None, it omits the accumulation part from the final variable name.

    Args:
        prefix: The base prefix for the variable name.
        vertical_level: The vertical level of the variable.
        accum: The accumulation value (hours).

    Returns:
        Constructed variable name.
    """
    return (
        f"{prefix}{accum}__{vertical_level}" if accum else f"{prefix}__{vertical_level}"
    )


class TagFormatter:
    """
    TagFormatter: Format a string containing tags of the form '[key:func]'.
    It follows the Vortex standard.
    """

    time_format: dict = {
        "fmth": "{:04d}",
        "fmthm": "{:04d}:00",
        "fmthhmm": "{:02d}:00",
        "fmtraw": "{:04d}00",
    }
    datetime_format: dict = {
        "julian": "%j",
        "ymd": "%Y%m%d",
        "yymd": "%y%m%d",
        "y": "%Y",
        "ymdh": "%Y%m%d%H",
        "yymdh": "%y%m%d%H",
        "ymdhm": "%Y%m%d%H%M",
        "ymdhms": "%Y%m%d%H%M%S",
        "mmddhh": "%m%d%H",
        "mm": "%m",
        "hm": "%H%M",
        "dd": "%d",
        "hh": "%H",
        "h": "%-H",
        "vortex": "%Y%m%dT%H%M%S",
        "stdvortex": "%Y%m%dT%H%M",
        "iso8601": "%Y-%m-%dT%H:%M:%SZ",
    }

    def format_tags(self, text: str, tags: dict = None) -> str:
        """
        Formats a string containing tags of the form '[key:func]'.

        Args:
            text: The text to format.
            tags: A dictionary of tag-value pairs. Defaults to None.

        Returns:
            The formatted string.
        """
        if not tags:
            return text

        for key, value in tags.items():
            # Raw key formatting
            text = text.replace("[{}]".format(key), str(value))

            # Time formatting
            if isinstance(value, int):
                for func, fmt in self.time_format.items():
                    text = text.replace("[{}:{}]".format(key, func), fmt.format(value))
            # Datetime formatting
            try:
                from mfire.utils.date import Datetime

                value_dt = Datetime(value)
                for func, fmt in self.datetime_format.items():
                    text = text.replace(
                        "[{}:{}]".format(key, func), value_dt.strftime(fmt)
                    )
            except (TypeError, ValueError):
                pass

            # Geometry formatting
            text = text.replace("[{}:area]".format(key), str(value).upper())

        return text


def is_vowel(letter: str) -> bool:
    if len(letter) > 1:
        raise ValueError

    return unicodedata.normalize("NFKD", letter).encode("ASCII", "ignore").decode(
        "utf-8"
    ).lower() in ["a", "e", "i", "o", "u", "y"]
