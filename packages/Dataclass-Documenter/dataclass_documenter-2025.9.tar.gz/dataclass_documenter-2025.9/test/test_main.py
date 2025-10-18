#!/usr/bin/env python3
"""
Test main submodule.
"""

import contextlib
import dataclasses
import io
import pathlib
import tempfile
import unittest

from dataclass_documenter import main as dm

THIS_PATH = pathlib.Path(__file__).resolve()


@dataclasses.dataclass
class Example:
    """
    Example dataclass.

    Parameters:
        string:
            A string parameter.
    """

    string: str


EXPECTED_YAML = """\
# Example

# A string parameter.
# Type: str [REQUIRED]
string: ...

"""

EXPECTED_MARKDOWN = f"""\
# Example

Example dataclass.

## Input

~~~yaml
{EXPECTED_YAML}~~~


"""


class TestMain(unittest.TestCase):
    """
    Test the main submodule.
    """

    def setUp(self):
        self.maxDiff = None  # pylint: disable=invalid-name

    def test_yaml(self):
        """Main prints YAML."""
        args = [f"{THIS_PATH}:Example"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            dm.run_main(args=args)
        self.assertEqual(buf.getvalue(), EXPECTED_YAML)

    def test_markdown(self):
        """Main prints Markdown."""
        args = [f"{THIS_PATH}:Example", "--markdown"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            dm.run_main(args=args)
        self.assertEqual(buf.getvalue(), EXPECTED_MARKDOWN)

    def test_load_module(self):
        """Load dataclass from module."""
        args = [f"{__name__}:Example"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            dm.main(args=args)
        self.assertEqual(buf.getvalue(), EXPECTED_YAML)

    def test_value_error(self):
        """Invalid arguments raise DataclassLoaderError errors."""
        with self.assertRaises(dm.DataclassLoaderError):
            dm.main(args=[str(THIS_PATH)])

    def test_non_python_file(self):
        """Non-Python files raise DataclassLoaderError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = pathlib.Path(tmp_dir) / "foo.txt"
            path.write_text("foo")
            args = [f"{path}:Example"]
            with self.assertRaises(dm.DataclassLoaderError):
                dm.main(args=args)

    def test_os_error(self):
        """OSErrors raises DataclassLoaderError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = pathlib.Path(tmp_dir)
            args = [f"{tmp_dir / 'foo.py'}:Example"]
            with self.assertRaises(dm.DataclassLoaderError):
                dm.main(args=args)

    def test_import_error(self):
        """ImportError raises DataclassLoaderError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = pathlib.Path(tmp_dir) / "foo.py"
            path.write_text("import ioursfdfhhrwrwggg")
            args = [f"{path}:Example"]
            with self.assertRaises(dm.DataclassLoaderError):
                dm.main(args=args)

    def test_attribute_error(self):
        """Missing dataclass in file raises DataclassLoaderError."""
        for src in (THIS_PATH, __name__):
            with self.subTest(source=src):
                args = [f"{src}:MissingExample"]
                with self.assertRaises(dm.DataclassLoaderError):
                    dm.main(args=args)

    def test_run_main_exit_with_error(self):
        """Errors exit with non-zero exit codes."""
        with self.assertRaisesRegex(
            SystemExit, "Dataclass not specified in format"
        ) as cm:
            dm.run_main(args=[str(THIS_PATH)])
        self.assertNotEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
