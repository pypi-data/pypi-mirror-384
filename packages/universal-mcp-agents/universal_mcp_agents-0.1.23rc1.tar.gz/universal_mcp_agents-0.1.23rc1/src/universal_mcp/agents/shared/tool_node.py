import asyncio
from collections import defaultdict
from typing import Annotated, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command
from loguru import logger
from pydantic import BaseModel, Field
from universal_mcp.tools.registry import ToolRegistry
from universal_mcp.types import ToolConfig

from universal_mcp.agents.shared.prompts import (
    APP_SELECTION_PROMPT,
    TOOL_SEARCH_QUERIES_PROMPT,
    TOOL_SELECTION_PROMPT,
)

MAX_RETRIES = 1


class SearchQueries(BaseModel):
    queries: list[str] = Field(description="A list of search queries for finding tools.")


class AppSelection(BaseModel):
    app_ids: list[str] = Field(description="The IDs of the selected applications.")


class ToolSelection(BaseModel):
    tool_ids: list[str] = Field(description="The IDs of the selected tools.")


class AgentState(TypedDict):
    """The central state of our agent graph."""

    original_task: str
    queries: list[str]
    candidate_tools: list[dict]
    execution_plan: ToolConfig
    messages: Annotated[list[AnyMessage], add_messages]
    retry_count: int


