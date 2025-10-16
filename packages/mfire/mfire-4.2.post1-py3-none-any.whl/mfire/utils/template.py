from __future__ import annotations

import json
from configparser import ConfigParser
from pathlib import Path
from typing import Any, Callable, Hashable, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from dtaidistance import dtw
from jinja2 import Template as JinjaTemplate

from mfire.settings import Settings, get_logger
from mfire.settings.constants import LOCALE_DIR, TEMPLATES_FILENAME
from mfire.utils import FormatDict

# Logging
LOGGER = get_logger(name="text.template.mod", bind="text.template")


class Template(str):
    """Template: class extending str type for formating using a custom FormatDict
    (in order to avoid issues when keys are missing).
    >>> s = Template("Ma {b} connait des blagues de {a}, et {c} ?")
    >>> s.format(a="toto", b="tata")
    "Ma tata connait des blagues de toto, et {c} ?"
    >>> s = Template("Bonjour M. {a_prenom} {a_nom}.")
    >>> s.format(a={"nom": "dupont", "prenom": "toto"}, b="tata")
    "Bonjour M. toto dupont."
    """

    def format(self, *args, **kwargs) -> Template:
        try:
            flat_kwargs = pd.json_normalize(kwargs, sep="_").to_dict(orient="records")
            flat_kwargs = flat_kwargs[0]
        except IndexError:
            flat_kwargs = kwargs

        format_dict = FormatDict(flat_kwargs)
        formatted_str = JinjaTemplate(self, keep_trailing_newline=True).render(
            format_dict
        )

        formatted_str = formatted_str.format_map(format_dict)
        while (f_str := formatted_str.format_map(format_dict)) != formatted_str:
            formatted_str = f_str

        return formatted_str


