"""Decorators for khivemcp Service Groups."""

import inspect
from collections.abc import Callable
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel

from .utils import typescript_schema

# Internal metadata attribute key
_KHIVEMCP_OP_META = "__khivemcp_op_meta__"


def operation(
    name: str | None = None,
    description: str | None = None,
    schema: type[BaseModel] = None,
    auth: list[str] | None = None,
    rate_limit: bool = False,
    accepts_context: bool = None,
    parallelizable: bool = False,
):
    """
    Decorator to mark an async method in an khivemcp group class as an operation.

    This attaches metadata used by the khivemcp server during startup to register
    the method as an MCP tool.

    Args:
        name: The local name of the operation within the group. If None, the
            method's name is used. The final MCP tool name will be
            'group_config_name.local_name'.
        description: A description for the MCP tool. If None, the method's
            docstring is used.
        schema: Pydantic model for request validation.
        auth: List of required permissions (e.g., ["read", "write"]). If provided
            and the group has a FastMCP auth provider, these permissions will be
            enforced. None means no auth required for this operation.
        rate_limit: Whether this operation should be rate limited. Note that
            groups can implement their own rate limiting logic.
        accepts_context: Whether the method accepts a 'ctx' parameter for FastMCP
            Context. If None, automatically detected from method signature.
        parallelizable: If True, the tool can accept a list of requests and execute
            them in parallel. Supports both single requests and batch requests.
    """
    if name is not None and not isinstance(name, str):
        raise TypeError("operation 'name' must be a string or None.")
    if description is not None and not isinstance(description, str):
        raise TypeError("operation 'description' must be a string or None.")
    if auth is not None and not isinstance(auth, list):
        raise TypeError(
            "operation 'auth' must be a list of permission strings or None."
        )
    if not isinstance(rate_limit, bool):
        raise TypeError("operation 'rate_limit' must be a boolean.")

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if not inspect.isfunction(func):
            # This might happen if applied to non-methods, although intended for methods
            raise TypeError("@khivemcp.operation can only decorate functions/methods.")
        if not inspect.iscoroutinefunction(func):
            raise TypeError(
                f"@khivemcp.operation requires an async function (`async def`), but got '{func.__name__}'."
            )

        op_name = name or func.__name__
        op_desc = (
            description
            or inspect.getdoc(func)
            or f"Executes the '{op_name}' operation."
        )
        if schema is not None:
            # Handle union types (e.g., ModelA | ModelB)
            # Check for both typing.Union and types.UnionType (Python 3.10+ A | B syntax)
            origin = get_origin(schema)
            # get_origin returns Union for typing.Union[A, B] but None for A | B
            # For A | B, we need to check the type directly
            is_union = origin is Union or (
                hasattr(schema, "__class__")
                and schema.__class__.__name__ == "UnionType"
            )

            if is_union:
                # Generate docs for each union member
                union_members = get_args(schema)
                if union_members:  # get_args works for both typing.Union and A | B
                    op_desc += "\n\nInput schema (TypeScript-style) - accepts any of:"
                    for i, member in enumerate(union_members, 1):
                        if hasattr(member, "model_json_schema"):
                            member_name = member.__name__
                            ts_schema = typescript_schema(member.model_json_schema())
                            op_desc += f"\n\nOption {i}: {member_name}\n{ts_schema}"
                else:
                    # Fallback if we can't extract members
                    op_desc += (
                        f"\n\nInput schema: Union type (documentation unavailable)"
                    )
            elif hasattr(schema, "model_json_schema"):
                # Single Pydantic model
                ts_schema = typescript_schema(schema.model_json_schema())
                op_desc += f"\n\nInput schema (TypeScript-style):\n{ts_schema}"
            else:
                op_desc += f"\n\nInput schema: {schema}"

            if parallelizable:
                op_desc += f"\n\nUse Python function call syntax: {op_name}(arg1, arg2, key=value)"
                op_desc += f"\n\nSupports batch/parallel execution: [{op_name}(...), {op_name}(...), ...]"
            else:
                op_desc += f"\n\nUse Python function call syntax: {op_name}(arg1, arg2, key=value)"

        # Auto-detect if method accepts context parameter if not explicitly set
        has_context_param = accepts_context
        if has_context_param is None:
            sig = inspect.signature(func)
            has_context_param = "ctx" in sig.parameters

        # Store metadata directly on the function object
        setattr(
            func,
            _KHIVEMCP_OP_META,
            {
                "local_name": op_name,
                "description": op_desc,
                "is_khivemcp_operation": True,  # Explicit marker
                "schema": schema,  # Store the schema class for later use
                "auth_required": auth,  # List of required permissions or None
                "rate_limited": rate_limit,  # Boolean flag for rate limiting
                "accepts_context": has_context_param,  # Whether method accepts ctx parameter
                "parallelizable": parallelizable,  # Whether tool supports batch/parallel execution
            },
        )

        # Metadata-only decorator: return the original function unchanged.
        # All coercion happens in tools.create_tool_wrapper() during registration.
        return func

    return decorator
