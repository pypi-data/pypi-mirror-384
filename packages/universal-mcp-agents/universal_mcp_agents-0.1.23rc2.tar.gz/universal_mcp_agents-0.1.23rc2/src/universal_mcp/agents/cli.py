import asyncio

from langgraph.checkpoint.memory import MemorySaver
from typer import Typer
from universal_mcp.agentr.client import AgentrClient
from universal_mcp.agentr.registry import AgentrRegistry
from universal_mcp.logger import setup_logger

from universal_mcp.agents import get_agent

app = Typer()


@app.command(
    help="Run the agent CLI",
    epilog="""
    Example:
    mcp client run --config client_config.json
    """,
)
def run(name: str = "react"):
    """Run the agent CLI"""

    setup_logger(log_file=None, level="ERROR")
    client = AgentrClient()
    params = {
        "instructions": "You are a helpful assistant",
        "model": "azure/gpt-4.1",
        "registry": AgentrRegistry(client=client),
        "memory": MemorySaver(),
    }
    agent_cls = get_agent(name)
    agent = agent_cls(name=name, **params)
    asyncio.run(agent.run_interactive())


if __name__ == "__main__":
    app()
