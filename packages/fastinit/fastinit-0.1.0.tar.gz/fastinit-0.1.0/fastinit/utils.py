"""Utility functions and helpers."""

import re


def to_snake_case(text: str) -> str:
    """Convert text to snake_case."""
    text = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
    text = re.sub("([a-z0-9])([A-Z])", r"\1_\2", text)
    return text.lower()


def to_pascal_case(text: str) -> str:
    """Convert text to PascalCase."""
    return "".join(
        word.capitalize() for word in text.replace("_", " ").replace("-", " ").split()
    )


def to_camel_case(text: str) -> str:
    """Convert text to camelCase."""
    pascal = to_pascal_case(text)
    return pascal[0].lower() + pascal[1:] if pascal else ""


def to_kebab_case(text: str) -> str:
    """Convert text to kebab-case."""
    text = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", text)
    text = re.sub("([a-z0-9])([A-Z])", r"\1-\2", text)
    return text.lower().replace("_", "-")


def pluralize(word: str) -> str:
    """Simple pluralization (for common cases)."""
    if word.endswith("y"):
        return word[:-1] + "ies"
    elif word.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"
    else:
        return word + "s"


def singularize(word: str) -> str:
    """Simple singularization (for common cases)."""
    if word.endswith("ies"):
        return word[:-3] + "y"
    elif word.endswith("es"):
        return word[:-2]
    elif word.endswith("s"):
        return word[:-1]
    else:
        return word
