"""
Session factory for agent-jupyter-toolkit.

Chooses between local (ZMQ) and server (HTTP+WS) transports and returns a
`Session` object with a small, stable async API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .transport import KernelTransport
from .transports.local import LocalTransport
from .transports.server import ServerTransport
from .types import ExecutionResult, OutputCallback, SessionConfig

if TYPE_CHECKING:
    from .manager import KernelManager


class Session:
    """
    A live kernel session wrapping a KernelTransport.

    Exposes a simple async API:
        - start()
        - execute(code, timeout=None) -> ExecutionResult
        - is_alive()
        - shutdown()

    Also supports use as an async context manager:

        async with create_session(cfg) as sess:
            await sess.execute("print('hi')")

    For advanced/local scenarios, `kernel_manager` is exposed when available.
    """

    def __init__(self, transport: KernelTransport) -> None:
        self._transport = transport

    async def start(self) -> None:
        """
        Start or attach to the underlying kernel and initialize channels.
        """
        await self._transport.start()

    async def shutdown(self) -> None:
        """
        Shut down the underlying kernel and release resources.
        """
        await self._transport.shutdown()

    async def is_alive(self) -> bool:
        """Return True if the underlying kernel is responsive."""
        return await self._transport.is_alive()

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
        Execute `code` in the underlying kernel.

        Args:
            code: Source code to run.
            timeout: Max seconds to wait for completion (None = no timeout).
            output_callback: If provided, this coroutine is called after each
                IOPub message that changes visible state, with
                `(outputs_so_far, execution_count)`. This allows real-time
                streaming of outputs into a collaborative document transport.
                Calls are strictly ordered as messages arrive; outputs is nbformat-like.
                May be invoked multiple times per cell.
            store_history: Whether to record execution in kernel history.
            allow_stdin: Whether the kernel may request stdin from this client.
            stop_on_error: Abort the queue if an error occurs in execution.

        Returns:
            ExecutionResult: Normalized execution metadata and nbformat-like outputs.
        """
        return await self._transport.execute(
            code,
            timeout=timeout,
            output_callback=output_callback,
            store_history=store_history,
            allow_stdin=allow_stdin,
            stop_on_error=stop_on_error,
        )

    @property
    def kernel_manager(self) -> KernelManager | None:
        """
        Expose the KernelManager if this is a local session; otherwise None.

        Useful for advanced callers who need manager-specific operations locally
        (e.g., inspecting the connection file). Server sessions return None.
        """
        return getattr(self._transport, "kernel_manager", None)

    # Async context manager sugar
    async def __aenter__(self) -> Session:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.shutdown()


def create_session(config: SessionConfig | None = None) -> Session:
    """
    Create a Session using either LocalTransport or ServerTransport.

    Returns:
        Session: a wrapper around the chosen KernelTransport.

    Raises:
        ValueError: if config.mode == "server" but no server config provided.
    """
    if config is None:
        config = SessionConfig()
    if config.mode == "server":
        if not config.server:
            raise ValueError("Server mode requires a ServerConfig")
        transport = ServerTransport(config.server)
    else:
        transport = LocalTransport(
            kernel_name=config.kernel_name,
            connection_file_name=config.connection_file_name,
        )
    return Session(transport)
