import argparse
import os
import re
from pathlib import Path

from mfire.settings import RULES_NAMES, Settings
from mfire.utils.date import Datetime


def _get_version(version_filename: str | Path) -> str:
    """
    Retrieves and checks version string from VERSION file

    Args:
        version_filename: File containing the version string

    Returns:
        Version string

    Raises:
        RuntimeError: Raised when VERSION file or string if malformed.
    """
    with open(version_filename, "r") as fp:
        version_lines = fp.readlines()
        if len(version_lines) != 1:
            raise RuntimeError("VERSION file is malformed")
        version = version_lines[0]
        version_pattern = re.compile(r"^(\d+).(\d+)(rc\d+|.dev\d+|.post\d+)?$")
        if not version_pattern.match(version):
            raise RuntimeError("VERSION string is malformed")
        return version


__version__ = _get_version(Path(__file__).parents[1] / "VERSION")


class CLI:
    """Class for centralizing mfire's Command Line Interface"""

    def __init__(self):
        self.parser = self.get_parser()

    @staticmethod
    def mfire_version():
        return __version__

    @classmethod
    def get_parser(cls):
        version_header = f"{__name__} ({__version__})"
        parser = argparse.ArgumentParser(prog=f"{version_header}")
        # version
        parser.add_argument("--version", action="version", version=version_header)
        # general not in settings
        parser.add_argument(
            "-d",
            "--draftdate",
            default=Datetime(),
            help="Drafting or launching datetime",
        )
        parser.add_argument(
            "-r",
            "--rules",
            default=RULES_NAMES[0],
            choices=RULES_NAMES,
            help="Name of the rules convention (for files selection). "
            f"This argument must belong to the following list: {RULES_NAMES}",
        )
        parser.add_argument(
            "-n",
            "--nproc",
            type=int,
            default=os.cpu_count(),
            help=f"Number of CPUs [1:{os.cpu_count()}]",
        )
        parser.add_argument(
            "-t",
            "--timeout",
            help="Maximum duration in seconds of a task. Default is 600.",
        )
        parser.add_argument(
            "-e",
            "--eccodes-definition-path",
            help="Set to the folder containing the set of definition files "
            "you want ecCodes to use instead of the default one.",
        )
        # general in settings
        parser.add_argument(
            "--altitudes-dirname",
            help=(
                "Directory containing NetCDF with Digital Elevation Model "
                "for each geometry"
            ),
        )
        parser.add_argument(
            "--alternate-max",
            type=int,
            help="Maximum number of alternates to use for a single file",
        )
        # working_directory
        #   general working_dir
        parser.add_argument("-w", "--working-dir", help="Working directory.")
        #   configs files
        parser.add_argument("--config-filename", help="Path to the configuration file")
        parser.add_argument(
            "--mask-config-filename", help="Path to the masks's configuration file"
        )
        parser.add_argument(
            "--data-config-filename", help="Path to the data's configuration file"
        )
        parser.add_argument(
            "--prod-config-filename", help="Path to the production's configuration file"
        )
        parser.add_argument(
            "--version-config-filename", help="Path to the version's configuration file"
        )
        #   mask directory
        parser.add_argument(
            "--mask-dirname", help="Path to the masks's local storage directory"
        )
        #   data directory
        parser.add_argument(
            "--data-dirname", help="Path to the data's local storage directory"
        )
        #   output directory
        parser.add_argument(
            "--output-dirname",
            help="Path to the output production's local storage directory",
        )
        #   output filename
        parser.add_argument(
            "--output_archive_filename", help="Path to the output tgz archive file"
        )
        parser.add_argument(
            "--disable_random",
            default=Settings().disable_random,
            help="To disable the random production",
            action="store_true",
        )
        # logging
        parser.add_argument(
            "--log-level",
            help="The logging level.",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        )
        parser.add_argument(
            "--log-file-name", default=None, type=str, help="The logging file's name."
        )
        parser.add_argument(
            "--log-file-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="The logging level of the given log file.",
        )
        # vortex
        parser.add_argument(
            "--vapp", help="Application's name (default is 'Promethee')"
        )
        parser.add_argument(
            "--vconf", help="Application's config name (default is 'msb')"
        )
        parser.add_argument(
            "--experiment", help="Application's name (default is 'TEST')"
        )
        return parser

    def parse_args(
        self, args: list = None, namespace: argparse.Namespace = None
    ) -> argparse.Namespace:
        # retrieving args
        res = self.parser.parse_args(args=args, namespace=namespace)

        # settings
        #   setting the full working_directory first
        if res.working_dir is not None:
            Settings.set_full_working_dir(working_dir=res.working_dir)
        #   setting the rest
        Settings.set(**res.__dict__)

        # Settings des variables d'environements hors mfire :
        # ECCODES_DEFINITION_PATH : chemin vers les definitions d'ECCODES
        if res.eccodes_definition_path is not None:
            os.environ["ECCODES_DEFINITION_PATH"] = res.eccodes_definition_path

        # puis on renvoie les args pour ce qui n'est pas directement modifiable ici
        return res
