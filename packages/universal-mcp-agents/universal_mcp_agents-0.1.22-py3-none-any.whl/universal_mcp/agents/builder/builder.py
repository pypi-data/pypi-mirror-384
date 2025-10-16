import asyncio
import json

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from loguru import logger
from universal_mcp.tools.registry import ToolRegistry
from universal_mcp.types import ToolConfig

from universal_mcp.agents.base import BaseAgent
from universal_mcp.agents.builder.helper import (
    _clean_conversation_history,
    _extract_tools_from_history,
    _merge_tool_configs,
)
from universal_mcp.agents.builder.prompts import _build_prompt
from universal_mcp.agents.builder.state import Agent, BuilderState
from universal_mcp.agents.llm import load_chat_model
from universal_mcp.agents.shared.tool_node import build_tool_node_graph


class BuilderAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str,
        registry: ToolRegistry,
        memory: BaseCheckpointSaver | None = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            instructions=instructions,
            model=model,
            memory=memory,
            **kwargs,
        )
        self.registry = registry
        self.llm = load_chat_model(model, thinking=False)

    async def invoke(
        self,
        thread_id: str,
        user_input: dict,
    ):
        """
        Overrides BaseAgent.invoke to build or modify an agent.
        This is the primary entry point for the Builder Agent.
        """
        keys = ("userInput", "agent", "tools", "messages")
        userInput, agent_data, tools, messages = (user_input.get(k) for k in keys)
        agent = Agent(**agent_data) if agent_data else None

        await self.ainit()
        graph = self._graph

        initial_state = BuilderState(
            user_task=userInput,
            generated_agent=agent,
            tool_config=tools,
            messages=[],
        )

        if messages:
            initial_state["messages"] = [HumanMessage(content=json.dumps(messages))]
        elif not userInput and not agent:
            raise ValueError("Either 'user_input' or 'messages' must be provided for a new agent.")

        run_metadata = {"agent_name": self.name, "is_background_run": False}

        config = {
            "configurable": {"thread_id": thread_id},
            "metadata": run_metadata,
            "run_id": thread_id,
            "run_name": self.name,
        }

        final_state = await graph.ainvoke(initial_state, config=config)
        return final_state

    def _entry_point_router(self, state: BuilderState):
        """
        Determines the entry point of the graph based on the initial state.
        """
        has_agent = state.get("generated_agent") is not None
        has_messages = bool(state.get("messages"))
        has_user_task = bool(state.get("user_task"))

        if has_agent:
            logger.info("Routing to: modify_agent.")
            return "modify_agent"
        elif has_messages:
            logger.info("Routing to: create_agent_from_history.")
            return "create_agent_from_history"
        elif has_user_task:
            logger.info("Routing to: create_agent_from_input.")
            return "create_agent_from_input"
        else:
            raise ValueError("Invalid initial state. Cannot determine route.")

    async def _create_agent_from_input(self, state: BuilderState) -> Command:
        """SCENARIO 1: Generates a new agent from a single user_input, running agent and tool creation in parallel."""
        user_task = state["user_task"]
        logger.info(f"Creating new agent from input: '{user_task}'")

        structured_llm = self.llm.with_structured_output(Agent)

        async def _task_generate_agent():
            prompt = _build_prompt(user_task=user_task)
            return await structured_llm.ainvoke(prompt)

        async def _task_find_tools():
            return await self._get_tool_config_for_task(user_task)

        # Run agent creation and tool finding concurrently for max efficiency
        agent_profile, tool_config = await asyncio.gather(_task_generate_agent(), _task_find_tools())

        logger.info(f"Successfully created agent '{agent_profile.name}' with tools: {tool_config}")

        return Command(
            update={"generated_agent": agent_profile, "tool_config": tool_config},
            goto=END,
        )

    async def _create_agent_from_history(self, state: BuilderState) -> Command:
        """SCENARIO 2: Generates an agent by synthesizing a conversation history."""
        user_task = state.get("user_task")

        content_str = state["messages"][-1].content
        raw_history = json.loads(content_str)
        conversation_history = _clean_conversation_history(raw_history)

        logger.info(f"Creating new agent from conversation history (length: {len(conversation_history)}).")

        # 1. Generate the agent profile first to get the definitive instructions
        tools_from_history = _extract_tools_from_history(raw_history)
        prompt = _build_prompt(
            user_task=user_task,
            conversation_history=conversation_history,
            tool_config=tools_from_history,
        )
        structured_llm = self.llm.with_structured_output(Agent)
        generated_agent = await structured_llm.ainvoke(prompt)
        logger.info(f"Successfully generated agent profile for '{generated_agent.name}'.")

        # 2. Synthesize tool configuration based on the new instructions and history
        tools_from_instructions = await self._get_tool_config_for_task(generated_agent.instructions)

        final_tool_config = _merge_tool_configs(tools_from_history, tools_from_instructions)
        logger.info(f"Final synthesized tool configuration: {final_tool_config}")

        return Command(
            update={
                "generated_agent": generated_agent,
                "tool_config": final_tool_config,
            },
            goto=END,
        )

    async def _modify_agent(self, state: BuilderState) -> Command:
        """SCENARIO 3: Modifies an existing agent and re-evaluates its tool configuration."""
        existing_agent = state["generated_agent"]
        modification_request = state["user_task"]
        existing_tools = state["tool_config"]

        logger.info(f"Modifying existing agent '{existing_agent.name}' with request: '{modification_request}'")

        # 1. Generate the modified agent profile to get the new definitive instructions
        prompt = _build_prompt(
            existing_instructions=existing_agent.instructions,
            modification_request=modification_request,
        )
        structured_llm = self.llm.with_structured_output(Agent)
        modified_agent = await structured_llm.ainvoke(prompt)
        logger.info(f"Successfully generated modified agent profile for '{modified_agent.name}'.")

        # 2. Update tool configuration based on the NEW instructions, preserving existing tools
        tools_from_new_instructions = await self._get_tool_config_for_task(modified_agent.instructions)
        final_tool_config = _merge_tool_configs(existing_tools, tools_from_new_instructions)
        logger.info(f"Final updated tool configuration: {final_tool_config}")

        return Command(
            update={
                "generated_agent": modified_agent,
                "tool_config": final_tool_config,
            },
            goto=END,
        )

    async def _get_tool_config_for_task(self, task: str) -> ToolConfig:
        """Helper method to find and configure tools for a given task string."""
        if not task:
            return {}
        tool_finder_graph = build_tool_node_graph(self.llm, self.registry)
        final_state = await tool_finder_graph.ainvoke({"original_task": task})
        return final_state.get("execution_plan") or {}

    async def _build_graph(self):
        """Builds the conversational agent graph with the new, scenario-based structure."""
        builder = StateGraph(BuilderState)

        # Add the three self-contained nodes for each scenario
        builder.add_node("create_agent_from_input", self._create_agent_from_input)
        builder.add_node("create_agent_from_history", self._create_agent_from_history)
        builder.add_node("modify_agent", self._modify_agent)

        # The entry point router directs to one of the three nodes, and they all go to END
        builder.add_conditional_edges(START, self._entry_point_router)

        return builder.compile(checkpointer=self.memory)
