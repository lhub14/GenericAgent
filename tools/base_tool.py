"""Base tool interface and registry for GenericAgent tools.

All tools used by the agent should inherit from BaseTool and register
themselves so they can be discovered and loaded dynamically.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, ClassVar

logger = logging.getLogger(__name__)

# Global tool registry: maps tool name -> tool class
_TOOL_REGISTRY: dict[str, type[BaseTool]] = {}


def register_tool(cls: type[BaseTool]) -> type[BaseTool]:
    """Class decorator that registers a tool in the global registry."""
    name = cls.name
    if not name:
        raise ValueError(f"Tool class {cls.__name__} must define a non-empty 'name'.")
    if name in _TOOL_REGISTRY:
        logger.warning("Tool '%s' is already registered; overwriting.", name)
    _TOOL_REGISTRY[name] = cls
    logger.debug("Registered tool: %s", name)
    return cls


def get_registered_tools() -> dict[str, type[BaseTool]]:
    """Return a shallow copy of the current tool registry."""
    return dict(_TOOL_REGISTRY)


def build_tool_schemas() -> list[dict[str, Any]]:
    """Build OpenAI-compatible function-call schemas for all registered tools."""
    schemas = []
    for tool_cls in _TOOL_REGISTRY.values():
        schemas.append(tool_cls.schema())
    return schemas


class BaseTool(ABC):
    """Abstract base class for all agent tools.

    Subclasses must define:
      - ``name``        : unique snake_case identifier used in function calls.
      - ``description`` : human-readable description sent to the model.
      - ``parameters``  : JSON-Schema ``object`` describing the tool's arguments.
      - ``run()``       : the actual implementation.
    """

    # --- Class-level attributes to be defined by subclasses ---
    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    # JSON-Schema 'object' dict (properties, required, etc.)
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    # ----------------------------------------------------------

    @classmethod
    def schema(cls) -> dict[str, Any]:
        """Return the OpenAI function-call schema for this tool."""
        return {
            "type": "function",
            "function": {
                "name": cls.name,
                "description": cls.description,
                "parameters": cls.parameters,
            },
        }

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """Execute the tool with the provided keyword arguments.

        Args:
            **kwargs: Arguments matching the tool's ``parameters`` schema.

        Returns:
            A JSON-serialisable result that will be sent back to the model.

        Raises:
            ToolExecutionError: If the tool fails in an expected way.
        """

    def __call__(self, arguments: str | dict[str, Any]) -> str:
        """Parse *arguments* (JSON string or dict) and call ``run()``.

        Returns a JSON string suitable for a tool-result message.
        """
        if isinstance(arguments, str):
            try:
                kwargs = json.loads(arguments)
            except json.JSONDecodeError as exc:
                logger.error("Failed to parse tool arguments for '%s': %s", self.name, exc)
                return json.dumps({"error": f"Invalid JSON arguments: {exc}"})
        else:
            kwargs = arguments

        try:
            result = self.run(**kwargs)
            if isinstance(result, str):
                return result
            return json.dumps(result, ensure_ascii=False)
        except TypeError as exc:
            logger.error("Tool '%s' called with wrong arguments: %s", self.name, exc)
            return json.dumps({"error": str(exc)})


class ToolExecutionError(Exception):
    """Raised when a tool encounters a recoverable execution error."""
