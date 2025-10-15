"""
Jupyter Agent Toolkit.

A comprehensive toolkit for building AI agents that can interact with Jupyter notebooks
and kernels. Provides abstractions for notebook manipulation and kernel execution.

Main Packages:
- notebook: High-level notebook manipulation and transport abstractions
- kernel: Jupyter kernel integration and execution management
- utils: Common utilities and helper functions
"""

from . import kernel, notebook, utils

__all__ = ["kernel", "notebook", "utils"]
