import asyncio
from collections import defaultdict
from typing import Any

from langchain_core.tools import tool
from universal_mcp.tools.registry import ToolRegistry
from universal_mcp.types import ToolFormat


def create_meta_tools(tool_registry: ToolRegistry) -> dict[str, Any]:
    """Create the meta tools for searching and loading tools"""

    @tool
    async def search_tools(queries: list[str]) -> str:
        """Search for relevant tools given list of queries.
        Each single query should be atomic (doable with a single tool).
        For tasks requiring multiple tools, add separate queries for each subtask"""
        try:
            # Fetch all connections
            connections = await tool_registry.list_connected_apps()
            connected_apps = {connection["app_id"] for connection in connections}

            # Use defaultdict to avoid key existence checks
            app_tools = defaultdict(list)

            # Process all queries concurrently
            search_tasks = []
            for query in queries:
                search_tasks.append(_search_query_tools(query))

            query_results = await asyncio.gather(*search_tasks)

            # Aggregate results with limit per app
            for tools_list in query_results:
                for tool in tools_list:
                    app = tool["id"].split("__")[0]
                    cleaned_desc = tool["description"].split("Context:")[0].strip()
                    app_tools[app].append(f"{tool['id']}: {cleaned_desc}")

            # Build result string efficiently
            result_parts = []
            for app, tools in app_tools.items():
                app_status = "connected" if app in connected_apps else "NOT connected"
                result_parts.append(f"Tools from {app} (status: {app_status} by user):")
                for tool in tools:
                    result_parts.append(f" - {tool}")
                result_parts.append("")  # Empty line between apps

            result_parts.append("Call load_tools to select the required tools only.")
            return "\n".join(result_parts)

        except Exception as e:
            return f"Error: {e}"

    async def _search_query_tools(query: str) -> list[dict]:
        """Helper function to search apps and tools for a single query."""
        # Start both searches concurrently
        tools_search_task = tool_registry.search_tools(query, limit=10)
        apps_search_task = tool_registry.search_apps(query, limit=4)

        # Wait for both to complete
        tools_from_general_search, apps_list = await asyncio.gather(tools_search_task, apps_search_task)

        # Create tasks for searching tools from each app
        app_tool_tasks = [tool_registry.search_tools(query, limit=5, app_id=app["id"]) for app in apps_list]

        # Wait for all app-specific tool searches to complete
        app_tools_results = await asyncio.gather(*app_tool_tasks)

        # Combine all results
        tools_list = list(tools_from_general_search)
        for app_tools in app_tools_results:
            tools_list.extend(app_tools)

        return tools_list

    @tool
    async def load_tools(tool_ids: list[str]) -> str:
        """Load specific tools by their IDs for use in subsequent steps.

        Args:
            tool_ids: Tool ids in the form 'app__tool'. Example: 'google_mail__send_email'

        Returns:
            Confirmation message about loaded tools
        """
        return f"Successfully loaded {len(tool_ids)} tools: {tool_ids}"

    @tool
    async def web_search(query: str) -> str:
        """Search the web for the given query. Returns the search results. Do not use for app-specific searches (for example, reddit or linkedin searches should be done using the app's tools)"""
        await tool_registry.export_tools(["exa__search_with_filters"], ToolFormat.LANGCHAIN)
        response = await tool_registry.call_tool(
            "exa__search_with_filters", {"query": query, "contents": {"summary": True}}
        )
        return response

    return {"search_tools": search_tools, "load_tools": load_tools, "web_search": web_search}


async def get_valid_tools(tool_ids: list[str], registry: ToolRegistry) -> tuple[list[str], list[str]]:
    """For a given list of tool_ids, validates the tools and returns a list of links for the apps that have not been logged in"""
    correct, incorrect = [], []
    connections = await registry.list_connected_apps()
    connected_apps = {connection["app_id"] for connection in connections}
    unconnected = set()
    unconnected_links = []
    app_tool_list: dict[str, set[str]] = {}

    # Group tool_ids by app for fewer registry calls
    app_to_tools: dict[str, list[tuple[str, str]]] = {}
    for tool_id in tool_ids:
        if "__" not in tool_id:
            incorrect.append(tool_id)
            continue
        app, tool_name = tool_id.split("__", 1)
        app_to_tools.setdefault(app, []).append((tool_id, tool_name))

    # Fetch all apps concurrently
    async def fetch_tools(app: str):
        try:
            tools_dict = await registry.list_tools(app)
            return app, {tool_unit["name"] for tool_unit in tools_dict}
        except Exception:
            return app, None

    results = await asyncio.gather(*(fetch_tools(app) for app in app_to_tools))

    # Build map of available tools per app
    for app, tools in results:
        if tools is not None:
            app_tool_list[app] = tools

    # Validate tool_ids
    for app, tool_entries in app_to_tools.items():
        available = app_tool_list.get(app)
        if available is None:
            incorrect.extend(tool_id for tool_id, _ in tool_entries)
            continue
        if app not in connected_apps and app not in unconnected:
            unconnected.add(app)
            text = registry.client.get_authorization_url(app)
            start = text.find(":") + 1
            end = text.find(". R", start)
            url = text[start:end].strip()
            markdown_link = f"[{app}]({url})"
            unconnected_links.append(markdown_link)
        for tool_id, tool_name in tool_entries:
            if tool_name in available:
                correct.append(tool_id)
            else:
                incorrect.append(tool_id)

    return correct, unconnected_links