def build_tool_node_graph(llm: BaseChatModel, registry: ToolRegistry) -> StateGraph:
    """Builds a workflow for tool selection with a retry mechanism."""

    async def _search_for_tools(state: AgentState) -> Command:
        """
        Performs a hierarchical search:
        1. Generates search queries for the task.
        2. Searches for candidate *applications*.
        3. Uses an LLM to select the most relevant applications.
        4. Searches for tools only within the selected applications.
        If any step fails, it can trigger a retry.
        """
        task = state["original_task"]
        logger.info(f"Starting hierarchical tool search for task: '{task}'")

        prompt = TOOL_SEARCH_QUERIES_PROMPT.format(task=task)
        response = await llm.with_structured_output(SearchQueries).ainvoke(prompt)
        queries = response.queries
        logger.info(f"Generated search queries: {queries}")

        if not queries:
            logger.error("LLM failed to generate any search queries.")
            return Command(
                update={"messages": [AIMessage(content="I could not understand the task to search for tools.")]},
                goto="handle_failure",
            )

        # Always store queries for potential retry
        update_state = {"queries": queries}

        app_search_tasks = [registry.search_apps(query, distance_threshold=0.7) for query in queries]
        app_results = await asyncio.gather(*app_search_tasks)
        unique_apps = {app["id"]: app for app_list in app_results for app in app_list}

        if not unique_apps:
            logger.warning(f"No applications found for queries: {queries}. Triggering retry.")
            return Command(update=update_state, goto="general_search_and_select")

        logger.info(f"Found {len(unique_apps)} candidate applications.")

        app_candidates_str = "\n - ".join([f"{app['id']}: {app['description']}" for app in unique_apps.values()])
        app_selection_prompt = APP_SELECTION_PROMPT.format(task=task, app_candidates=app_candidates_str)
        app_selection_response = await llm.with_structured_output(AppSelection).ainvoke(app_selection_prompt)
        selected_app_ids = app_selection_response.app_ids

        if not selected_app_ids:
            logger.warning("LLM did not select any applications from the candidate list. Triggering retry.")
            return Command(update=update_state, goto="general_search_and_select")

        logger.success(f"Selected {len(selected_app_ids)} applications: {selected_app_ids}")

        tool_search_tasks = [
            registry.search_tools(task, app_id=app_id, distance_threshold=0.8) for app_id in selected_app_ids
        ]
        tool_results = await asyncio.gather(*tool_search_tasks)
        candidate_tools = [tool for tool_list in tool_results for tool in tool_list]

        if not candidate_tools:
            logger.warning(f"No tools found within the selected applications: {selected_app_ids}. Triggering retry.")
            return Command(update=update_state, goto="general_search_and_select")

        logger.success(f"Found {len(candidate_tools)} candidate tools from selected apps.")
        update_state["candidate_tools"] = candidate_tools
        return Command(update=update_state, goto="select_tools_for_plan")

    async def _general_search_and_select(state: AgentState) -> Command:
        """
        A retry node that performs a general tool search without app filters.
        """
        state["original_task"]
        queries = state["queries"]
        retry_count = state.get("retry_count", 0)

        if retry_count >= MAX_RETRIES:
            logger.error("Max retries reached. Failing the planning process.")
            return Command(
                update={
                    "messages": [AIMessage(content="I could not find any relevant tools after extensive searching.")]
                },
                goto="handle_failure",
            )

        logger.info(f"--- RETRY {retry_count + 1}/{MAX_RETRIES} ---")
        logger.info("Performing a general tool search without app filters.")

        general_search_tasks = [registry.search_tools(query, distance_threshold=0.85) for query in queries]
        tool_results = await asyncio.gather(*general_search_tasks)

        unique_tools = {tool["id"]: tool for tool_list in tool_results for tool in tool_list}
        candidate_tools = list(unique_tools.values())

        if not candidate_tools:
            logger.error("General search (retry) also failed to find any tools.")
            return Command(
                update={
                    "messages": [
                        AIMessage(content="I could not find any tools for your request, even with a broader search.")
                    ],
                    "retry_count": retry_count + 1,
                },
                goto="handle_failure",
            )

        logger.success(f"General search found {len(candidate_tools)} candidate tools.")
        return Command(
            update={"candidate_tools": candidate_tools, "retry_count": retry_count + 1},
            goto="select_tools_for_plan",
        )

    async def _select_tools_for_plan(state: AgentState) -> Command:
        """Selects the best tools from the candidates and builds the final execution plan."""
        task = state["original_task"]
        candidate_tools = state["candidate_tools"]
        retry_count = state.get("retry_count", 0)
        logger.info("Starting tool selection from candidate list.")

        tool_candidates_str = "\n - ".join([f"{tool['id']}: {tool['description']}" for tool in candidate_tools])
        prompt = TOOL_SELECTION_PROMPT.format(task=task, tool_candidates=tool_candidates_str)
        response = await llm.with_structured_output(ToolSelection).ainvoke(prompt)
        selected_tool_ids = response.tool_ids

        if not selected_tool_ids:
            if retry_count >= MAX_RETRIES:
                logger.error("LLM did not select any tools, even after a retry. Failing.")
                return Command(
                    update={
                        "messages": [AIMessage(content="I found potential tools, but could not create a final plan.")]
                    },
                    goto="handle_failure",
                )
            else:
                logger.warning(
                    "LLM did not select any tools from the current candidate list. Triggering general search."
                )
                return Command(goto="general_search_and_select")

        logger.success(f"Selected {len(selected_tool_ids)} tools for the final plan: {selected_tool_ids}")

        final_plan = defaultdict(list)
        for tool_id in selected_tool_ids:
            if "__" in tool_id:
                app_id, tool_name = tool_id.split("__", 1)
                final_plan[app_id].append(tool_name)

        sorted_final_plan = {app_id: sorted(tools) for app_id, tools in final_plan.items()}
        return Command(update={"execution_plan": sorted_final_plan}, goto=END)

    def _handle_planning_failure(state: AgentState) -> Command:
        """Handles cases where tool search or selection fails by logging the final error message."""
        if messages := state.get("messages"):
            last_message = messages[-1].content
            logger.error(f"Planning failed. Final message: {last_message}")
        else:
            logger.error("Planning failed with no specific message.")
        return Command(goto=END)

    workflow = StateGraph(AgentState)
    workflow.add_node("search_for_tools", _search_for_tools)
    workflow.add_node("general_search_and_select", _general_search_and_select)
    workflow.add_node("select_tools_for_plan", _select_tools_for_plan)
    workflow.add_node("handle_failure", _handle_planning_failure)

    workflow.set_entry_point("search_for_tools")

    return workflow.compile()
