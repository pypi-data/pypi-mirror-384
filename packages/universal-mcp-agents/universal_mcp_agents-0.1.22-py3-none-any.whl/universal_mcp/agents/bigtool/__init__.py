from datetime import UTC, datetime

from langgraph.checkpoint.base import BaseCheckpointSaver
from loguru import logger
from universal_mcp.tools.registry import ToolRegistry
from universal_mcp.types import ToolConfig, ToolFormat

from universal_mcp.agents.base import BaseAgent
from universal_mcp.agents.llm import load_chat_model

from .graph import build_graph
from .prompts import SYSTEM_PROMPT
from .tools import create_meta_tools


class BigToolAgent(BaseAgent):
    def __init__(
        self,
        registry: ToolRegistry,
        name: str = "Wingman",
        instructions: str = "",
        model: str = "anthropic/claude-4-sonnet-20250514",
        tools: ToolConfig | None = None,
        memory: BaseCheckpointSaver | None = None,
        **kwargs,
    ):
        super().__init__(name, instructions, model, memory, **kwargs)

        self._tool_registry = registry
        self._tools = tools or {}
        if "ui" not in self._tools:
            self._tools["ui"] = ["create_table"]
        self.recursion_limit = kwargs.get("recursion_limit", 10)

        logger.info(f"BigToolAgent '{self.name}' initialized with model '{self.model}'.")

    def _build_system_message(self):
        return SYSTEM_PROMPT.format(
            name=self.name,
            instructions=f"**User Instructions:**\n{self.instructions}" if len(self.instructions) > 0 else "",
            system_time=datetime.now(tz=UTC).isoformat(),
        )

    async def _build_graph(self):
        """Build the LangGraph workflow"""
        try:
            default_tools = await self._tool_registry.export_tools(self._tools, ToolFormat.LANGCHAIN)
            meta_tools = create_meta_tools(self._tool_registry)
            graph_builder = build_graph(
                registry=self._tool_registry,
                base_model=load_chat_model(self.model),
                system_prompt=self._build_system_message(),
                default_tools=default_tools,
                meta_tools=meta_tools,
            )
            compiled_graph = graph_builder.compile(checkpointer=self.memory)
            return compiled_graph
        except Exception as e:
            raise Exception(f"Failed to build AutoAgent graph: {e}")

    @property
    def graph(self):
        return self._graph


__all__ = ["BigToolAgent"]
