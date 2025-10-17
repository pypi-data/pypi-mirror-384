from universal_mcp.agentr.registry import AgentrRegistry

from universal_mcp.agents.bigtool import BigToolAgent


async def agent():
    agent_object = await BigToolAgent(
        registry=AgentrRegistry(),
    )._build_graph()
    return agent_object
