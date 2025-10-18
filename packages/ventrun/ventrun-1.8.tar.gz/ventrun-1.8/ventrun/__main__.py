import argparse

from loguru import logger
from moduvent import discover_modules, emit

from .events import Main


def main(path="."):
    discover_modules(path)
    emit(Main())


def cli_main():
    parser = argparse.ArgumentParser(
        prog="ventrun",
        description="A Python script that bootstraps your application and emits a Main event to ModuVent.",
    )
    parser.add_argument(
        "path", nargs="?", default=".", help="path to the root directory of the project"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    args = parser.parse_args()
    if not args.verbose:
        logger.remove()
    main(args.path)

if __name__ == "__main__":
    cli_main()