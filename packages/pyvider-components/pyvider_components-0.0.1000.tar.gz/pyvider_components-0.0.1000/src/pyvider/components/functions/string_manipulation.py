#
# pyvider/components/functions/string_manipulation.py
#

from typing import Any

from provide.foundation import logger
from provide.foundation.errors import resilient
from provide.foundation.formatting import (
    format_size,
    pluralize,
    to_camel_case,
    to_kebab_case,
    to_snake_case,
    truncate,
)
from pyvider.exceptions import FunctionError
from pyvider.hub import register_function

from .type_conversion_functions import tostring


@register_function(name="upper", summary="Converts a string to uppercase.")
def upper(input_str: str | None) -> str | None:
    if input_str is None:
        return None
    return input_str.upper()


@register_function(name="lower", summary="Converts a string to lowercase.")
def lower(input_str: str | None) -> str | None:
    if input_str is None:
        return None
    return input_str.lower()


@register_function(
    name="format", summary="Formats a string using positional arguments."
)
@resilient()
def format_str(template: str | None, values: list[Any] | None) -> str | None:
    if template is None:
        return None
    value_list = values or []
    try:
        str_values = [tostring(v) for v in value_list]
        result = template.format(*str_values)
        logger.debug("Formatted string", template=template, value_count=len(value_list))
        return result
    except IndexError as e:
        raise FunctionError(
            f"Formatting failed: not enough values for template '{template}'."
        ) from e


@register_function(name="join", summary="Joins list elements with a delimiter.")
def join(delimiter: str | None, strings: list[Any] | None) -> str | None:
    if strings is None:
        return None
    delimiter_str = delimiter or ""
    return delimiter_str.join(map(tostring, strings))


@register_function(name="split", summary="Splits a string by a delimiter.")
def split(delimiter: str | None, string: str | None) -> list[str] | None:
    if string is None:
        return None
    delimiter_str = delimiter or ""
    if not string:
        return []
    return string.split(delimiter_str)


@register_function(name="replace", summary="Replaces occurrences of a substring.")
def replace(
    string: str | None, search: str | None, replacement: str | None
) -> str | None:
    if string is None:
        return None
    return string.replace(search or "", replacement or "")


@register_function(name="to_snake_case", summary="Converts text to snake_case.")
def snake_case(text: str | None) -> str | None:
    """Convert text to snake_case using provide-foundation utilities."""
    if text is None:
        return None
    return to_snake_case(text)


@register_function(name="to_camel_case", summary="Converts text to camelCase.")
def camel_case(text: str | None, upper_first: bool = False) -> str | None:
    """Convert text to camelCase using provide-foundation utilities."""
    if text is None:
        return None
    return to_camel_case(text, upper_first=upper_first)


@register_function(name="to_kebab_case", summary="Converts text to kebab-case.")
def kebab_case(text: str | None) -> str | None:
    """Convert text to kebab-case using provide-foundation utilities."""
    if text is None:
        return None
    return to_kebab_case(text)


@register_function(name="format_size", summary="Formats bytes as human-readable size.")
def format_file_size(size_bytes: int | None, precision: int = 1) -> str | None:
    """Format bytes as human-readable size using provide-foundation utilities."""
    if size_bytes is None:
        return None
    return format_size(size_bytes, precision)


@register_function(name="truncate", summary="Truncates text to specified length.")
def truncate_text(
    text: str | None, max_length: int = 100, suffix: str = "..."
) -> str | None:
    """Truncate text to specified length using provide-foundation utilities."""
    if text is None:
        return None
    return truncate(text, max_length, suffix)


@register_function(name="pluralize", summary="Pluralizes a word based on count.")
def pluralize_word(
    word: str | None, count: int = 1, plural: str | None = None
) -> str | None:
    """Pluralize a word based on count using provide-foundation utilities."""
    if word is None:
        return None
    return pluralize(word, count, plural)


# ✂️📝🎯
