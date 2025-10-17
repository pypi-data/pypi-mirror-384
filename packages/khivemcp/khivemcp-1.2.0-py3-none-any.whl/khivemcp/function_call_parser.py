import ast
from typing import Any


def parse_function_call(call_str: str) -> dict[str, Any]:
    """
    Parse Python function call syntax into JSON tool invocation format.

    Examples:
        >>> parse_function_call('search("AI news")')
        {'tool': 'search', 'arguments': {'query': 'AI news'}}

        >>> parse_function_call('search("AI news", limit=10, categories=["company"])')
        {'tool': 'search', 'arguments': {'query': 'AI news', 'limit': 10, 'categories': ['company']}}

    Args:
        call_str: Python function call as string

    Returns:
        Dict with 'tool' and 'arguments' keys

    Raises:
        ValueError: If the string is not a valid function call
    """
    try:
        # Parse the call as a Python expression
        tree = ast.parse(call_str, mode="eval")
        call = tree.body

        if not isinstance(call, ast.Call):
            raise ValueError("Not a function call")

        # Extract function name
        if isinstance(call.func, ast.Name):
            tool_name = call.func.id
        elif isinstance(call.func, ast.Attribute):
            # Handle chained calls like client.search()
            tool_name = call.func.attr
        else:
            raise ValueError(f"Unsupported function type: {type(call.func)}")

        # Extract arguments
        arguments = {}

        # Positional arguments (will be mapped by parameter order in schema)
        for i, arg in enumerate(call.args):
            # For now, use position-based keys; will be mapped to param names later
            arguments[f"_pos_{i}"] = ast.literal_eval(arg)

        # Keyword arguments
        for keyword in call.keywords:
            if keyword.arg is None:
                # **kwargs syntax
                raise ValueError("**kwargs not supported")
            arguments[keyword.arg] = ast.literal_eval(keyword.value)

        return {"tool": tool_name, "arguments": arguments}

    except (SyntaxError, ValueError) as e:
        raise ValueError(f"Invalid function call syntax: {e}")


def map_positional_args(
    arguments: dict[str, Any], param_names: list[str]
) -> dict[str, Any]:
    """
    Map positional arguments (_pos_0, _pos_1, ...) to actual parameter names.

    Args:
        arguments: Dict with _pos_N keys for positional args
        param_names: Ordered list of parameter names from schema

    Returns:
        Dict with positional args mapped to proper names
    """
    mapped = {}
    pos_count = 0

    for key, value in arguments.items():
        if key.startswith("_pos_"):
            if pos_count >= len(param_names):
                raise ValueError(
                    f"Too many positional arguments (expected {len(param_names)})"
                )
            mapped[param_names[pos_count]] = value
            pos_count += 1
        else:
            # Keep keyword arguments as-is
            mapped[key] = value

    return mapped
