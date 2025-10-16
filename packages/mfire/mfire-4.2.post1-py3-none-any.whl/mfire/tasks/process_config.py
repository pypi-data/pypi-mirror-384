import sys

from mfire.configuration.processor import Processor
from mfire.settings import Settings
from mfire.tasks.CLI import CLI


def main(args):
    # Arguments parsing
    args = CLI().parse_args(args)
    print(args)
    print(f"mfire version : {CLI.mfire_version()}")
    # Filenames
    settings = Settings()

    # Running the config processor
    config_processor = Processor(
        configuration_path=settings.config_filename,
        drafting_datetime=args.draftdate,
        rules=args.rules,
    )
    # Retrieving processed configs
    config_processor.process(nproc=args.nproc)


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
