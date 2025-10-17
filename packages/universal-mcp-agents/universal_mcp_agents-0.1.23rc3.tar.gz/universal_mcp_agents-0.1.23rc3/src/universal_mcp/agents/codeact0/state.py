from typing import Annotated, Any

from langgraph.prebuilt.chat_agent_executor import AgentState
from pydantic import BaseModel, Field


class AgentBuilderPlan(BaseModel):
    steps: list[str] = Field(description="The steps of the agent.")


class AgentBuilderCode(BaseModel):
    code: str = Field(description="The Python code for the agent.")


class AgentBuilderMeta(BaseModel):
    name: str = Field(description="Concise, title-cased agent name (3-6 words).")
    description: str = Field(description="Short, one-sentence description (<= 140 chars).")


def _enqueue(left: list, right: list) -> list:
    """Treat left as a FIFO queue, append new items from right (preserve order),
    keep items unique, and cap total size to 20 (drop oldest items)."""

    # Tool ifd are unique
    max_size = 30
    preferred_size = 20
    if len(right) > preferred_size:
        preferred_size = min(max_size, len(right))
    queue = list(left or [])

    for item in right[:preferred_size] or []:
        if item in queue:
            queue.remove(item)
        queue.append(item)

    if len(queue) > preferred_size:
        queue = queue[-preferred_size:]

    return list(set(queue))


class CodeActState(AgentState):
    """State for CodeAct agent."""

    context: dict[str, Any]
    """Dictionary containing the execution context with available tools and variables."""
    add_context: dict[str, Any]
    """Dictionary containing the additional context (functions, classes, imports) to be added to the execution context."""
    agent_builder_mode: str | None
    """State for the agent builder agent."""
    selected_tool_ids: Annotated[list[str], _enqueue]
    """Queue for tools exported from registry"""
    plan: list[str] | None
    """Plan for the agent builder agent."""
    agent_name: str | None
    """Generated agent name after confirmation."""
    agent_description: str | None
    """Generated short description after confirmation."""
