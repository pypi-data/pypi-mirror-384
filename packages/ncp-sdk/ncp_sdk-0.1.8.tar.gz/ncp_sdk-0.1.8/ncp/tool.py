"""Tool decorator for creating agent tools (SDK version).

Tools are Python functions decorated with @tool that agents can call.
The decorator converts functions into Tool instances compatible with the NCP platform.
"""

import asyncio
import inspect
from functools import wraps
from typing import Any, Callable, Dict, Optional

# Import from a local _tool_base to avoid importing the full platform
# We'll create a minimal Tool class here that matches the platform's interface


class Tool:
    """SDK version of Tool that wraps a function for platform deployment.

    This is a lightweight version that doesn't include execution logic.
    The platform will reconstruct full Tool instances on deployment.

    Attributes:
        name: Tool name
        description: Tool description
        func: The wrapped function
    """

    def __init__(self, name: str, description: str, func: Callable):
        """Initialize a tool.

        Args:
            name: Tool name
            description: Tool description
            func: Python function to wrap
        """
        if not name or not name.strip():
            raise ValueError("Tool name cannot be empty")
        if not description or not description.strip():
            raise ValueError("Tool description cannot be empty")
        if not callable(func):
            raise ValueError("Tool func must be callable")

        self.name = name
        self.description = description
        self.func = func

        self._is_async = asyncio.iscoroutinefunction(func)
        self._signature = inspect.signature(func)
        self._schema = self._generate_schema()

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool.

        Returns:
            OpenAI function calling schema
        """
        return self._schema

    def _generate_schema(self) -> Dict[str, Any]:
        """Generate JSON schema from function signature.

        Returns:
            OpenAI function calling schema
        """
        params = {}

        for param_name, param in self._signature.parameters.items():
            param_schema: Dict[str, Any] = {"type": "string"}  # Default

            # Infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                if param.annotation is int:
                    param_schema["type"] = "integer"
                elif param.annotation is float:
                    param_schema["type"] = "number"
                elif param.annotation is bool:
                    param_schema["type"] = "boolean"
                elif param.annotation is str:
                    param_schema["type"] = "string"
                elif param.annotation is list:
                    param_schema["type"] = "array"
                elif param.annotation is dict:
                    param_schema["type"] = "object"

            # Add default if present
            if param.default != inspect.Parameter.empty:
                param_schema["default"] = param.default

            params[param_name] = param_schema

        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": params,
                "required": [
                    param_name
                    for param_name, param in self._signature.parameters.items()
                    if param.default == inspect.Parameter.empty
                ],
            },
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"Tool(name={self.name}, description={self.description})"


def tool(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Any:
    """Decorator to mark a function as an agent tool.

    The decorator converts a Python function into a Tool instance that can be
    used by agents on the NCP platform. The function's signature and docstring
    are used to generate the tool schema.

    Args:
        func: The function to decorate (used when @tool is called without parentheses)
        name: Optional custom name for the tool (defaults to function name)
        description: Optional custom description (defaults to function docstring)

    Returns:
        Tool instance wrapping the function

    Examples:
        Basic usage with type hints:

        >>> @tool
        ... def get_weather(location: str, units: str = "celsius") -> dict:
        ...     '''Get weather information for a location.'''
        ...     return {"temperature": 22, "condition": "sunny"}

        With custom name and description:

        >>> @tool(name="weather_api", description="Fetch current weather data")
        ... def get_weather(location: str) -> dict:
        ...     return {"temperature": 22}

        Async tools:

        >>> @tool
        ... async def fetch_data(url: str) -> dict:
        ...     '''Fetch data from a URL asynchronously.'''
        ...     async with aiohttp.ClientSession() as session:
        ...         async with session.get(url) as resp:
        ...             return await resp.json()
    """

    def decorator(f: Callable) -> Tool:
        tool_name = name or f.__name__
        tool_description = description or (f.__doc__ or "").strip()

        if not tool_description:
            raise ValueError(
                f"Tool '{tool_name}' must have a description. "
                f"Either provide a docstring or use @tool(description='...')"
            )

        # Create Tool instance
        return Tool(
            name=tool_name,
            description=tool_description,
            func=f,
        )

    # Handle both @tool and @tool() syntax
    if func is None:
        return decorator
    else:
        return decorator(func)
