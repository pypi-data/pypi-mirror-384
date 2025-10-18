#!/usr/bin/env python3
"""
Test DataclassDocumenter class.
"""

import contextlib
import dataclasses
import logging
import re
import unittest
from typing import Optional, get_origin

from dataclass_documenter import DataclassDocumenter


@dataclasses.dataclass
class NestedExampleDataclass:
    """
    Nested dataclass to test recursive documentation.

    Parameters:
        nested_string:
            A string parameter of the nested dataclass.

        nested_number:
            A numerical parameter of the nested dataclass
    """

    nested_string: str = "Another string value."
    nested_number: int | float = 5


# Python 3.14 replaces UnionType with Union in some contexts.
UNION_TYPE = get_origin(dataclasses.fields(NestedExampleDataclass)[1].type).__name__


@dataclasses.dataclass
class ExampleDataclass:  # pylint: disable=too-many-instance-attributes
    """
    Brief description for example dataclass.

    This is a longer description. This dataclass is used for testing and
    generating an example in the README.

    Parameters:
        string:
            A string parameter.

        nested_dataclass:
            A nested dataclass that encapsulates its own parameters.

        integer:
            An integer parameter.

        floats:
            A list of floats.

        opt_string:
            An optional string that may be None.

        nested_dataclass_list:
            List of nested dataclass objects for testing composite types.
    """

    string: str
    nested_dataclass: NestedExampleDataclass
    integer: int = 7
    floats: list[float] = dataclasses.field(default_factory=list)
    opt_string: Optional[str] = None
    undocumented_string: str = "Intentionally undocumented string."
    nested_dataclass_list: list[NestedExampleDataclass] = dataclasses.field(
        default_factory=list
    )
    nested_dataclass_dict: dict[str, NestedExampleDataclass] = dataclasses.field(
        default_factory=dict
    )


EXPECTED_YAML = f"""\
# ExampleDataclass

# A string parameter.
# Type: str [REQUIRED]
string: ...

# A nested dataclass that encapsulates its own parameters.
nested_dataclass:
  # A string parameter of the nested dataclass.
  # Type: str [OPTIONAL]
  nested_string: Another string value.

  # A numerical parameter of the nested dataclass
  # Type: {UNION_TYPE}[int, float] [OPTIONAL]
  nested_number: 5

# An integer parameter.
# Type: int [OPTIONAL]
integer: 7

# A list of floats.
# Type: list[float] [OPTIONAL]
floats: []

# An optional string that may be None.
# Type: str [OPTIONAL]
opt_string: null

# Undocumented.
# Type: str [OPTIONAL]
undocumented_string: Intentionally undocumented string.

# List of nested dataclass objects for testing composite types.
# Type: list[NestedExampleDataclass] [OPTIONAL]
nested_dataclass_list: []
  # NestedExampleDataclass

  # A string parameter of the nested dataclass.
  # Type: str [OPTIONAL]
  # - nested_string: Another string value.

  # A numerical parameter of the nested dataclass
  # Type: {UNION_TYPE}[int, float] [OPTIONAL]
  #   nested_number: 5

# Undocumented.
# Type: dict[str, NestedExampleDataclass] [OPTIONAL]
nested_dataclass_dict: {{}}
  # String key
  # key:
    # NestedExampleDataclass

    # A string parameter of the nested dataclass.
    # Type: str [OPTIONAL]
    # nested_string: Another string value.

    # A numerical parameter of the nested dataclass
    # Type: {UNION_TYPE}[int, float] [OPTIONAL]
    # nested_number: 5
"""


EXPECTED_MARKDOWN = f"""\
# ExampleDataclass

Brief description for example dataclass.

This is a longer description. This dataclass is used for testing and
generating an example in the README.

## Input

~~~yaml
{EXPECTED_YAML}
~~~

"""


@contextlib.contextmanager
def disable_logger():
    """
    Context manager for disabling a specific logger.

    Args:
        name:
            The logger name to disable.
    """
    logger = logging.getLogger("dataclass_documenter.dataclass_documenter")
    prev = logger.disabled
    logger.disabled = True
    try:
        yield None
    finally:
        logger.disabled = prev


class TestDataclassDocumenter(unittest.TestCase):
    """
    Test the DataclassDocumenter class.
    """

    def setUp(self):
        self.dado = DataclassDocumenter(ExampleDataclass)
        self.maxDiff = None  # pylint: disable=invalid-name

    def test_non_dataclass(self):
        """Passing a non-dataclass argument raises ValueError."""
        with self.assertRaises(ValueError):
            DataclassDocumenter(int)

    def test_get_param_type(self):
        """Parameter types are returned."""
        self.assertIs(str, self.dado.get_param_type("string"))
        self.assertIs(int, self.dado.get_param_type("integer"))

    # This indireclty tests YAML generation.
    def test_markdown(self):
        """Markdown is correctly generated from dataclasses."""
        with disable_logger():
            self.assertEqual(EXPECTED_MARKDOWN, self.dado.get_markdown())

    def test_markdown_level(self):
        """Markdown headers are correctly set."""
        for level in range(0, 5):
            repl = "#" * (level + 1)
            expected = re.sub(r"^#", repl, EXPECTED_MARKDOWN, count=2, flags=re.M)
            with self.subTest(level=level), disable_logger():
                self.assertEqual(expected, self.dado.get_markdown(level=level))

    def test_commented_yaml(self):
        """Commented YAML is correctly generated from dataclasses."""
        expected_yaml = re.sub(
            r"^(\s*)([^#\s])", r"\1# \2", EXPECTED_YAML, flags=re.MULTILINE
        )
        with disable_logger():
            self.assertEqual(expected_yaml, self.dado.get_yaml(commented=True))

    def test_undocumented_parameters_warning(self):
        """Undocumented parameters create warnings."""
        expected = (
            "WARNING:dataclass_documenter.dataclass_documenter:"
            "undocumented_string is not documented in the docstring."
        )
        with self.assertLogs(level=logging.WARNING) as ctx:
            self.dado.get_markdown()
            self.assertIn(expected, ctx.output)

    def test_dataclass_instance(self):
        """The values of dataclass instances are documented."""
        nested = NestedExampleDataclass(nested_string="Nested override")
        example = ExampleDataclass(string="Override", nested_dataclass=nested)
        dado = DataclassDocumenter(example)
        expected = EXPECTED_MARKDOWN.replace(
            "string: ...", "# string: ...\nstring: Override"
        ).replace(
            "  nested_string: Another string value.",
            "  # nested_string: Another string value.\n  nested_string: Nested override",
        )
        with disable_logger():
            self.assertEqual(expected, dado.get_markdown())


if __name__ == "__main__":
    unittest.main()
