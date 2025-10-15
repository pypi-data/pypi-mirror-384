"""
KernelTransport protocol for pluggable execution backends.

Local (ZMQ) and Server (HTTP+WS) transports both implement this interface.
"""

from __future__ import annotations

from .types import ExecutionResult, OutputCallback


class KernelTransport:
    """
    Minimal async interface for executing code in a Jupyter kernel.

    Implementations:
    - MUST call `output_callback(outputs_so_far, exec_count)` after each IOPub
        message that changes visible state (execute_input, stream, display_data,
        execute_result, clear_output, error), in order, if a callback is provided.
    - SHOULD also call it once at the end to deliver the final snapshot.
    """

    async def start(self) -> None:
        """Start or attach to a kernel and initialize channels."""
        ...

    async def shutdown(self) -> None:
        """Stop the kernel and teardown channels."""
        ...

    async def is_alive(self) -> bool:
        """Return True if the kernel is alive."""
        ...

    async def execute(
        self,
        code: str,
        *,
        timeout: float | None = None,
        output_callback: OutputCallback | None = None,
        store_history: bool = True,
        allow_stdin: bool = False,
        stop_on_error: bool = True,
    ) -> ExecutionResult:
        """
        Execute code and (optionally) stream outputs via `output_callback`.

        Semantics:
        - If provided, `output_callback` is awaited *in order* after each IOPub message
            that changes the cell's visible state, passing the cumulative outputs and
            the latest execution_count (or None if not yet known).
        - `timeout` applies to the overall cell execution

        Call-order and shape guarantees:
        - Order: Calls to `output_callback` are strictly ordered as messages arrive.
        - Shape: `outputs` is nbformat-like (dicts with `output_type`, `data`, `metadata`, etc.).
            It represents the *current* state (e.g., after a `clear_output`, the list may become
            empty).
        - Count: `execution_count` may be `None` until the kernel emits `execute_input`.
        - Final snapshot: The callback is typically invoked again with the final set once
          the request is complete.
        """
        ...
