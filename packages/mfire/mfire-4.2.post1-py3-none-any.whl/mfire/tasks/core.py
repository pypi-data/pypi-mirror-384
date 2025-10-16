import sys

from mfire.production import ProductionManager
from mfire.settings import Settings, get_logger

# Own package imports
from mfire.tasks.CLI import CLI

LOGGER = get_logger(name="core.mod", bind="core")


def main(args):
    # Arguments parsing
    args = CLI().parse_args(args)
    print(args)
    print(f"mfire version : {CLI.mfire_version()}")
    production_manager = ProductionManager.load(Settings().prod_config_filename)
    production_manager.compute(nproc=args.nproc)


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
