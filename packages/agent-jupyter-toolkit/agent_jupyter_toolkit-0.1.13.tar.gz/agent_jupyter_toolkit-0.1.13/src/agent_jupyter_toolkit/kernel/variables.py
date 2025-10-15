"""
Variable management utilities for kernel subsystem.

This module provides utilities for managing variables in Jupyter kernels,
including setting, getting, and listing variables across different programming
languages. It uses the session interface for code execution.

Example:
    ```python
    from agent_jupyter_toolkit.kernel.session import create_session
    from agent_jupyter_toolkit.kernel.variables import VariableManager

    session = await create_session()
    var_manager = VariableManager(session)

    # Set a variable
    await var_manager.set("my_var", [1, 2, 3])

    # Get a variable
    value = await var_manager.get("my_var")

    # List all variables
    vars_list = await var_manager.list()
    ```
"""

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .session import Session


class VariableManager:
    """
    Language-agnostic variable manager for kernel variable operations.

    This class provides a high-level interface for setting, getting, and listing
    variables in a kernel session. It handles serialization and uses appropriate
    code templates for different programming languages.

    Attributes:
        session: The kernel session used for code execution
        language: Programming language of the target kernel
    """

    def __init__(self, session: "Session", language: str = "python"):
        """
        Initialize the variable manager.

        Args:
            session: Active kernel session for code execution
            language: Programming language (currently only "python" supported)
        """
        self.session = session
        self.language = language

    async def set(self, name: str, value: Any, mimetype: str = None) -> None:
        """
        Set a variable in the kernel as its native Python object.

        This method serializes the value appropriately and executes code
        to assign it to the specified variable name in the kernel namespace.

        Args:
            name: Variable name to assign
            value: Python object to assign
            mimetype: Unused parameter (kept for compatibility)

        Raises:
            Exception: If the variable assignment fails
        """
        # For JSON-serializable types, use JSON; for others, use repr and exec
        try:
            # Try to serialize as JSON and assign
            json_str = json.dumps(value)
            code = f"import json; {name} = json.loads('''{json_str}''')"
        except (TypeError, ValueError):
            # Fallback: assign using repr (works for most Python objects)
            code = f"{name} = {repr(value)}"

        await self.session.execute(code)

    async def get(self, name: str) -> Any:
        """
        Get a variable from the kernel as its native Python object.

        Args:
            name: Variable name to retrieve

        Returns:
            The variable value, or None if the variable doesn't exist

        Raises:
            Exception: If the variable retrieval fails
        """
        code = f"import json; print(json.dumps(globals().get('{name}', None), default=str))"
        result = await self.session.execute(code)
        out = result.stdout.strip() if result.stdout else ""

        # Try to parse as JSON, else return as string
        try:
            return json.loads(out)
        except (json.JSONDecodeError, ValueError):
            return out

    async def list(self) -> list[str]:
        """
        List all variable names in the kernel namespace.

        Returns:
            List of variable names available in the kernel

        Raises:
            Exception: If the variable listing fails
        """
        if self.language == "python":
            code = """
import json
# Get user-defined variables (exclude built-ins and modules)
user_vars = [name for name, obj in globals().items()
             if not name.startswith('_')
             and not callable(obj)
             and not hasattr(obj, '__module__')]
print(json.dumps(user_vars))
"""
        else:
            raise ValueError(f"Language '{self.language}' not supported")

        result = await self.session.execute(code)
        out = result.stdout.strip() if result.stdout else "[]"

        try:
            return json.loads(out)
        except (json.JSONDecodeError, ValueError):
            return []
