"""preprocess_data.py

Preprocessing data 'binary' file
Preprocesses raw model data files (grib files) according to a given "data" configuration
"""

import sys

from mfire.data.data_preprocessor import DataPreprocessor
from mfire.settings.settings import Settings
from mfire.tasks.CLI import CLI


def main(args):
    # Arguments parsing
    args = CLI().parse_args(args)
    print(args)
    print(f"mfire version : {CLI.mfire_version()}")

    # Preprocessing
    preprocessor = DataPreprocessor(rules=args.rules)
    preprocessor.preprocess(
        configuration_path=Settings().data_config_filename, nproc=args.nproc
    )


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
