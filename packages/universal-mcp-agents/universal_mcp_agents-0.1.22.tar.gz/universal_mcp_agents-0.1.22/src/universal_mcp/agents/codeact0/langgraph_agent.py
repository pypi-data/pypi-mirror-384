from universal_mcp.agentr.registry import AgentrRegistry

from universal_mcp.agents.codeact0 import CodeActPlaybookAgent


async def agent():
    agent_obj = CodeActPlaybookAgent(
        name="CodeAct Agent",
        instructions="Be very concise in your answers.",
        model="anthropic:claude-4-sonnet-20250514",
        tools=[],
        registry=AgentrRegistry(),
    )
    return await agent_obj._build_graph()
