"""khivemcp: Configuration-driven MCP server framework using FastMCP."""

from .decorators import operation
from .function_call_parser import parse_function_call
from .types import GroupConfig, ServiceConfig, ServiceGroup
from .utils import typescript_schema

__version__ = "1.2.0"

__all__ = [
    "operation",
    "ServiceConfig",
    "GroupConfig",
    "ServiceGroup",
    "parse_function_call",
    "typescript_schema",
    "__version__",
]
