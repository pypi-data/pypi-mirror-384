import asyncio

from langgraph.checkpoint.memory import MemorySaver
from rich import print
from universal_mcp.agentr.registry import AgentrRegistry

from universal_mcp.agents.codeact0.agent import CodeActPlaybookAgent
from universal_mcp.agents.utils import messages_to_list


async def main():
    memory = MemorySaver()
    agent = CodeActPlaybookAgent(
        name="CodeAct Agent",
        instructions="Be very concise in your answers.",
        model="anthropic:claude-4-sonnet-20250514",
        tools={"google_mail": ["list_messages"]},
        registry=AgentrRegistry(),
        memory=memory,
    )
    print("Starting agent...")
    result = await agent.invoke(
        user_input="Fetch unsubscribe links from my Gmail inbox for promo emails I have received in the last 7 days"
    )
    print(messages_to_list(result["messages"]))


if __name__ == "__main__":
    asyncio.run(main())
