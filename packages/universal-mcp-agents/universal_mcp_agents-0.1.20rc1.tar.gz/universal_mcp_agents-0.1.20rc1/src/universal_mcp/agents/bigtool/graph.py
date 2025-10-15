import json
from typing import Literal, cast

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from langgraph.types import Command, RetryPolicy
from universal_mcp.tools.registry import ToolRegistry
from universal_mcp.types import ToolFormat

from universal_mcp.agents.utils import filter_retry_on

from .state import State
from .tools import get_valid_tools

load_dotenv()


def build_graph(
    registry: ToolRegistry,
    base_model: BaseChatModel,
    system_prompt: str,
    default_tools: list[BaseTool],
    meta_tools: dict[str, BaseTool],
):
    """Build the LangGraph workflow"""

    async def agent_node(state: State) -> Command[Literal["execute_tools"]]:
        """Main agent reasoning node"""

        # Combine meta tools with currently loaded tools
        if len(state["selected_tool_ids"]) > 0:
            try:
                current_tools = await registry.export_tools(
                    tools=state["selected_tool_ids"], format=ToolFormat.LANGCHAIN
                )
            except Exception as e:
                raise Exception(f"Failed to export selected tools: {e}")
        else:
            current_tools = []
        all_tools = (
            [meta_tools["search_tools"], meta_tools["load_tools"], meta_tools.get("web_search")]
            + default_tools
            + current_tools
        )

        # Remove duplicates based on tool name
        seen_names = set()
        unique_tools = []
        for tool in all_tools:
            if tool.name not in seen_names:
                seen_names.add(tool.name)
                unique_tools.append(tool)

        try:
            if isinstance(base_model, ChatAnthropic):
                model_with_tools = base_model.bind_tools(
                    unique_tools,
                    tool_choice="auto",
                    parallel_tool_calls=False,
                    cache_control={"type": "ephemeral", "ttl": "1h"},
                )
            else:
                model_with_tools = base_model.bind_tools(
                    unique_tools,
                    tool_choice="auto",
                    parallel_tool_calls=False,
                )
        except Exception as e:
            raise Exception(f"Failed to bind tools to model: {e}")

        # Get response from model
        messages = [SystemMessage(content=system_prompt), *state["messages"]]

        try:
            response = cast(AIMessage, await model_with_tools.ainvoke(messages))
        except Exception as e:
            raise Exception(f"Model invocation failed: {e}")

        if response.tool_calls:
            return Command(goto="execute_tools", update={"messages": [response]})
        else:
            return Command(update={"messages": [response], "model_with_tools": model_with_tools})

    async def execute_tools_node(state: State) -> Command[Literal["agent"]]:
        """Execute tool calls"""
        last_message = state["messages"][-1]
        tool_calls = last_message.tool_calls if isinstance(last_message, AIMessage) else []

        tool_messages = []
        new_tool_ids = []
        ask_user = False

        for tool_call in tool_calls:
            try:
                if tool_call["name"] == "load_tools":  # Handle load_tools separately
                    valid_tools, unconnected_links = await get_valid_tools(
                        tool_ids=tool_call["args"]["tool_ids"], registry=registry
                    )
                    new_tool_ids.extend(valid_tools)
                    # Create tool message response
                    tool_result = f"Successfully loaded {len(valid_tools)} tools: {valid_tools}"
                    if unconnected_links:
                        ask_user = True
                        links = "\n".join(unconnected_links)
                        ai_msg = f"Please login to the following app(s) using the following links and let me know in order to proceed:\n {links} "

                elif tool_call["name"] == "search_tools":
                    tool_result = await meta_tools["search_tools"].ainvoke(tool_call["args"])
                elif tool_call["name"] == "web_search":
                    tool_result = await meta_tools["web_search"].ainvoke(tool_call["args"])
                else:
                    # Load tools first
                    await registry.export_tools([tool_call["name"]], ToolFormat.LANGCHAIN)
                    tool_result = await registry.call_tool(tool_call["name"], tool_call["args"])
            except Exception as e:
                tool_result = f"Error during {tool_call}: {e}"

            tool_message = ToolMessage(
                content=json.dumps(tool_result),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
            tool_messages.append(tool_message)
        if ask_user:
            tool_messages.append(AIMessage(content=ai_msg))
            return Command(update={"messages": tool_messages, "selected_tool_ids": new_tool_ids})

        return Command(goto="agent", update={"messages": tool_messages, "selected_tool_ids": new_tool_ids})

    # Define the graph
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node(
        "agent",
        agent_node,
        retry_policy=RetryPolicy(max_attempts=3, retry_on=filter_retry_on, initial_interval=2, backoff_factor=2),
    )
    workflow.add_node(
        "execute_tools",
        execute_tools_node,
        retry_policy=RetryPolicy(max_attempts=3, retry_on=filter_retry_on, initial_interval=2, backoff_factor=2),
    )

    # Set entry point
    workflow.set_entry_point("agent")

    return workflow
