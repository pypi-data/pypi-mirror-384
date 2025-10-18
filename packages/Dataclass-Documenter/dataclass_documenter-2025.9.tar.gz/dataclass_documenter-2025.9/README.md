---
title: README
author: Jan-Michael Rye
---

[insert: badges gitlab]: #

[![Hatch](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch) [![Latest Release](https://gitlab.inria.fr/jrye/dataclass-documenter/-/badges/release.svg)](https://gitlab.inria.fr/jrye/dataclass-documenter/-/tags) [![License](https://img.shields.io/badge/license-MIT-9400d3.svg)](https://spdx.org/licenses/MIT.html) [![Pipeline Status](https://gitlab.inria.fr/jrye/dataclass-documenter/badges/main/pipeline.svg)](https://gitlab.inria.fr/jrye/dataclass-documenter/-/commits/main) [![PyPI](https://img.shields.io/badge/PyPI-Dataclass__Documenter-006dad.svg)](https://pypi.org/project/Dataclass-Documenter/) [![PyPI Downloads](https://static.pepy.tech/badge/Dataclass_Documenter)](https://pepy.tech/projects/Dataclass_Documenter) [![Pylint](https://gitlab.inria.fr/jrye/dataclass-documenter/-/jobs/artifacts/main/raw/pylint/pylint.svg?job=pylint)](https://gitlab.inria.fr/jrye/dataclass-documenter/-/jobs/artifacts/main/raw/pylint/pylint.txt?job=pylint) [![Test Coverage](https://gitlab.inria.fr/jrye/dataclass-documenter/badges/main/coverage.svg)](https://gitlab.inria.fr/jrye/dataclass-documenter)

[/insert: badges gitlab]: #

# Synopsis

A Python package and command-line utility to automate documentation of Python [dataclasses](https://docs.python.org/3/library/dataclasses.html). It can generate the following:

* Commented YAML input files which can be used as user configuration files.
* Markdown output for README files which contain the dataclass docstring and commented YAML.

## Links

[insert: links 2]: #

### GitLab

* [Homepage](https://gitlab.inria.fr/jrye/dataclass-documenter)
* [Source](https://gitlab.inria.fr/jrye/dataclass-documenter.git)
* [Issues](https://gitlab.inria.fr/jrye/dataclass-documenter/issues)
* [Documentation](https://jrye.gitlabpages.inria.fr/dataclass-documenter)
* [GitLab package registry](https://gitlab.inria.fr/jrye/dataclass-documenter/-/packages)

### Other Repositories

* [Python Package Index (PyPI)](https://pypi.org/project/Dataclass-Documenter/)
* [Software Heritage](https://archive.softwareheritage.org/browse/origin/?origin_url=https%3A//gitlab.inria.fr/jrye/dataclass-documenter.git)

[/insert: links 2]: #

# Usage

## Command-Line Utility

The package installs the `dataclass_documenter` which can be used to generate the output from the command-line.


[insert: command_output dataclass_documenter -h]: #

~~~
usage: dataclass_documenter [-h] [-m] [-l LEVEL] dataclass

Generate Markdown or YAML for a dataclass. Note that this will load the module
containing the target dataclass and thus execute any top-level code within
that module.

positional arguments:
  dataclass          The target dataclass, specified as
                     "<module|file>:<class>", e.g. "mypkg.mod1:MyDataclass" or
                     "path/to/src.py:MyDataclass".

options:
  -h, --help         show this help message and exit
  -m, --markdown     Output Markdown documentation instead of just the YAML
                     input file.
  -l, --level LEVEL  Nesting level of output. For YAML this defines the
                     indentation level. For Markdown this defines the header
                     level.

~~~

[/insert: command_output dataclass_documenter -h]: #


## Python API

The package can also be used directly via its API.

~~~python
# Import the documenter class.
from dataclass_documenter import Dataclass_Documenter

# Initialize it with a custom dataclass. Here we assume that MyDataclass is a
defined dataclass.
dado = Dataclass_Documenter(MyDataclass)

# Retrieve YAML and/or Markdown text.
yaml_output = dado.get_yaml()
markdown_output = dado.get_markdown()
~~~


## Example

The following is an example using the dataclasses defined for the unit tests.

[insert: command_output:embedded_markdown scripts/run_in_venv.sh scripts/gen_example.py -l 3]: #

### Dataclass Definitions

Example dataclasses to show the correpondence between the definition and the
generated documentation.

~~~python
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

~~~

### Markdown Output

The following is the Markdowna and YAML output automatically generated from the example dataclasses.

#### ExampleDataclass

Brief description for example dataclass.

This is a longer description. This dataclass is used for testing and
generating an example in the README.

##### Input

~~~yaml
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
  # Type: UnionType[int, float] [OPTIONAL]
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
  # Type: UnionType[int, float] [OPTIONAL]
  #   nested_number: 5

# Undocumented.
# Type: dict[str, NestedExampleDataclass] [OPTIONAL]
nested_dataclass_dict: {}
  # String key
  # key:
    # NestedExampleDataclass

    # A string parameter of the nested dataclass.
    # Type: str [OPTIONAL]
    # nested_string: Another string value.

    # A numerical parameter of the nested dataclass
    # Type: UnionType[int, float] [OPTIONAL]
    # nested_number: 5

~~~

[/insert: command_output:embedded_markdown scripts/run_in_venv.sh scripts/gen_example.py -l 3]: #
