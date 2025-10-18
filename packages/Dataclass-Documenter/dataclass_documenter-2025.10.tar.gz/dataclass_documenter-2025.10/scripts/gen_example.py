#!/usr/bin/env python3
"""Generate example for README."""

import argparse
import pathlib
import inspect

from dataclass_documenter import DataclassDocumenter
from dataclass_documenter.main import import_dcls_from_file


def main(args=None):
    """Main."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-l",
        "--level",
        type=int,
        default=0,
        help="The Markdown nesting level. Default: %(default)d",
    )
    pargs = parser.parse_args(args=args)
    header_prefix = "#" * (pargs.level)

    repo_path = pathlib.Path(__file__).parent.parent
    test_path = repo_path / "test/test_dataclass_documenter.py"
    dcls_1 = import_dcls_from_file(test_path, "ExampleDataclass")
    dcls_2 = import_dcls_from_file(test_path, "NestedExampleDataclass")

    print(
        f"""{header_prefix} Dataclass Definitions

Example dataclasses to show the correpondence between the definition and the
generated documentation.

~~~python
{inspect.getsource(dcls_2)}

{inspect.getsource(dcls_1)}
~~~

{header_prefix} Markdown Output

The following is the Markdowna and YAML output automatically generated from the example dataclasses.
"""
    )

    dado = DataclassDocumenter(dcls_1)
    print(dado.get_markdown(level=pargs.level))


if __name__ == "__main__":
    main()
