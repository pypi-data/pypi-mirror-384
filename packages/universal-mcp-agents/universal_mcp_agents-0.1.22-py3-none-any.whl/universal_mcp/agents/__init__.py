from typing import Literal

from universal_mcp.agents.base import BaseAgent
from universal_mcp.agents.bigtool import BigToolAgent
from universal_mcp.agents.builder.builder import BuilderAgent
from universal_mcp.agents.codeact0 import CodeActPlaybookAgent
from universal_mcp.agents.react import ReactAgent
from universal_mcp.agents.simple import SimpleAgent


def get_agent(
    agent_name: Literal["react", "simple", "builder", "bigtool", "codeact-script", "codeact-repl"],
):
    if agent_name == "react":
        return ReactAgent
    elif agent_name == "simple":
        return SimpleAgent
    elif agent_name == "builder":
        return BuilderAgent
    elif agent_name == "bigtool":
        return BigToolAgent
    elif agent_name == "codeact-repl":
        return CodeActPlaybookAgent
    else:
        raise ValueError(
            f"Unknown agent: {agent_name}. Possible values:  react, simple, builder, bigtool, codeact-script, codeact-repl"
        )


__all__ = [
    "BaseAgent",
    "ReactAgent",
    "SimpleAgent",
    "BuilderAgent",
    "BigToolAgent",
    "CodeActScript",
    "CodeActRepl",
]
