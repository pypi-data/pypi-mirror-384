import asyncio

from loguru import logger
from universal_mcp.agentr.registry import AgentrRegistry

from universal_mcp.agents.bigtool import BigToolAgent


async def main():
    agent = BigToolAgent(
        registry=AgentrRegistry(),
    )
    async for event in agent.stream(
        user_input="Load a supabase tool",
        thread_id="test123",
    ):
        logger.info(event.content)


if __name__ == "__main__":
    asyncio.run(main())
