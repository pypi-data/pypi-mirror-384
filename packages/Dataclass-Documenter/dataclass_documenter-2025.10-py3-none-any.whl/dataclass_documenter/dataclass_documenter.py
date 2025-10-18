#!/usr/bin/env python3
"""Generate documented YAML files from documented dataclasses."""

import dataclasses
import functools
import logging
import textwrap
from typing import get_args, get_origin

import yaml
from docstring_parser import parse as parse_docstring

from .block_meta import BlockMeta
from .typing import type_to_string

LOGGER = logging.getLogger(__name__)


class DataclassDocumenter:
    """Generate markdown and YAML documentation from documented dataclasses."""

    def __init__(self, datacls, name=None, width=120, indent_unit="  "):
        """
        Args:
            datacls:
                The dataclass class or instance to document.

            name:
                The name to use for this class in the documentation. If None,
                the name of the dataclass will be used.

            width:
                The target output width for wrapped comments.

            indent_unit:
                The string to repeat at the start of each line for each level of
                indentation.
        """
        if not dataclasses.is_dataclass(datacls):
            raise ValueError("First argument is not a dataclass.")
        if isinstance(datacls, type):
            self.datacls = datacls
            self.object = None
        else:
            self.datacls = datacls.__class__
            self.object = datacls
        self.name = self.datacls.__name__ if name is None else name
        self.width = int(width)
        self.indent_unit = indent_unit

    @functools.cached_property
    def docstring(self):
        """The parsed docstring."""
        return parse_docstring(self.datacls.__doc__)

    @functools.cached_property
    def fields(self):
        """The fields of the dataclass."""
        return dataclasses.fields(self.datacls)

    @functools.cached_property
    def params(self):
        """The dict mapping parameter names to DocstringParam values."""
        return {param.arg_name: param for param in self.docstring.params}

    def get_param_desc(self, param, default=None, warn=False):
        """
        Get the description of a parameter.

        Args:
            param:
                The parameter name.

            default:
                The default value to return if the parameter lacks a description.

            warn:
                If True, log a warning when the description is missing.

        Returns:
            The parameter description.
        """
        try:
            return self.params[param].description
        except KeyError:
            if warn:
                LOGGER.warning("%s is not documented in the docstring.", param)
            return default

    def get_param_type(self, param):
        """
        Get the type of a parameter.

        Args:
            param:
                The parameter name.

        Returns:
            The parameter type.
        """
        return self.datacls.__annotations__[param]

    def _wrap_yaml_comment(self, comment, indent):
        """
        Wrap a YAML comment.

        Args:
            comment:
                The comment to wrap.

            indent:
                The indentation for each line.

        Returns:
            The wrapped lines.
        """
        indent = f"{indent}# "
        for line in textwrap.wrap(
            comment, width=self.width, initial_indent=indent, subsequent_indent=indent
        ):
            yield line.rstrip()

    def _default_as_yaml(self, name, value, block_meta, override=None):
        """
        Wrap YAML output for embedding in another YAML document.

        Args:
            name:
                The field name.

            value:
                The value.

            block_meta:
                A BlockMeta instance.

            override:
                An optional value different from the given value. This is used
                to display instance values that different from the dataclass's
                default value. The given value will be displayed on a commented
                line above this value.

        Returns:
            A generator over the wrapped YAML lines.
        """
        indent_1, _ = block_meta.indents
        indent_2 = indent_1.replace("-", " ")

        overridden = override is not None and override != value
        if overridden:
            ind_1, _ = block_meta.commented_indents
            ind_1 = ind_2 = ind_1.replace("-", " ")
        else:
            ind_1 = indent_1
            ind_2 = indent_2

        if value is not dataclasses.MISSING:
            text = yaml.dump({name: value})
        else:
            text = f"{name}: ..."

        for i, line in enumerate(text.splitlines()):
            ind = ind_1 if i == 0 else ind_2
            yield f"{ind}{line}"

        if overridden:
            text = yaml.dump({name: override})
            for i, line in enumerate(text.splitlines()):
                ind = indent_1 if i == 0 else indent_2
                yield f"{ind}{line}"

    def _get_nested_dado(self, datacls):
        """
        Get another instance of this class with the same parameters for emitting
        nested YAML.
        """
        return self.__class__(datacls, width=self.width, indent_unit=self.indent_unit)

    def _get_field_yaml_blocks(self, field, block_meta, empty_line):
        """
        Internal method for emitting fields in YAML.

        Args:
            field:
                A` dataclasses.Field instance.

            block_meta:
                A BlockMeta instance.

            empty_line:
                The string of characters to emit for an empty line.

        Returns:
            A generator over blocks of YAML for this field and any nested
            fields.
        """
        field_indent, indent = block_meta.indents

        # Output the description from the docstring.
        yield from self._wrap_yaml_comment(
            self.get_param_desc(field.name, default="Undocumented.", warn=True),
            indent,
        )

        # Recursively document dataclasses.
        if dataclasses.is_dataclass(field.type):
            yield f"{field_indent}{field.name}:"
            try:
                dado = self._get_nested_dado(getattr(self.object, field.name))
            except AttributeError:
                dado = self._get_nested_dado(field.type)
            yield from dado.get_yaml_blocks(
                level=block_meta.indent_level + 1, commented=block_meta.commented
            )
            return

        meta = f"{indent}# Type: {type_to_string(field.type)}"
        try:
            object_value = getattr(self.object, field.name)
        except AttributeError:
            object_value = None
        if field.default is dataclasses.MISSING:
            if field.default_factory is dataclasses.MISSING:
                yield f"{meta} [REQUIRED]"
                default = dataclasses.MISSING
            else:
                yield f"{meta} [OPTIONAL]"
                default = field.default_factory()
            yield from self._default_as_yaml(
                field.name, default, block_meta, override=object_value
            )

        else:
            yield f"{meta} [OPTIONAL]"
            yield from self._default_as_yaml(
                field.name, field.default, block_meta, override=object_value
            )
        emit_empty_line = True
        for arg in get_args(field.type):
            if dataclasses.is_dataclass(arg):
                dado = self._get_nested_dado(arg)
                yield from dado.get_yaml_blocks(
                    header=arg.__name__,
                    level=block_meta.indent_level + 1,
                    commented=True,
                    origin=get_origin(field.type),
                )
                emit_empty_line = False

        if emit_empty_line:
            yield empty_line

    def get_yaml_blocks(self, level=0, header=None, commented=False, origin=None):
        """
        Get commented YAML input for the dataclass.

        Args:
            level:
                The indentation level.

            header:
                An optional header to emit as a comment at the start of the
                output.

            commented:
                If True, comment all fields.

            origin:
                The optional container type for this object, either dict, list
                or None.

        Returns:
            A generator over blocks of YAML.
        """
        block_meta = BlockMeta(
            indent_unit=self.indent_unit,
            indent_level=level,
            commented=commented,
            first=False,
            in_list=origin is list,
        )
        field_indent, indent = block_meta.indents
        empty_line = ""
        if origin is dict:
            yield f"{indent}# String key"
            yield f"{field_indent}key:"
            yield from self.get_yaml_blocks(
                level=level + 1, header=header, commented=commented
            )
            return
        if header is not None:
            yield from self._wrap_yaml_comment(header, indent)
            yield empty_line
        for i, field in enumerate(self.fields):
            block_meta.first = i == 0
            yield from self._get_field_yaml_blocks(field, block_meta, empty_line)

    def get_yaml(self, level=0, commented=False):
        """
        Get commented YAML input for the dataclass.

        Args:
            level:
                Markdown header level.

            commented:
                If True, comment all lines.
        """
        header = self.name
        return "\n".join(
            self.get_yaml_blocks(level=level, header=header, commented=commented)
        )

    def get_markdown(self, level=0):
        """
        Get a markdown description of the dataclass that contains a commented
        example YAML input file.

        Args:
            level:
                Markdown header level.

        Returns:
            The markdown string.
        """
        level = max(level + 1, 1)
        header_prefix = "#" * level

        docstring = self.docstring
        cls_desc = (docstring.short_description, docstring.long_description)
        cls_desc = [desc for desc in cls_desc if desc]
        if cls_desc:
            cls_desc = "\n\n".join(cls_desc)
        return f"""{header_prefix} {self.name}

{cls_desc}

{header_prefix}# Input

~~~yaml
{self.get_yaml()}
~~~

"""
