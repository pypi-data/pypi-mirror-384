from universal_mcp.agentr.registry import AgentrRegistry
from universal_mcp.agents import get_agent
from langgraph.checkpoint.memory import MemorySaver
from universal_mcp.agents.utils import messages_to_list
import time
from loguru import logger


async def main():
    start_time = time.time()
    memory = MemorySaver()
    logger.info(f"Checkpointer: Time consumed: {time.time() - start_time}")
    agent_cls = get_agent("codeact-repl")
    logger.info(f"Get class: Time consumed: {time.time() - start_time}")
    registry = AgentrRegistry()
    logger.info(f"Init Registry: Time consumed: {time.time() - start_time}")
    agent = agent_cls(
        name="CodeAct Agent",
        instructions="Be very concise in your answers.",
        model="anthropic:claude-4-sonnet-20250514",
        tools={},
        registry=registry,
        memory=memory,
    )
    logger.info(f"Create agent: Time consumed: {time.time() - start_time}")
    print("Init agent...")
    await agent.ainit()
    logger.info(f"Init Agent: Time consumed: {time.time() - start_time}")
    print("Starting agent...")
    async for e in agent.stream(user_input="hi"):
        logger.info(f"First token: Time consumed: {time.time() - start_time}")
        print(e)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
