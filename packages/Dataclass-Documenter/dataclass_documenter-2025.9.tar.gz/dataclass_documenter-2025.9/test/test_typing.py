#!/usr/bin/env python3
"""
Test typing submodule.
"""

import unittest
from typing import Optional, Union

from dataclass_documenter import typing as dt


class Dummy:  # pylint: disable=too-few-public-methods
    """Dummy class for testing unions."""


def get_test_types():
    """
    Get pairs of types and their string names.
    """
    for typ in (int, float, bool, str):
        name = typ.__name__
        yield typ, name
        yield Union[typ, Dummy], f"Union[{name}, Dummy]"


TEST_TYPES = dict(get_test_types())


class TestTyping(unittest.TestCase):
    """
    Test the typing submodule.
    """

    def test_is_optional(self):
        """Optional types are detected."""
        for typ in TEST_TYPES:
            with self.subTest(type=typ):
                self.assertFalse(dt.is_optional(typ))
                self.assertTrue(dt.is_optional(Optional[typ]))

    def test_strip_optional(self):
        """Recover base type from optional type."""
        for typ in TEST_TYPES:

            with self.subTest(type=typ):
                self.assertIs(dt.strip_optional(typ), typ)
                self.assertIs(dt.strip_optional(Optional[typ]), typ)

    def test_type_to_string(self):
        """Types are converted to strings."""
        for typ, name in TEST_TYPES.items():
            with self.subTest(type=typ):
                self.assertEqual(dt.type_to_string(typ), name)
                self.assertEqual(dt.type_to_string(Optional[typ]), name)

    def test_ellipsis(self):
        """The ellipsis type is converted to its string literal."""
        self.assertEqual(dt.type_to_string(Ellipsis), "...")

    def test_singletons(self):
        """Singleton types are converted to their names."""
        singletons = {True: "True", False: "False", None: "None"}
        for singleton, name in singletons.items():
            with self.subTest(singleton=singleton):
                self.assertEqual(dt.type_to_string(singleton), name)


if __name__ == "__main__":
    unittest.main()
