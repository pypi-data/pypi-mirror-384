from typing import Any

from universal_mcp.agents.codeact0.utils import light_copy

MAX_RETRIES = 3


def get_context_str(source: Any | list[Any] | dict[str, Any]) -> str:
    """Converts context to a string representation."""
    if not isinstance(source, dict):
        if isinstance(source, list):
            source = {f"doc_{i + 1}": str(doc) for i, doc in enumerate(source)}
        else:
            source = {"content": str(source)}

    return "\n".join(f"<{k}>\n{str(v)}\n</{k}>" for k, v in source.items())


def smart_print(data: Any) -> None:
    """Prints a dictionary or list of dictionaries with string values truncated to 30 characters.

    Args:
        data: Either a dictionary with string keys, or a list of such dictionaries
    """
    print(light_copy(data))  # noqa: T201
