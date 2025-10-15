"""
Local file system notebook transport.

This module provides the LocalFileDocumentTransport class for reading and writing
Jupyter notebooks directly from the local file system using nbformat. This transport
is ideal for applications that need to work with .ipynb files stored locally.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import nbformat
from nbformat.notebooknode import NotebookNode

from ..transport import NotebookDocumentTransport

log = logging.getLogger(__name__)


class LocalFileDocumentTransport(NotebookDocumentTransport):
    """
    Notebook transport backed by a local .ipynb file via `nbformat`.

    This transport provides direct file system access to Jupyter notebook files,
    using the standard nbformat library for reading and writing. It's ideal for
    local development, testing, and scenarios where notebooks need to be persisted
    to the local file system.

    Key Features:
        - Direct file system access with atomic writes
        - Full nbformat compatibility and validation
        - Automatic directory creation for notebook paths
        - Efficient in-memory operations with selective persistence
        - Thread-safe through synchronous file operations

    File Operations:
        - Each mutation reads the file, applies in-memory changes, then writes back
        - Uses atomic write operations (temp file + rename) to prevent corruption
        - Automatically creates parent directories as needed
        - Preserves NotebookNode structure for nbformat compatibility

    Concurrency:
        There is no internal locking; call sites should serialize access if used
        concurrently from multiple tasks/threads. For concurrent access, consider
        using ContentsApiDocumentTransport with a Jupyter server instead.

    Example:
        ```python
        transport = LocalFileDocumentTransport("/path/to/notebook.ipynb")

        await transport.start()  # Creates file if missing

        # Add content
        await transport.append_markdown_cell("# Local Analysis")
        code_idx = await transport.append_code_cell("import numpy as np")

        # Update with results
        outputs = [{"output_type": "execute_result", "data": {"text/plain": "42"}}]
        await transport.update_cell_outputs(code_idx, outputs, execution_count=1)

        # File is automatically saved after each operation
        await transport.stop()  # No-op for local files
        ```

    Lifecycle:
        - `start()` ensures the target file exists (creating a minimal notebook if not)
        - `stop()` is a no-op (no persistent handles are held open)
        - Methods are idempotent where practical
    """

    def __init__(self, path: str) -> None:
        """
        Initialize the local file transport.

        Args:
            path: Filesystem path to a .ipynb file. Parent directories will be created
                  automatically. The file itself will be created on `start()` if missing.

        Example:
            ```python
            # Absolute path
            transport = LocalFileDocumentTransport("/home/user/notebooks/analysis.ipynb")

            # Relative path (resolved relative to current working directory)
            transport = LocalFileDocumentTransport("./notebooks/analysis.ipynb")
            ```
        """
        self._path = Path(path)
        self._on_change: list[Callable[[dict[str, Any]], None]] = []

    async def start(self) -> None:
        """
        Ensure the directory exists and create an empty notebook if absent.
        Idempotent.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            log.info("Creating new notebook at %s", self._path)
            nb = nbformat.v4.new_notebook()
            self._atomic_write(nb)

    async def stop(self) -> None:
        """No persistent resources to release for local files."""
        return

    async def is_connected(self) -> bool:
        """Always True for local files (the file may still be missing before `start()`)."""
        return True

    async def fetch(self) -> dict[str, Any]:
        """
        Read and return the notebook as a plain nbformat-like dict.

        Notes:
            nbformat.read(..., as_version=4) returns a NotebookNode (dict-like).
            We JSON round-trip to convert nested NotebookNodes into plain dict/list
            so callers (and other transports) see a consistent JSON-serializable shape.
        """
        nb = self._read_nb()  # NotebookNode
        return json.loads(nbformat.writes(nb, version=4))

    async def save(self, content: dict[str, Any]) -> None:
        """
        Overwrite the notebook with the provided nbformat-like dict.
        """
        nb = nbformat.from_dict(content)
        self._atomic_write(nb)
        for cb in self._on_change:
            cb({"op": "save"})

    async def append_code_cell(
        self,
        source: str,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> int:
        """
        Append a code cell and return its zero-based index.
        """
        nb = self._read_nb()
        cell = nbformat.v4.new_code_cell(source)
        cell["id"] = cell.get("id") or uuid.uuid4().hex
        cell["metadata"].update(metadata or {})
        if tags is not None:
            _validate_tags(tags)
            cell["metadata"].setdefault("tags", [])
            cell["metadata"]["tags"] = list(set(cell["metadata"]["tags"]).union(tags))
        nb.cells.append(cell)
        self._atomic_write(nb)
        idx = len(nb.cells) - 1
        for cb in self._on_change:
            cb({"op": "cells-mutated", "kind": "append_code", "index": idx})
        return idx

    async def insert_code_cell(
        self,
        index: int,
        source: str,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """
        Insert a code cell at a specific index (0..len). `len` means append.
        Raises IndexError if out of range.
        """
        nb = self._read_nb()
        if index < 0 or index > len(nb.cells):
            raise IndexError(f"insert_code_cell: index {index} out of range 0..{len(nb.cells)}")

        cell = nbformat.v4.new_code_cell(source)
        cell["id"] = cell.get("id") or uuid.uuid4().hex
        cell["metadata"].update(metadata or {})
        if tags is not None:
            _validate_tags(tags)
            cell["metadata"].setdefault("tags", [])
            cell["metadata"]["tags"] = list(set(cell["metadata"]["tags"]).union(tags))

        nb.cells.insert(index, cell)
        self._atomic_write(nb)
        for cb in self._on_change:
            cb({"op": "cells-mutated", "kind": "insert_code", "index": index})

    async def update_cell_outputs(
        self,
        index: int,
        outputs: list[dict[str, Any]],
        execution_count: int | None,
    ) -> None:
        """
        Replace outputs and execution count of the code cell at `index`.
        Raises IndexError if the index is out of range.
        """
        if not isinstance(outputs, list) or not all(
            isinstance(o, (dict, NotebookNode)) for o in outputs
        ):
            raise TypeError("update_cell_outputs: 'outputs' must be a list of nbformat-like dicts")

        nb = self._read_nb()
        if index < 0 or index >= len(nb.cells):
            raise IndexError(
                f"update_cell_outputs: index {index} out of range 0..{len(nb.cells) - 1}"
            )

        # Coerce each output dict → NotebookNode so nbformat.write() can attribute-access
        coerced: list[NotebookNode] = []
        for o in outputs or []:
            coerced.append(o if isinstance(o, NotebookNode) else nbformat.from_dict(o))  # type: ignore[arg-type]

        nb.cells[index]["outputs"] = coerced
        nb.cells[index]["execution_count"] = execution_count

        self._atomic_write(nb)
        for cb in self._on_change:
            cb({"op": "cells-mutated", "kind": "outputs", "index": index})

    async def append_markdown_cell(
        self,
        source: str,
        tags: list[str] | None = None,
    ) -> int:
        """
        Append a markdown cell and return its zero-based index.
        """
        nb = self._read_nb()
        cell = nbformat.v4.new_markdown_cell(source)
        cell["id"] = cell.get("id") or uuid.uuid4().hex
        if tags is not None:
            _validate_tags(tags)
            cell["metadata"].setdefault("tags", [])
            cell["metadata"]["tags"] = list(set(cell["metadata"]["tags"]).union(tags))
        nb.cells.append(cell)
        self._atomic_write(nb)
        idx = len(nb.cells) - 1
        for cb in self._on_change:
            cb({"op": "cells-mutated", "kind": "append_markdown", "index": idx})
        return idx

    async def insert_markdown_cell(
        self,
        index: int,
        source: str,
        tags: list[str] | None = None,
    ) -> None:
        """
        Insert a markdown cell at a specific index (0..len). `len` means append.
        Raises IndexError if out of range.
        """
        nb = self._read_nb()
        if index < 0 or index > len(nb.cells):
            raise IndexError(f"insert_markdown_cell: index {index} out of range 0..{len(nb.cells)}")

        cell = nbformat.v4.new_markdown_cell(source)
        cell["id"] = cell.get("id") or uuid.uuid4().hex
        if tags is not None:
            _validate_tags(tags)
            cell["metadata"].setdefault("tags", [])
            cell["metadata"]["tags"] = list(set(cell["metadata"]["tags"]).union(tags))

        nb.cells.insert(index, cell)
        self._atomic_write(nb)
        for cb in self._on_change:
            cb({"op": "cells-mutated", "kind": "insert_markdown", "index": index})

    async def set_cell_source(self, index: int, source: str) -> None:
        """
        Replace the source text of the cell at `index` (code or markdown).
        Raises IndexError if out of range.
        """
        nb = self._read_nb()
        if index < 0 or index >= len(nb.cells):
            raise IndexError(f"set_cell_source: index {index} out of range 0..{len(nb.cells) - 1}")
        nb.cells[index]["source"] = source
        self._atomic_write(nb)
        for cb in self._on_change:
            cb({"op": "cells-mutated", "kind": "set_source", "index": index})

    async def delete_cell(self, index: int) -> None:
        """
        Delete the cell at `index`.
        Raises IndexError if out of range.
        """
        nb = self._read_nb()
        if index < 0 or index >= len(nb.cells):
            raise IndexError(f"delete_cell: index {index} out of range 0..{len(nb.cells) - 1}")
        del nb.cells[index]
        self._atomic_write(nb)
        for cb in self._on_change:
            cb({"op": "cells-mutated", "kind": "delete", "index": index})

    def on_change(self, cb: Callable[[dict[str, Any]], None]) -> None:
        """
        Register a callback invoked after `save()` or a cell mutation.
        Callback signature: `cb(event: Dict[str, Any]) -> None`.
        """
        self._on_change.append(cb)

    def _read_nb(self):
        """Centralized reader (nbformat v4)."""
        return nbformat.read(self._path, as_version=4)

    def _atomic_write(self, nb) -> None:
        """
        Write notebook content atomically to avoid partial/corrupted files.

        Strategy:
            - write to a temporary file in the same directory
            - replace the target path in a single operation
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", delete=False, dir=self._path.parent, encoding="utf-8") as tf:
            nbformat.write(nb, tf)
            tmp_name = tf.name
        Path(tmp_name).replace(self._path)


def _validate_tags(tags: list[str]) -> None:
    """Ensure tags is a list of strings (raise TypeError otherwise)."""
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise TypeError("tags must be a list of strings")
