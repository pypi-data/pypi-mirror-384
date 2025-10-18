#!/usr/bin/env python3
"""Typing functions."""

from typing import Union, get_args, get_origin


def is_optional(typ):
    """
    Check if a type is Optional.

    Args:
        typ:
            The type to check.

    Returns:
        True if the type is optional, False otherwise.
    """
    return get_origin(typ) is Union and type(None) in get_args(typ)


def strip_optional(typ):
    """
    Strip outer optional types.

    Args:
        typ:
            The type to strip.

    Returns:
        The first non-optional type within the type.
    """
    while is_optional(typ):
        args = tuple(a for a in get_args(typ) if a is not type(None))
        if len(args) > 1:
            typ = Union[*args]
        else:
            typ = args[0]
    return typ


def get_type_name(typ):
    """
    Get the name of a type.

    Returns:
        The name as a string.
    """
    if typ is Ellipsis:
        return "..."
    try:
        return typ.__name__
    except AttributeError:
        return str(typ)


def type_to_string(typ):
    """
    Get a string representation of a type. Optional types are stripped down to
    their underlying type.

    Args:
        typ:
            The type to represent.

    Returns:
        The string representing the type.
    """
    typ = strip_optional(typ)
    orig = get_origin(typ)
    name = get_type_name(typ) if orig is None else get_type_name(orig)
    args = get_args(typ)
    if args:
        args = ", ".join(type_to_string(a) for a in args)
        return f"{name}[{args}]"
    return name
