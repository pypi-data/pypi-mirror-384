"""
Canonical dataclasses and types for the kernel subsystem.
Used by both local (ZMQ) and remote (HTTP+WS) execution paths.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

# Type Aliases
OutputCallback = Callable[[list[dict[str, Any]], int | None], Awaitable[None]]


# Custom Exceptions
class KernelError(Exception):
    """Base exception for kernel-related errors."""

    pass


class KernelExecutionError(KernelError):
    """Raised when code execution fails in the kernel."""

    pass


class KernelTimeoutError(KernelError):
    """Raised when kernel operations exceed timeout."""

    pass


@dataclass
class ServerConfig:
    """
    Settings for connecting to a remote Jupyter Server.

    Attributes:
        base_url: Base URL to user's server (e.g., "https://hub.example.com/user/alex").
        token: API token for 'Authorization: Token <token>' (omit if using cookies).
        headers: Extra headers (e.g., {"Cookie":"...", "X-XSRFToken":"..."}).
        kernel_name: Kernel to create when launching a new session.
        notebook_path: If set, bind to a specific notebook via the Sessions API.
    """

    base_url: str
    token: str | None = None
    headers: dict[str, str] | None = None
    kernel_name: str = "python3"
    notebook_path: str | None = None


@dataclass
class SessionConfig:
    """
    High-level configuration for creating a kernel session.

    Attributes:
        mode: "local" or "server".
        kernel_name: Kernel name to spawn (default: "python3"). Used in local mode, and
                     as default when creating a server kernel/session unless overridden.
        connection_file_name: If provided in local mode, attach to an existing kernel.
        server: Required when mode == "server"; settings for remote Jupyter Server.
    """

    mode: str = "local"
    kernel_name: str = "python3"
    connection_file_name: str | None = None
    server: ServerConfig | None = None


@dataclass
class ExecutionResult:
    """
    Normalized result of executing code in a kernel.

    Fields:
        status: "ok" or "error"
        execution_count: Kernel's execution counter if provided
        stdout/stderr: Concatenated stream text
        outputs: List of plain dicts (stream, display_data, execute_result, error) as required by
            nbformat

    Optional extras:
        user_expressions: Any user_expressions results
        elapsed_ms: Rough client-side timing if measured
    """

    status: str = "ok"
    execution_count: int | None = None
    stdout: str = ""
    stderr: str = ""
    # IMPORTANT: plain dicts, not dataclasses (nbformat requires JSONable objects)
    outputs: list[dict[str, Any]] = field(default_factory=list)

    # optional extras
    user_expressions: dict[str, Any] | None = None
    elapsed_ms: float | None = None
