"""
Notebook transport implementations.

This package provides concrete implementations of the NotebookDocumentTransport
protocol for different storage and collaboration backends:

- LocalFileDocumentTransport: Local .ipynb files via nbformat
- ContentsApiDocumentTransport: Remote Jupyter server via Contents API
- CollabYjsDocumentTransport: Collaborative editing via Yjs/CRDT
"""

from .collab import CollabYjsDocumentTransport
from .contents import ContentsApiDocumentTransport
from .local_file import LocalFileDocumentTransport

__all__ = [
    "LocalFileDocumentTransport",
    "ContentsApiDocumentTransport",
    "CollabYjsDocumentTransport",
]
