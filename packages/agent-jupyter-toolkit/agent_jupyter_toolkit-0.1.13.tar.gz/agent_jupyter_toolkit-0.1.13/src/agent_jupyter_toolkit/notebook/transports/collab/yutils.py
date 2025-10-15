from __future__ import annotations

import uuid as _uuid_mod
from typing import Any

import pycrdt

PyText = pycrdt.Text
PyMap = pycrdt.Map


def ytext_to_str(v: Any) -> str:
    """
    Convert YText or plain string to Python string.

    Args:
        v: Value that might be YText, PyText, or regular string

    Returns:
        String representation of the value, empty string if conversion fails
    """
    if hasattr(v, "to_string"):
        try:
            return v.to_string()
        except Exception:
            pass
    return v if isinstance(v, str) else ""


def is_yarray(v: Any) -> bool:
    """
    Check if value is a YArray/PyArray (supports both legacy and pythonic APIs).

    Args:
        v: Value to check

    Returns:
        True if the value appears to be a Y array type
    """
    if v is None:
        return False
    looks_legacy = callable(getattr(v, "length", None)) and callable(getattr(v, "push", None))
    looks_pythonic = hasattr(v, "__len__") and (
        callable(getattr(v, "append", None)) or callable(getattr(v, "insert", None))
    )
    return bool(looks_legacy or looks_pythonic)


def alen(a: Any) -> int:
    """
    Get length of YArray/PyArray (supports both legacy and pythonic APIs).

    Args:
        a: Array-like object

    Returns:
        Length of the array
    """
    f = getattr(a, "length", None)
    if callable(f):
        try:
            return f()
        except TypeError:
            pass
    return len(a)


def aget(a: Any, i: int) -> Any:
    """
    Get element at index from YArray/PyArray (supports both legacy and pythonic APIs).

    Args:
        a: Array-like object
        i: Index to retrieve

    Returns:
        Element at the specified index
    """
    f = getattr(a, "get", None)
    if callable(f):
        try:
            return f(i)
        except TypeError:
            pass
    return a[i]


def adel(a: Any, i: int) -> None:
    """
    Delete element at index from YArray/PyArray (supports both legacy and pythonic APIs).

    Args:
        a: Array-like object
        i: Index to delete
    """
    f = getattr(a, "remove", None)
    if callable(f):
        f(i)
    else:
        del a[i]


def _uuid() -> str:
    """Generate a random hex string suitable for nbformat 'id'."""
    return _uuid_mod.uuid4().hex


def validate_tags(tags: list[str]) -> None:
    """Ensure tags is a list of strings (raise TypeError otherwise)."""
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise TypeError("tags must be a list of strings")


def make_code_cell_dict(
    source: str, metadata: dict[str, Any] | None, tags: list[str] | None
) -> dict[str, Any]:
    """
    Create a code cell dictionary compatible with nbformat.

    Args:
        source: Source code for the cell
        metadata: Optional metadata dict to merge into the cell
        tags: Optional list of tags to add to metadata

    Returns:
        Dictionary representing a code cell in nbformat structure
    """
    md = dict(metadata or {})
    if tags:
        md = dict(md)
        md["tags"] = list(set(tags))
    return {
        "id": _uuid(),
        "cell_type": "code",
        "metadata": md,
        "source": source,
        "outputs": [],
        "execution_count": None,
    }


def make_md_cell_dict(source: str, tags: list[str] | None = None) -> dict[str, Any]:
    """
    Create a markdown cell dictionary compatible with nbformat.

    Args:
        source: Markdown text for the cell
        tags: Optional list of tags to add to metadata

    Returns:
        Dictionary representing a markdown cell in nbformat structure
    """
    md: dict[str, Any] = {}
    if tags:
        md["tags"] = list(set(tags))
    return {
        "id": _uuid(),
        "cell_type": "markdown",
        "metadata": md,
        "source": source,
    }
