from collections.abc import Sequence
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from universal_mcp.types import ToolConfig


class Agent(BaseModel):
    """Agent that can be created by the builder."""

    name: str = Field(description="Name of the agent.")
    description: str = Field(description="A small description of the agent.")
    expertise: str = Field(description="The expertise of the agent.")
    instructions: str = Field(description="The instructions for the agent to follow.")
    schedule: str | None = Field(description="The cron expression for the agent to run on.", default=None)


class BuilderState(TypedDict):
    user_task: str | None
    generated_agent: Agent | None
    tool_config: ToolConfig | None
    messages: Annotated[Sequence[BaseMessage], add_messages]
