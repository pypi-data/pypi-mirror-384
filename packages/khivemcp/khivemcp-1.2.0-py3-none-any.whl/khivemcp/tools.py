"""Tool wrapper creation and registration for FastMCP."""

import asyncio
import logging
from typing import Any

from fastmcp import FastMCP
from fastmcp.server.context import Context
from pydantic import TypeAdapter

from .function_call_parser import map_positional_args, parse_function_call
from .tool_spec import ToolSpec

logger = logging.getLogger(__name__)


def _parse_list_of_calls(payload: str) -> list[dict]:
    """
    Parse a list of function calls from string format.

    Example: "[func1(x=1), func2(y=2)]" -> [{"tool": "func1", "arguments": {"x": 1}}, ...]
    """
    # Check if it looks like a list
    payload = payload.strip()
    if not (payload.startswith("[") and payload.endswith("]")):
        raise ValueError("Not a list format")

    # Extract the list content (without outer brackets)
    list_content = payload[1:-1].strip()
    if not list_content:
        return []

    # Split by commas at the top level (not inside parentheses/brackets)
    calls = []
    depth = 0
    current_call = []

    for char in list_content:
        if char in "({[":
            depth += 1
        elif char in ")}]":
            depth -= 1

        if char == "," and depth == 0:
            # Top-level comma - split here
            call_str = "".join(current_call).strip()
            if call_str:
                calls.append(call_str)
            current_call = []
        else:
            current_call.append(char)

    # Don't forget the last call
    call_str = "".join(current_call).strip()
    if call_str:
        calls.append(call_str)

    # Parse each call
    parsed_calls = []
    for call_str in calls:
        parsed = parse_function_call(call_str)
        parsed_calls.append(parsed)

    return parsed_calls


