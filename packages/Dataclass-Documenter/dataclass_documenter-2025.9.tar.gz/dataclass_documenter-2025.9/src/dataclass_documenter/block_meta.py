#!/usr/bin/env python3
"""YAML block metadata."""

import dataclasses


@dataclasses.dataclass
class BlockMeta:
    """
    Metadata for YAML blocks.

    Parameters:
        indent_unit:
            The string to repeat for each level of indentation.

        indent_level:
            The indentation level.

        commented:
            True if the entries should be deactivated by comments.

        first:
            True if this is the first block within its context.

        in_list:
            True if this block is containined in a list.
    """

    indent_unit: str = "  "
    indent_level: int = 0
    commented: bool = False
    first: bool = True
    in_list: bool = False

    @property
    def indents(self):
        """
        The field and non-field indent strings based on the current block
        context.
        """
        field_indent = indent = self.indent_unit * self.indent_level
        if self.commented:
            field_indent = f"{indent}# "

        if self.in_list:
            if self.first:
                field_indent += f"-{self.indent_unit[1:]}"
            else:
                field_indent += self.indent_unit
        return field_indent, indent

    @property
    def commented_indents(self):
        """
        Same as indents but with forced commenting.
        """
        commented = self.commented
        try:
            self.commented = True
            return self.indents
        finally:
            self.commented = commented