class TemplateRetriever:
    """TemplateRetriever : Abstract class for defining a TemplateRetriever.
    It is done to retrieve a string template identified by a key from a file.
    """

    def __init__(self, table: Any):
        self.table: Any = table

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.table == other.table

    def __repr__(self) -> str:
        return f"{self.__class__}\n{self.table}"

    @staticmethod
    def read(
        filename: Path | str,
        col: Optional[str] = "template",
        force_centroid: bool = False,
        **kwargs,
    ) -> Optional[TemplateRetriever]:
        """read_file : reads a templates file and returns the proper corresponding
        TemplateRetriever object.

        Args:
            filename: File containing the template.
            col: templates column name in a csv file.
            force_centroid: Indicate if the centroid is force or not.
            **kwargs: keyword arguments of the file reader used :
                - json : json.load()
                - ini  : ConfigParser().read()
                - csv  : pandas.read_csv()

        Returns:
            TemplateRetriever object.
        """
        filename = Path(filename)
        if not filename.exists():
            LOGGER.error(f"Template file {filename} does not exist")
            return None

        if filename.suffix == ".json":
            return JsonTemplateRetriever.read_file(filename, **kwargs)
        if filename.suffix == ".ini":
            return IniTemplateRetriever.read_file(filename, **kwargs)
        if filename.suffix == ".csv":
            if force_centroid or "weights" in pd.read_csv(filename).iloc[:, 0].values:
                return CentroidTemplateRetriever.read_file(filename, col=col, **kwargs)
            return CsvTemplateRetriever.read_file(filename, col=col, **kwargs)

        return TemplateRetriever.read_file(filename, **kwargs)

    @classmethod
    def read_file(cls, filename: str | Path, **kwargs) -> TemplateRetriever:
        """
        Class method for instantiating an TemplateRetriever out of a file.

        Args:
            filename: Filename.
            **kwargs: Keyword arguments.

        Returns:
            New cls object
        """
        table = {"filename": Path(filename)}
        table.update(kwargs)
        return cls(table)

    def get(
        self,
        key: Hashable | Sequence[Hashable],
        default: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Retrieves a specific template identified by a key.

        Args:
            key: Key for retrieving our template. If the key is a sequence (list, tuple)
                of keys, then we find the template by searching in subdirectories.
            default: Default value to return if the given key is not in table. Defaults
                to None.
            **kwargs: Keyword arguments.

        Returns:
            The wanted template
        """
        pop_method = kwargs.get("pop_method") or "random"
        pop_methods = {
            "first": lambda x: x[0],
            "last": lambda x: x[-1],
            "random": Settings().random_choice,
        }

        if key in self.table:
            tpl = self.table[key]
            if isinstance(tpl, str):
                return Template(tpl)
            return Template(pop_methods.get(pop_method, pop_method)(tpl))
        try:
            tpl = self.table
            for element in key:
                tpl = tpl.get(element)
                if tpl is None:
                    return Template(default) if default is not None else None
            if isinstance(tpl, str):
                return Template(tpl)
            return Template(pop_methods.get(pop_method, pop_method)(tpl))
        except (Exception,):
            return Template(default) if default is not None else None

    @staticmethod
    def path_by_name(template: str, language: str) -> Path:
        # Returns the template filename according to the given language and name.
        return LOCALE_DIR / language / TEMPLATES_FILENAME[template]

    @staticmethod
    def get_by_name(template: str, language: str, **kwargs) -> TemplateRetriever:
        # Returns the template retriever according to the given name.
        return TemplateRetriever.read(
            TemplateRetriever.path_by_name(template, language), **kwargs
        )

    @staticmethod
    def table_by_name(template: str, language: str) -> Any:
        # Returns the template according to the language and the given name.
        return TemplateRetriever.get_by_name(template, language).table


class JsonTemplateRetriever(TemplateRetriever):
    """JsonTemplateRetriever : TemplateRetriever from json files.

    Currently used by:
        - mfire.text.comment.comment_builder
    """

    @classmethod
    def read_file(
        cls, filename: str | Path, **kwargs
    ) -> Optional[JsonTemplateRetriever]:
        """
        Class method for instantiating an JsonTemplateRetriever out of a file.

        Args:
            filename: File's name.
            **kwargs: Keyword arguments.

        Returns:
            New cls object
        """
        try:
            with open(filename, "r") as json_file:
                return cls(json.load(json_file, **kwargs))
        except OSError:
            LOGGER.error(f"Failed to read json template file {filename}", exc_info=True)
            return None


class IniTemplateRetriever(TemplateRetriever):
    """JsonTemplateRetriever : TemplateRetriever from ini files.

    Currently unused.
    """

    @classmethod
    def read_file(
        cls, filename: str | Path, **kwargs
    ) -> Optional[IniTemplateRetriever]:
        """
        Class method for instantiating an IniTemplateRetriever out of a file.

        Args:
            filename: File's name.
            **kwargs: Keyword arguments.

        Returns:
            New cls object
        """
        config = ConfigParser()
        read_ok = config.read(filename, **kwargs)
        if read_ok:
            return cls(config)

        LOGGER.error(
            f"Failed to read ini template file {filename}",
            filename=filename,
            exc_info=True,
        )
        return None

    def get(
        self,
        key: Hashable | Sequence[Hashable],
        default: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Retrieves a specific template identified by a key.

        Args:
            key: Key for retrieving our template.
            default: Default value to return if the given key is not in table. Defaults
                to None.
            **kwargs: Keyword arguments.

        Returns:
            The wanted template
        """
        if isinstance(key, str):
            key = ("DEFAULT", key)
        try:
            return self.table.get(*key)
        except (Exception,):
            return Template(default) if default is not None else None


class CsvTemplateRetriever(TemplateRetriever):
    def __init__(self, table: pd.DataFrame, col: Optional[str] = "template"):
        super().__init__(table=table)
        self.col = col if col in self.table.columns else self.table.columns[0]
        if idx_columns := table.columns.difference([self.col]).tolist():
            self.table = table.set_index(idx_columns)

    @classmethod
    def read_file(
        cls, filename: str | Path, **kwargs
    ) -> Optional[CsvTemplateRetriever]:
        """
        Class method for instantiating an CsvTemplateRetriever out of a file.

        Args:
            filename: File's name
            **kwargs: Keyword arguments

        Returns:
            New cls object
        """
        try:
            col = kwargs.pop("col", "template")
            return cls(pd.read_csv(filename, **kwargs), col=col)
        except (Exception,):
            LOGGER.error(
                f"Failed to read csv template file {filename}",
                filename=filename,
                exc_info=True,
            )
            return None

    def get(
        self,
        key: Hashable | Sequence[Hashable],
        default: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Retrieves a specific template identified by a key.

        Args:
            key: Key for retrieving our template.
            default: Default value to return if the given key is not in table. Defaults
                to None.
            **kwargs: Keyword arguments

        Returns:
            The wanted template
        """
        try:
            result = self.table.loc[*key].item()
            if not isinstance(result, (pd.Series, pd.DataFrame)):
                return Template(result)
        except (Exception,):
            pass

        return Template(default) if default is not None else None

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.table.equals(other.table)


class CentroidTemplateRetriever(CsvTemplateRetriever):
    """CentroidTemplateRetriever : TemplateRetriever for csv-centroids files.

    Currently used by:
        - mfire.utils.date : for describing short periods
    """

    def __init__(self, table: pd.DataFrame, col: Optional[str] = "template"):
        if "weights" in table.iloc[:, 0].values:
            self.weights = np.array(table.iloc[-1, 1:-1])
            table = table.iloc[:-1, 1:]
        else:
            self.weights = np.ones(len(table.index.names))
        super().__init__(table, col)

    def get(
        self,
        key: Hashable | Sequence[Hashable],
        default: Optional[str] = None,
        **kwargs,
    ) -> str | Tuple[str, list]:
        """get: method used to retrieve a specific template identified by a key.
        It returns the template associated to the nearest centroid of the given key.

        Args:
            key: Key for retrieving our template.
            default: Default value to return if the given key is not in table. Defaults
                to None.
            **kwargs: Keyword arguments

        Returns:
            The wanted template
        """
        centroids = self.table.index.to_frame().values
        try:
            templates = self.table.values.flatten()
            dist = np.sum(np.square(self.weights * (centroids - np.array(key))), axis=1)

            key = dist.argmin()
            tpl = Template(templates[key])
        except Exception:
            key, tpl = None, Template(default)
        return (
            tpl
            if not kwargs.get("return_centroid")
            else (tpl, centroids[key].astype("float").tolist())
        )

    def get_by_dtw(
        self, key: list | np.ndarray, pop_method: Optional[str | Callable] = "random"
    ) -> dict:
        """Retrieves a specific template identified by a key.

        This method returns the template associated with the nearest centroid
        of the given key using the DTW (Dynamic Time Warping) method.

        Args:
            key: Key for retrieving the template.
            pop_method: Method to use if the element retrieved with the key is not a
                string. It can be a string among {"first", "last", "random"}, or it can
                be a function which take the element as input and outputs a str.
                Defaults to "first".

        Returns:
            Dict containing the min distance, the path, the template, the centroid.
        """

        # Define methods for selecting elements
        pop_methods = {
            "first": lambda x: x[0],
            "last": lambda x: x[-1],
            "random": Settings().random_choice,
        }

        # Get centroids
        centroids = self.table.index.to_frame().values

        # Create a list of data, one for each centroid
        datas = []
        for centroid in centroids:
            data = [x for x in centroid if not pd.isnull(x)]
            datas.append(data)

        # Get templates
        templates = self.table.values.flatten()

        # Create a dictionary of distances
        distance_dict = {}
        for index, centroid in enumerate(datas):
            distance_dict[tuple(centroid)] = {
                "distance": dtw.distance_fast(
                    np.array(key, dtype=np.double), np.array(centroid, dtype=np.double)
                ),
                "path": dtw.warping_path_fast(
                    np.array(key, dtype=np.double), np.array(centroid, dtype=np.double)
                ),
                "template": Template(
                    pop_methods.get(pop_method, pop_method)(templates[index].split("|"))
                ),
            }

        # Get result
        result = {"distance": np.inf}
        for centroid, value in distance_dict.items():
            if result["distance"] >= value["distance"]:
                result = value | {"centroid": centroid}
        return result

    def __eq__(self, other: Any) -> bool:
        return super().__eq__(other) and np.all(self.weights == other.weights)
