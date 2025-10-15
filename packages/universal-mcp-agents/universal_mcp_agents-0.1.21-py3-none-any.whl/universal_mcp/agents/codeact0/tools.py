import asyncio
import json
from collections import defaultdict
from typing import Annotated, Any

from langchain_core.tools import tool
from loguru import logger
from pydantic import Field
from universal_mcp.agentr.registry import AgentrRegistry
from universal_mcp.types import ToolFormat


def enter_playbook_mode():
    """Call this function to enter playbook mode. Playbook mode is when the user wants to store a repeated task as a script with some inputs for the future."""
    return


def exit_playbook_mode():
    """Call this function to exit playbook mode. Playbook mode is when the user wants to store a repeated task as a script with some inputs for the future."""
    return


def create_meta_tools(tool_registry: AgentrRegistry) -> dict[str, Any]:
    """Create the meta tools for searching and loading tools"""

    @tool
    async def search_functions(
        queries: Annotated[
            list[str] | str | None,
            Field(description="A single query or a list of queries to search for relevant functions"),
        ] = None,
        app_id: Annotated[
            str | None,
            Field(description="The ID or common name of a specific application to search within"),
        ] = None,
    ) -> str:
        """
        Searches for relevant functions across applications based on queries and/or a specific app.
        This function operates in three modes:

        1.  **Global Search (provide `queries` only):**
            - Use when the user wants to perform an action without specifying an application.
            - The system will search across all available functions.
            - Example: For "how can I create a presentation?", call with queries=["create presentation"].

        2.  **App Discovery (provide `app_id` only):**
            - Use when the user asks about the capabilities of a specific application.
            - The `app_id` can be the common name of the app (e.g., "Gmail", "Google Drive").
            - This will return all available functions for that application, up to a limit.
            - Example: For "what can you do with Gmail?", call with app_id="Gmail".

        3.  **Scoped Search (provide `queries` AND `app_id`):**
            - Use when the user wants to perform an action within a specific application.
            - This performs a targeted search only within the specified app's functions.
            - Example: For "how do I find an email in Gmail?", call with queries=["find email"], app_id="Gmail".
        """
        if isinstance(queries, str):  # Handle JSON string input
            try:
                queries = json.loads(queries)
            except json.JSONDecodeError:
                # If it's a single query as a string, convert to list
                queries = [queries] if queries else None

        if not queries and not app_id:
            raise ValueError("You must provide 'queries', an 'app_id', or both.")

        registry = tool_registry
        connections = await registry.list_connected_apps()
        connected_app_ids = {connection["app_id"] for connection in connections}

        canonical_app_id = None
        found_tools_result = []

        if app_id:
            relevant_apps = await registry.search_apps(query=app_id, distance_threshold=0.7)
            if not relevant_apps:
                return {
                    "found_tools": [],
                    "message": f"Search failed. Application '{app_id}' was not found.",
                }
            canonical_app_id = relevant_apps[0]["id"]

        if canonical_app_id and not queries:
            all_app_tools = await registry.search_tools(query="", app_id=canonical_app_id, limit=20)

            tool_list = []
            for tool in all_app_tools:
                cleaned_description = tool.get("description", "").split("Context:")[0].strip()
                tool_list.append({"id": tool["id"], "description": cleaned_description})

            found_tools_result.append(
                {
                    "app_id": canonical_app_id,
                    "connection_status": "connected" if canonical_app_id in connected_app_ids else "not_connected",
                    "tools": tool_list,
                }
            )

        else:
            query_results = []
            prioritized_app_id_list = []

            if canonical_app_id:
                prioritized_app_id_list = [canonical_app_id]
            else:
                # 1. Perform an initial broad search for tools.
                initial_tool_search_tasks = [registry.search_tools(query=q, distance_threshold=0.7) for q in queries]
                initial_tool_results = await asyncio.gather(*initial_tool_search_tasks)

                # 2. Search for relevant apps.
                app_search_tasks = [registry.search_apps(query=q, distance_threshold=0.7) for q in queries]
                app_search_results = await asyncio.gather(*app_search_tasks)

                # 3. Create a prioritized list of app IDs for the final search.
                # Apps found via search_apps are considered higher priority and come first.
                app_ids_from_apps = {app["id"] for result_list in app_search_results for app in result_list}
                # Use a list to maintain order.
                prioritized_app_id_list.extend(list(app_ids_from_apps))

                # Add app_ids from the initial tool search, ensuring no duplicates.
                app_ids_from_tools = {tool["app_id"] for result_list in initial_tool_results for tool in result_list}

                for tool_app_id in app_ids_from_tools:
                    if tool_app_id not in app_ids_from_apps:
                        prioritized_app_id_list.append(tool_app_id)

            # 4. Perform the final, comprehensive tool search across the prioritized list of apps.
            if prioritized_app_id_list:
                # print(f"Prioritized app IDs for final search: {prioritized_app_id_list}")
                final_tool_search_tasks = []
                for app_id_to_search in prioritized_app_id_list:
                    for query in queries:
                        final_tool_search_tasks.append(
                            registry.search_tools(query=query, app_id=app_id_to_search, distance_threshold=0.7)
                        )
                query_results = await asyncio.gather(*final_tool_search_tasks)

            # 5. Aggregate all found tools for easy lookup.
            aggregated_tools = defaultdict(dict)
            for tool_list in query_results:
                for tool in tool_list:
                    app_id_from_tool = tool.get("app_id", "unknown")
                    tool_id = tool.get("id")
                    if not tool_id or tool_id in aggregated_tools[app_id_from_tool]:
                        continue
                    cleaned_description = tool.get("description", "").split("Context:")[0].strip()
                    aggregated_tools[app_id_from_tool][tool_id] = {
                        "id": tool_id,
                        "description": cleaned_description,
                    }

            # 6. Build the final results list, respecting the prioritized app order.
            for app_id_from_list in prioritized_app_id_list:
                if app_id_from_list in aggregated_tools and aggregated_tools[app_id_from_list]:
                    found_tools_result.append(
                        {
                            "app_id": app_id_from_list,
                            "connection_status": "connected"
                            if app_id_from_list in connected_app_ids
                            else "not_connected",
                            "tools": list(aggregated_tools[app_id_from_list].values()),
                        }
                    )

        # Build result string efficiently
        result_parts = []
        apps_in_results = {app["app_id"] for app in found_tools_result}
        connected_apps_in_results = apps_in_results.intersection(connected_app_ids)

        for app in found_tools_result:
            app_id = app["app_id"]
            connection_status = app["connection_status"]
            tools = app["tools"]

            app_status = "connected" if connection_status == "connected" else "NOT connected"
            result_parts.append(f"Tools from {app_id} (status: {app_status} by user):")

            for tool in tools:
                tool_id = tool["id"]
                description = tool["description"]
                result_parts.append(f" - {tool_id}: {description}")
            result_parts.append("")  # Empty line between apps

        # Add connection status information
        if len(connected_apps_in_results) == 0 and len(apps_in_results) > 0:
            result_parts.append(
                "Connection Status: None of the apps in the results are connected. You must ask the user to choose the application."
            )
        elif len(connected_apps_in_results) > 1:
            connected_list = ", ".join(connected_apps_in_results)
            result_parts.append(
                f"Connection Status: Multiple apps are connected ({connected_list}). You must ask the user to select which application they want to use."
            )

        result_parts.append("Call load_functions to select the required functions only.")
        return "\n".join(result_parts)

    @tool
    async def load_functions(tool_ids: list[str]) -> str:
        """Load specific functions by their IDs for use in subsequent steps.

        Args:
            tool_ids: Function ids in the form 'app__function'. Example: 'google_mail__send_email'

        Returns:
            Confirmation message about loaded functions
        """
        return f"Successfully loaded {len(tool_ids)} functions: {tool_ids}"

    @tool
    async def web_search(query: str) -> dict:
        """Get an LLM answer to a question informed by Perplexity web search results.
        Useful when you need information from a wide range of real-time sources on the web.
        Do not use this when you need to access contents of a specific webpage.

        This tool performs a Perplexity request via `perplexity__answer_with_search`, which:
        1. Provides a **direct answer** for factual queries with citation(s)
        2. Generates a **summary with citations** for open-ended questions

        Args:
            query (str): The question or topic to answer.

        Returns:
            dict: A structured response containing:
                - answer (str): Generated answer with markdown formatting and citation numbers [1][2]
                - citations (list[str]): List of source URLs corresponding to citation numbers
        """
        await tool_registry.export_tools(["exa__answer"], ToolFormat.LANGCHAIN)
        response = await tool_registry.call_tool("exa__answer", {"query": query, "text": True})
        logger.info(f"Web search response: {response}")

        # Extract only desired fields
        return {
            "answer": response.get("content"),
            "citations": response.get("citations", []),
        }

    return {"search_functions": search_functions, "load_functions": load_functions, "web_search": web_search}


async def get_valid_tools(tool_ids: list[str], registry: AgentrRegistry) -> tuple[list[str], list[str]]:
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
            text = registry.authorise_app(app_id=app)
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
