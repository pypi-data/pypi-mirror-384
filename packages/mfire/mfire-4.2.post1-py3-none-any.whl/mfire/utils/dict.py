import re
import sys
from collections import UserDict, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict

import numpy as np


def recursive_format(
    obj: dict | list | str, values: Dict[str, str]
) -> dict | list | str:
    """Function that recursively formats str values within a dict or a list.

    >>> dico = {
        "id": "{nom}_{prenom}",
        "nom": "{nom}",
        "prenoms": ["{prenom}"],
        "intro": "Bonjour, je suis {prenom} {nom}, j'ai {age} ans.",
    }
    >>>  values = {
        "nom": "La Blague",
        "prenom": "Toto",
        "age": 8,
    }
    >>> recursive_format(dico, values)
    {'id': 'La Blague_Toto',
    'nom': 'La Blague',
    'prenoms': ['Toto'],
    'intro': "Bonjour, je suis Toto La Blague, j'ai 8 ans."}

    Args:
        obj: Object containing values to format.
        values: Mapping of values to format.

    Returns:
        dict | list | str: Given obj with formatted values.
    """
    if isinstance(obj, str) and "{" in obj and "}" in obj:
        return obj.format_map(FormatDict(values))
    if isinstance(obj, list):
        return [recursive_format(o, values) for o in obj]
    if isinstance(obj, dict):
        return {key: recursive_format(val, values) for key, val in obj.items()}
    return obj


def recursive_replace(obj: Any, old: str, new: str) -> Any:
    """Function that recursively replaces str values within a dict or a list.

    >>> dico = {
        "id": "toto",
        "nom": "tata",
        "prenoms": ["tata", "titi"],
        "intro": "Bonjour, je suis tata toto, j'ai 18 ans.",
    }
    >>> recursive_replace(dico, "tata", "tutu")
    {
        "id": "toto",
        "nom": "tutu",
        "prenoms": ["tutu", "titi"],
        "intro": "Bonjour, je suis tutu toto, j'ai 18 ans.",
    }

    Args:
        obj: Object containing values to format.
        old: String to be replaced.
        new: New string to replace.

    Returns:
        Any: Given obj with formatted values.
    """
    if isinstance(obj, str):
        return obj.replace(old, new)
    if isinstance(obj, list):
        return [recursive_replace(o, old, new) for o in obj]
    if isinstance(obj, dict):
        return {key: recursive_replace(val, old, new) for key, val in obj.items()}
    if isinstance(obj, Path):
        return Path(str(obj).replace(old, new))
    return obj


def recursive_remove_key(obj: dict | list | str, key: str) -> dict | list | str:
    """Function that recursively removes a key within a dict or a list.

    >>> dico = {
        "id": "toto",
        "nom": "tata",
        "prenoms": ["tata", "titi"],
        "recur": {"nom": "tata"}
    }
    >>> recursive_remove_key(dico, "nom")
    {
        "id": "toto",
        "prenoms": ["tata", "titi"],
        "recur": {}
    }

    Args:
        obj: Object containing values to format.
        key: Key to delete

    Returns:
        Given obj with formatted values.
    """
    if isinstance(obj, list):
        return [recursive_remove_key(o, key) for o in obj]
    if isinstance(obj, dict):
        return {k: recursive_remove_key(val, key) for k, val in obj.items() if k != key}
    return obj


def _id(val: dict) -> str:
    return val.get("id") or val.get("ComponentId")


def _sorted_key(val: dict) -> str:
    # Try to sort configuration dictionary
    try:
        return (
            f"{val['id']}_{val['period']['id']}_"
            f"{val.get('hazard_id', '')}_{val.get('level', '')}"
        )
    except (KeyError, TypeError):
        pass

    # Try to sort production dictionary
    return (
        f"{val['ComponentId']}_{val['Period']['PeriodId']}_{val['GeoId']}"
        f"_{val.get('HazardId', '')}"
    )


def _recursive_are_equals_log(idx: str, verbose: int, msg: str):
    header = f"{idx}\t: " if idx else ""
    if verbose:
        channel = sys.stdout if verbose == 1 else sys.stderr
        print(f"{header}{msg}", file=channel)


def _recursive_are_equals_dict(
    left: dict | list | str,
    right: dict | list | str,
    index_list: str = "",
    verbose: int = 2,
    **kwargs,
) -> bool:
    keysl = set(left)
    keysr = set(right)
    results = []
    if keysl - keysr:
        _recursive_are_equals_log(
            index_list, verbose, f"missing keys in right dict {keysl - keysr}"
        )
        results += [False]
    if keysr - keysl:
        _recursive_are_equals_log(
            index_list, verbose, f"missing keys in left dict {keysr - keysl}"
        )
        results += [False]
    for key in keysl & keysr:
        results += [
            recursive_are_equals(
                left=left[key],
                right=right[key],
                index_list=index_list + f"['{key}']",
                verbose=verbose,
                **kwargs,
            )
        ]
    return all(results)


