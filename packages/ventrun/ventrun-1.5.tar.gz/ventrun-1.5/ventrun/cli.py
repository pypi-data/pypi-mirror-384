import argparse

from .events import Main
from loguru import logger
from moduvent import discover_modules, emit


def main():
    parser = argparse.ArgumentParser(prog="ventrun", description="A Python script that bootstraps your application and emits a Main event to ModuVent.")
    parser.add_argument("path", nargs="?", default=".", help="path to the root directory of the project")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    args = parser.parse_args()
    if not args.verbose:
        logger.remove()
    discover_modules(args.path)
    emit(Main())