def create_tool_wrapper(spec: ToolSpec):
    """Create a wrapper function compatible with FastMCP tool registration.

    Handles Pydantic conversion, RBAC enforcement, and FastMCP Context injection
    based on the tool specification.

    Args:
        spec: ToolSpec containing method and metadata

    Returns:
        Wrapped function ready for FastMCP registration
    """
    bound_method = spec.bound_method
    schema_cls = spec.schema_cls
    accepts_ctx = spec.accepts_ctx

    # Cache TypeAdapter for better performance
    adapter = TypeAdapter(schema_cls) if schema_cls else None

    async def _coerce_request(payload):
        """Convert various request formats to the expected schema.

        Supports:
        - JSON objects: {"key": "value"}
        - JSON strings: '{"key": "value"}'
        - Function call syntax: 'tool("arg1", key="value")'
        """
        if adapter is None:
            return payload

        try:
            # If string, try parsing as function call first (more compact format)
            if isinstance(payload, str):
                # Try function call syntax first
                try:
                    parsed = parse_function_call(payload)
                    arguments = parsed.get("arguments", {})

                    # Map positional args to param names if needed
                    if any(k.startswith("_pos_") for k in arguments.keys()):
                        # Get parameter names from schema
                        if schema_cls and hasattr(schema_cls, "model_fields"):
                            param_names = list(schema_cls.model_fields.keys())
                            arguments = map_positional_args(arguments, param_names)

                    # Validate the parsed arguments
                    return adapter.validate_python(arguments)
                except (ValueError, SyntaxError):
                    # Not function call syntax, try JSON
                    return adapter.validate_json(payload)
            else:
                # Dict payload - validate directly
                return adapter.validate_python(payload)
        except Exception as e:
            logger.error(f"Request validation failed for {spec.full_tool_name}: {e}")
            raise ValueError(f"Invalid request format: {e}")

    async def _check_authz(ctx: Context | None):
        """Check authorization if required for this tool."""
        if not spec.auth_required:
            return  # No auth required

        if ctx is None:
            raise PermissionError(
                f"Authentication required for tool '{spec.full_tool_name}'"
            )

        # Try common Context shapes without hard-coding FastMCP internals
        token = getattr(ctx, "access_token", None) or getattr(ctx, "token", None)
        if token is None:
            raise PermissionError(
                f"Authentication required for tool '{spec.full_tool_name}'"
            )

        # Check if token has required scopes
        token_scopes = set(getattr(token, "scopes", []) or [])
        required_scopes = set(spec.auth_required)

        if not required_scopes.issubset(token_scopes):
            missing = sorted(required_scopes - token_scopes)
            raise PermissionError(
                f"Missing required scopes for tool '{spec.full_tool_name}': {missing}"
            )

    # Strategy: If auth is required, always request Context so we can authorize,
    # even if the underlying method doesn't accept ctx.
    # Otherwise mirror the method's declared context usage.
    if spec.auth_required or accepts_ctx:

        async def tool_with_context(ctx: Context, request: dict | str | Any):
            await _check_authz(ctx)

            # Check if parallelizable and request is a list
            if spec.parallelizable and isinstance(request, str):
                try:
                    # Try to parse as list of function calls
                    batch_requests = _parse_list_of_calls(request)
                    # Execute all in parallel
                    tasks = []
                    for parsed in batch_requests:
                        # Extract just the arguments from parsed dict
                        arguments = parsed.get("arguments", {})

                        # Map positional args to param names if needed
                        if any(k.startswith("_pos_") for k in arguments.keys()):
                            if schema_cls and hasattr(schema_cls, "model_fields"):
                                param_names = list(schema_cls.model_fields.keys())
                                arguments = map_positional_args(arguments, param_names)

                        # Validate with adapter (TypeAdapter handles union types automatically)
                        coerced = (
                            adapter.validate_python(arguments) if adapter else arguments
                        )
                        if accepts_ctx:
                            tasks.append(bound_method(ctx=ctx, request=coerced))
                        else:
                            tasks.append(bound_method(request=coerced))
                    return await asyncio.gather(*tasks)
                except ValueError:
                    # Not a list, continue with single request
                    pass

            # Single request
            coerced_request = await _coerce_request(request)
            if accepts_ctx:
                return await bound_method(ctx=ctx, request=coerced_request)
            else:
                # Underlying method does not accept ctx
                return await bound_method(request=coerced_request)

        tool_with_context.__annotations__ = {
            "ctx": Context,
            "request": str,  # Accept string to enable function call syntax
            "return": Any,
        }
        wrapper = tool_with_context
    else:
        # Standard method without context
        async def tool_without_context(request: dict | str | Any):
            # No auth required here; if required, we used tool_with_context above

            # Check if parallelizable and request is a list
            if spec.parallelizable and isinstance(request, str):
                try:
                    # Try to parse as list of function calls
                    batch_requests = _parse_list_of_calls(request)
                    # Execute all in parallel
                    tasks = []
                    for parsed in batch_requests:
                        # Extract just the arguments from parsed dict
                        arguments = parsed.get("arguments", {})

                        # Map positional args to param names if needed
                        if any(k.startswith("_pos_") for k in arguments.keys()):
                            if schema_cls and hasattr(schema_cls, "model_fields"):
                                param_names = list(schema_cls.model_fields.keys())
                                arguments = map_positional_args(arguments, param_names)

                        # Validate with adapter (TypeAdapter handles union types automatically)
                        coerced = (
                            adapter.validate_python(arguments) if adapter else arguments
                        )
                        tasks.append(bound_method(request=coerced))
                    return await asyncio.gather(*tasks)
                except ValueError:
                    # Not a list, continue with single request
                    pass

            # Single request
            coerced_request = await _coerce_request(request)
            return await bound_method(request=coerced_request)

        tool_without_context.__annotations__ = {
            "request": str,
            "return": Any,
        }  # Accept string to enable function call syntax
        wrapper = tool_without_context

    # Set metadata for FastMCP
    wrapper.__name__ = spec.full_tool_name.replace("-", "_")
    wrapper.__qualname__ = spec.full_tool_name.replace("-", "_")
    wrapper.__doc__ = spec.description

    logger.debug(
        f"Created wrapper for tool '{spec.full_tool_name}' "
        f"(context: {accepts_ctx}, schema: {schema_cls is not None}, "
        f"auth: {spec.auth_required is not None})"
    )

    return wrapper


def register_tools(mcp: FastMCP, tool_specs: list[ToolSpec]) -> int:
    """Register all tool specifications with the FastMCP server.

    Args:
        mcp: FastMCP server instance
        tool_specs: List of tool specifications to register

    Returns:
        Number of tools successfully registered
    """
    logger.info(f"Registering {len(tool_specs)} tools...")
    registered_count = 0

    for spec in tool_specs:
        try:
            wrapper = create_tool_wrapper(spec)
            mcp.tool(wrapper)
            registered_count += 1
            logger.debug(f"Registered tool '{spec.full_tool_name}'")

        except Exception as e:
            logger.error(f"Failed to register tool '{spec.full_tool_name}': {e}")

    logger.info(f"Successfully registered {registered_count}/{len(tool_specs)} tools")
    return registered_count
