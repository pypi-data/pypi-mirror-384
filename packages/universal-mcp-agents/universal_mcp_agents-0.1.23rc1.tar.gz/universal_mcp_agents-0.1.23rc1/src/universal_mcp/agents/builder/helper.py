import collections
from collections import defaultdict

from loguru import logger
from universal_mcp.types import ToolConfig


def _extract_tools_from_history(history: list[dict]) -> ToolConfig:
    """
    Parses a conversation history to find and extract all tool names,
    returning them in a structured ToolConfig format.

    This function identifies messages with a "type" of "tool", extracts the
    tool's name from the "name" key, and filters out a predefined list of
    excluded tools. The remaining tool names are expected to be in an
    "app_id__tool_id" format. These are then organized into a dictionary
    mapping each app_id to a sorted list of its associated tool_ids.
    """
    apps_with_tools = collections.defaultdict(set)
    excluded_tools = {"search_tools", "load_tools"}

    for message in history:
        if message.get("type") == "tool":
            full_tool_name = message.get("name")
            if not full_tool_name or full_tool_name in excluded_tools:
                continue

            if "__" in full_tool_name:
                app_id, tool_id = full_tool_name.split("__", 1)
                apps_with_tools[app_id].add(tool_id)

    return {app_id: sorted(list(tools)) for app_id, tools in apps_with_tools.items()}


def _clean_conversation_history(history: list[dict]) -> list[dict]:
    """
    Filters a raw conversation history, keeping only messages relevant for
    agent synthesis (human, ai, and tool messages with a name containing double underscores).
    """
    cleaned_history = []
    for message in history:
        msg_type = message.get("type")

        if msg_type in ["human", "ai"]:
            cleaned_history.append(message)
        elif msg_type == "tool" and isinstance(message.get("name"), str) and "__" in message["name"]:
            cleaned_history.append(message)

    return cleaned_history


def _merge_tool_configs(old_config: ToolConfig, new_config: ToolConfig) -> ToolConfig:
    """Merges two tool configurations, taking the union of tools for each app."""
    if not old_config:
        return new_config
    if not new_config:
        return old_config

    # Start with a copy of the old configuration
    merged_config = defaultdict(set)
    for app, tools in old_config.items():
        merged_config[app].update(tools)

    # Add the new tools, ensuring uniqueness
    for app, tools in new_config.items():
        merged_config[app].update(tools)

    # Convert the sets back to sorted lists for consistent output
    final_config = {app: sorted(list(tool_set)) for app, tool_set in merged_config.items()}
    logger.info(f"Merged tool configuration: {final_config}")
    return final_config
