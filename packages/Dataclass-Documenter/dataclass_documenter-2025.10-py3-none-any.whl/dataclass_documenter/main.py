#!/usr/bin/env python3
"""Command-line utility for generating dataclass documentation."""

import argparse
import importlib
import importlib.util
import logging
import pathlib
import sys

from . import DataclassDocumenter

LOGGER = logging.getLogger(__name__)

DCLS_SPEC_STR = "<module|file>:<class>"


class DataclassLoaderError(Exception):
    """Custom exception."""


def import_dcls_from_file(path, name):
    """
    Import a dataclass from a filepath.

    Args:
        path:
            The path to the file containing the definition of the dataclass, as
            a pathlib.Path object.

        name:
            The name of the dataclass.

    Returns:
        The dataclass.
    """
    LOGGER.info("Attempting to import %s from file: %s.", name, path)
    try:
        spec = importlib.util.spec_from_file_location(path.stem, str(path))
        if not spec:
            raise DataclassLoaderError(f"Importlib failed to load {path}.")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except (OSError, ImportError) as err:
        raise DataclassLoaderError(err) from err
    sys.modules[mod.__name__] = mod
    try:
        return getattr(mod, name)
    except AttributeError as err:
        raise DataclassLoaderError(err) from err


def import_dcls_from_module(module, name):
    """
    Import a dataclass from a module.

    Args:
        module:
            The module name. It must be importable.

        name:
            The name of the dataclass.

    Returns:
        The dataclass.
    """
    LOGGER.info("Attempting to import %s from module: %s.", name, module)
    try:
        mod = importlib.import_module(module)
    except ImportError:
        sys.path[:] = [str(pathlib.Path.cwd().resolve()), *sys.path]
        try:
            mod = importlib.import_module(module)
        except ImportError as err:
            raise DataclassLoaderError(err) from err
    sys.modules[mod.__name__] = mod
    try:
        return getattr(mod, name)
    except AttributeError as err:
        raise DataclassLoaderError(err) from err


def main(args=None):
    """
    Generate Markdown or YAML for a dataclass.

    Note that this will load the module containing the target dataclass and thus
    execute any top-level code within that module.
    """
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument(
        "dataclass",
        type=str,
        help=(
            f'The target dataclass, specified as "{DCLS_SPEC_STR}", '
            'e.g. "mypkg.mod1:MyDataclass" or "path/to/src.py:MyDataclass".'
        ),
    )
    parser.add_argument(
        "-m",
        "--markdown",
        action="store_true",
        help="Output Markdown documentation instead of just the YAML input file.",
    )
    parser.add_argument(
        "-l",
        "--level",
        type=int,
        default=0,
        help=(
            "Nesting level of output. "
            "For YAML this defines the indentation level. "
            "For Markdown this defines the header level."
        ),
    )
    pargs = parser.parse_args(args=args)
    try:
        mod_name, name = pargs.dataclass.split(":")
    except ValueError as err:
        raise DataclassLoaderError(
            f'Dataclass not specified in format "{DCLS_SPEC_STR}".'
        ) from err
    path = pathlib.Path(mod_name)
    if path.exists():
        dcls = import_dcls_from_file(path, name)
    else:
        dcls = import_dcls_from_module(mod_name, name)

    dado = DataclassDocumenter(dcls)
    if pargs.markdown:
        print(dado.get_markdown(level=pargs.level))
        return
    print(dado.get_yaml(level=pargs.level))


def run_main(args=None):
    """
    Wrapper to run main().
    """
    try:
        main(args=args)
    except KeyboardInterrupt:  # pragma: no cover
        pass
    except DataclassLoaderError as err:
        sys.exit(err)


if __name__ == "__main__":  # pragma: no cover
    run_main()