def _recursive_are_equals_list(
    left: dict | list | str,
    right: dict | list | str,
    index_list: str = "",
    verbose: int = 2,
    **kwargs,
) -> bool:
    len_left = len(left)
    len_right = len(right)
    if len_left != len_right:
        _recursive_are_equals_log(
            index_list,
            verbose,
            f"lengths of iterables don't match ({len_left} | {len_right})",
        )
        return False

    if len_left > 0 and all(isinstance(d, dict) for d in left):
        try:
            sorted_left = sorted(left, key=_sorted_key)
            sorted_right = sorted(right, key=_sorted_key)

            return all(
                recursive_are_equals(
                    left=sorted_left[i],
                    right=sorted_right[i],
                    index_list=index_list + f"[id={_id(sorted_left[i])}]",
                    verbose=verbose,
                    **kwargs,
                )
                for i in range(len_left)
            )
        except (KeyError, TypeError):
            pass

    try:
        left, right = sorted(left), sorted(right)
    except TypeError:
        pass
    return all(
        recursive_are_equals(
            left=left[i],
            right=right[i],
            index_list=index_list + f"[{i}]",
            verbose=verbose,
            **kwargs,
        )
        for i in range(len_left)
    )


def _recursive_are_equals_str(
    left: dict | list | str,
    right: dict | list | str,
    index_list: str = "",
    verbose: int = 2,
    **kwargs,
) -> bool:
    if left == right:
        return True

    if not kwargs:
        _recursive_are_equals_log(
            index_list, verbose, f"str values don't match ('{left}' | '{right}')"
        )
        return False
    format_kwargs = FormatDict(kwargs)
    formatted_left = left.format_map(format_kwargs)
    formatted_right = right.format_map(format_kwargs)
    if formatted_left != formatted_right:
        _recursive_are_equals_log(
            index_list,
            verbose,
            f"formatted str values don't match ('{formatted_left}' | "
            f"'{formatted_right}')",
        )
        return False
    return True


def recursive_are_equals(
    left: dict | list | str,
    right: dict | list | str,
    index_list: str = "",
    verbose: int = 2,
    **kwargs,
) -> bool:
    """
    Recursive function made to check the difference between two given values
    and to highlight the differences.

    Args:
        left: Value 1
        right: Value 2
        index_list: Index of list. Defaults to "".
        verbose: Level of description of the differences. Defaults to 2.
        **kwargs: Keyword arguments.

    Returns:
        True if left and right are equal, else False
    """

    if not isinstance(left, type(right)):
        _recursive_are_equals_log(
            index_list, verbose, f"type mismatch ('{type(left)}' | '{type(right)}')"
        )
        return False

    # Try to compare with float types
    if isinstance(left, float) and np.isnan(left) and np.isnan(right):
        return True

    # Try to compare with main types
    equal_funcs = {
        dict: _recursive_are_equals_dict,
        list: _recursive_are_equals_list,
        str: _recursive_are_equals_str,
    }
    for kind, func in equal_funcs.items():
        if isinstance(left, kind):
            return func(left, right, index_list, verbose, **kwargs)

    # Try to compare as a last resort
    if left != right:
        _recursive_are_equals_log(
            index_list, verbose, f"values don't match ('{left}' | '{right}')"
        )
        return False

    return True


class FormatDict(UserDict):
    """FormatDict: dictionary extension for handling string formatting
    with missing or default keys. For instance :
    >>> dico = {"key1" : "value1"}
    >>> "la valeur 1 = {key1}, la valeur 2 = {key2}".format_map(dico)
    ...
    KeyError("key2")
    >>> dico = FormatDict(dico)
    >>> "la valeur 1 = {key1}, la valeur 2 = {key2}".format_map(dico)
    "la valeur 1 = value1, la valeur 2 = {key2}"
    >>> dico = FormatDict(dico)
    >>> "la valeur 1 = {key1}, la valeur 2 = {key2|value2}".format_map(dico)
    "la valeur 1 = value1, la valeur 2 = {value2}"

    Inheritance:
        UserDict
    """

    def __missing__(self, key: Any) -> str:
        if match := re.match(r"(.+?)\|(.+)", key):
            return (
                val
                if (val := self.data.get(match.group(1))) is not None
                else match.group(2)
            )
        return f"{{{key}}}"

    def __getitem__(self, key: str) -> str:
        item = super().__getitem__(key)
        if isinstance(item, str):
            if match := re.match(r"(.+?)\|(.+)", key):
                key = match.group(1)
            item = (
                self.data.get(f"{key}-prefix", "")
                + item
                + self.data.get(f"{key}-suffix", "")
            )
        return item


class KeyBasedDefaultDict(defaultdict):
    default_factory: Callable

    def __init__(self, default_factory: Callable = None, **kwargs):
        super().__init__(default_factory, **kwargs)

    def __missing__(self, key):
        if self.default_factory is not None:
            self[key] = self.default_factory(key)
            return self[key]
        raise KeyError(key)
