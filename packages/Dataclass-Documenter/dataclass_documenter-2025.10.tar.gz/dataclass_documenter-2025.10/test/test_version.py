#!/usr/bin/env python3
"""
Test version submodule.
"""

import unittest

from dataclass_documenter import version as dv


class TestVersion(unittest.TestCase):
    """
    Test the version submodule.
    """

    def test_version(self):
        """Version is a string."""
        self.assertIsInstance(dv.VERSION, str)

    def test_version_tuple(self):
        """Version tuple is a tuple."""
        self.assertIsInstance(dv.VERSION_TUPLE, tuple)


if __name__ == "__main__":
    unittest.main()
