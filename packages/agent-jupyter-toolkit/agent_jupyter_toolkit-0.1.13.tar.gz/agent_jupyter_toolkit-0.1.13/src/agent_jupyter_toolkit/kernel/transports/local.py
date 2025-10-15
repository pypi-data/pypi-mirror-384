"""
Local kernel transport for agent-jupyter-toolkit.

This module provides LocalTransport, which connects to local Jupyter kernels
via ZMQ (Zero Message Queue) for high-performance, low-latency communication.
The transport handles kernel lifecycle management, code execution, and real-time
output streaming for AI agent workflows.

Key features:
- Direct ZMQ communication with local kernels
- Support for existing connection files (kernel reuse)
- Real-time output streaming via callbacks
- Robust error handling and cleanup
- Full compatibility with Jupyter kernel protocol
"""

from __future__ import annotations

import os
from typing import Any

from jupyter_core.paths import jupyter_runtime_dir

from ..manager import KernelManager
from ..transport import KernelTransport
from ..types import ExecutionResult


class LocalTransport(KernelTransport):
    """
    Local kernel transport using ZMQ for direct communication.

    This transport manages local Jupyter kernel processes and provides
    high-performance execution capabilities for AI agents. It supports
    both fresh kernel creation and attachment to existing kernels via
    connection files.

    Architecture:
        LocalTransport -> KernelManager -> AsyncKernelManager (jupyter_client)
                       -> Direct ZMQ communication with execute_interactive

    Lifecycle:
        1. start(): Launch or attach to kernel, initialize ZMQ channels
        2. execute(): Send code, stream outputs, return results
        3. shutdown(): Clean kernel termination and resource cleanup
    """

    def __init__(
        self, *, kernel_name: str = "python3", connection_file_name: str | None = None
    ) -> None:
        """
        Initialize local transport with kernel configuration.

        Args:
            kernel_name: Jupyter kernel specification name (e.g., "python3", "ir", "julia-1.8").
                        Must be installed and available via `jupyter kernelspec list`.
            connection_file_name: Optional path to existing kernel connection file.
                                If provided, attempts to attach to running kernel instead
                                of launching new one. Useful for kernel reuse patterns.

        Note:
            Connection files are typically in jupyter_runtime_dir() and follow
            format: kernel-{uuid}.json containing ZMQ port and key information.
        """
        # Initialize kernel manager with configuration
        self._km = KernelManager(kernel_name=kernel_name, connection_file_name=connection_file_name)

    @property
    def kernel_manager(self) -> KernelManager:
        """
        Access to underlying kernel manager for advanced operations.

        Returns:
            KernelManager: The internal kernel manager instance.

        Use cases:
            - Accessing connection file paths
            - Advanced kernel introspection
            - Custom kernel management operations
            - Debugging kernel state

        Example:
            >>> transport = LocalTransport()
            >>> await transport.start()
            >>> km = transport.kernel_manager
            >>> print(f"Kernel ID: {km.kernel_id}")
        """
        return self._km

    async def start(self) -> None:
        """
        Start or attach to a local Jupyter kernel for code execution.

        This method implements smart connection logic:
        1. If connection_file_name was provided in __init__, try to attach first
        2. If connection file exists and is valid, reuse that kernel
        3. Otherwise, launch a fresh kernel process
        4. Ready for direct code execution via execute() method

        Connection file logic:
            - Relative paths are resolved against jupyter_runtime_dir()
            - Connection files contain ZMQ ports, keys, and transport info
            - Attachment allows kernel reuse across agent sessions

        Raises:
            RuntimeError: If kernel fails to start or become ready
            FileNotFoundError: If specified connection file is invalid

        Note:
            This method is idempotent - calling multiple times is safe
            (though not recommended due to potential resource leaks).
        """
        # Smart connection logic: try existing connection file first
        cf_name = getattr(self._km, "_connection_file_name", None)
        if cf_name:
            # Handle relative vs absolute paths
            cf_path = cf_name
            if not os.path.isabs(cf_path):
                # Resolve relative paths against Jupyter runtime directory
                cf_path = os.path.join(jupyter_runtime_dir(), cf_path)

            # Prefer existing kernel if connection file exists
            if os.path.exists(cf_path):
                await self._km.connect_to_existing(cf_path)
            else:
                # Connection file not found, start fresh kernel
                await self._km.start()
        else:
            # No connection file specified, always start fresh
            await self._km.start()

        # Kernel is ready for direct execution

    async def shutdown(self) -> None:
        """
        Shut down the local kernel and release all resources.

        This method performs clean shutdown:
        1. Terminates kernel process gracefully
        2. Closes ZMQ connections
        3. Releases system resources

        The shutdown is fault-tolerant - it will attempt cleanup
        even if the kernel is already dead or unresponsive.

        Note:
            After shutdown, this transport cannot be reused.
            Create a new LocalTransport instance for further operations.
        """
        # Attempt graceful kernel shutdown
        await self._km.shutdown()

    async def is_alive(self) -> bool:
        """
        Check if the local kernel process is alive and responsive.

        Returns:
            bool: True if kernel is running and can accept requests,
                  False if kernel is dead, crashed, or unresponsive.

        Note:
            This method checks actual kernel process status, not just
            transport connectivity. A False result indicates the kernel
            needs to be restarted via start().
        """
        return await self._km.is_alive()

    async def execute(
        self,
        code: str,
        *,
        timeout: float | None = None,
        output_callback=None,
        store_history: bool = True,
        allow_stdin: bool = False,
        stop_on_error: bool = True,
    ) -> ExecutionResult:
        """
        Execute code in the local kernel with real-time output streaming.

        This method provides comprehensive code execution with:
        - Real-time output callbacks for responsive UIs
        - Configurable timeout handling
        - History and stdin control
        - Error handling options

        Args:
            code: Python code to execute. Can be multi-line.
            timeout: Maximum execution time in seconds. None = no client timeout
                    (kernel may still have its own timeout).
            output_callback: Optional async callback for real-time outputs.
                           Signature: callback(outputs: List[Dict], execution_count: Optional[int])
                           Called whenever new output arrives from kernel.
            store_history: If True, code is stored in kernel's input history.
                          Disable for utility code that shouldn't pollute history.
            allow_stdin: If True, kernel can request user input via stdin.
                        Should be False for headless/agent usage.
            stop_on_error: If True, kernel stops processing on first error.
                          If False, continues execution despite errors.

        Returns:
            ExecutionResult: Complete execution information including:
                - status: "ok", "error", or "abort"
                - execution_count: Kernel's execution counter
                - outputs: List of display outputs (text, images, etc.)
                - error_message: Description if execution failed

        Raises:
            RuntimeError: If transport hasn't been started via start()
            asyncio.TimeoutError: If execution exceeds timeout

        Example:
            >>> result = await transport.execute("print('Hello')")
            >>> print(result.status)  # "ok"
            >>> print(result.outputs)  # [{'name': 'stdout', 'text': 'Hello\\n'}]
        """
        # Validate transport state
        if not self._km or not self._km.client:
            raise RuntimeError("LocalTransport not started. Call start() first.")

        kc = self._km.client

        # Initialize result
        from ..hooks import kernel_hooks
        from ..types import ExecutionResult

        res = ExecutionResult(status="ok")

        # Trigger pre-execution hooks for instrumentation/logging
        kernel_hooks.trigger_before_execute_hooks(code)

        # Accumulators for output_callback
        outputs: list = []
        exec_count: int | None = None

        # Custom output hook to capture outputs for our result object
        def output_hook(msg: dict[Any, Any]) -> None:
            """Capture IOPub messages and fold them into our ExecutionResult."""
            kernel_hooks.trigger_output_hooks(msg)

            header = msg.get("header") or {}
            msg_type = header.get("msg_type")
            content = msg.get("content") or {}

            if msg_type == "execute_input":
                # Extract execution count from execute_input message
                nonlocal exec_count
                ec = content.get("execution_count")
                if ec is not None:
                    res.execution_count = ec
                    exec_count = ec

            elif msg_type == "stream":
                # Handle stdout/stderr stream output
                name = content.get("name")
                text = content.get("text", "") or ""
                output_dict = {"output_type": "stream", "name": name, "text": text}
                res.outputs.append(output_dict)
                outputs.append(output_dict)
                if name == "stdout":
                    res.stdout += text
                elif name == "stderr":
                    res.stderr += text
                # Call Session-style callback
                if output_callback:
                    import asyncio

                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(output_callback(outputs[:], exec_count))
                    except RuntimeError:
                        pass

            elif msg_type in ("display_data", "update_display_data", "execute_result"):
                # Handle rich display outputs (plots, HTML, etc.) and execution results
                data = content.get("data") or {}
                md = content.get("metadata") or {}
                if "execution_count" in content and content["execution_count"] is not None:
                    res.execution_count = content["execution_count"]
                    exec_count = res.execution_count
                out = {
                    "output_type": (
                        "display_data" if msg_type != "execute_result" else "execute_result"
                    ),
                    "data": data,
                    "metadata": md,
                }
                if out["output_type"] == "execute_result":
                    out["execution_count"] = res.execution_count
                res.outputs.append(out)
                outputs.append(out)
                # Call Session-style callback
                if output_callback:
                    import asyncio

                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(output_callback(outputs[:], exec_count))
                    except RuntimeError:
                        pass

            elif msg_type == "clear_output":
                # Handle output clearing (common in interactive widgets)
                res.outputs.clear()
                res.stdout = ""
                res.stderr = ""
                outputs.clear()
                # Call Session-style callback
                if output_callback:
                    import asyncio

                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(output_callback(outputs[:], exec_count))
                    except RuntimeError:
                        pass

            elif msg_type == "error":
                # Handle execution errors with traceback
                res.status = "error"
                err = {
                    "output_type": "error",
                    "ename": content.get("ename"),
                    "evalue": content.get("evalue"),
                    "traceback": content.get("traceback"),
                }
                res.outputs.append(err)
                outputs.append(err)
                # Call Session-style callback
                if output_callback:
                    import asyncio

                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(output_callback(outputs[:], exec_count))
                    except RuntimeError:
                        pass

        try:
            # Use execute_interactive for proper async handling
            reply = await kc.execute_interactive(
                code,
                silent=False,
                store_history=store_history,
                allow_stdin=allow_stdin,
                stop_on_error=stop_on_error,
                timeout=timeout,
                output_hook=output_hook,
            )

            # Update final status from reply (unless already set to error by IOPub)
            if res.status != "error":
                res.status = reply.get("content", {}).get("status", "ok")

            # Extract final execution count from reply
            if "execution_count" in reply.get("content", {}):
                res.execution_count = reply["content"]["execution_count"]
                exec_count = res.execution_count

            # Trigger post-execution hooks for instrumentation/cleanup
            kernel_hooks.trigger_after_execute_hooks(res)

        except TimeoutError as te:
            # Handle execution timeout gracefully
            res.status = "error"
            res.stderr += f"\nExecution timed out after {timeout}s."
            kernel_hooks.trigger_on_error_hooks(te)

        except Exception as e:
            # Handle any other execution errors
            res.status = "error"
            res.stderr += f"\n{type(e).__name__}: {e}"
            kernel_hooks.trigger_on_error_hooks(e)

        return res
