import asyncio

from rich import print
from universal_mcp.agentr.registry import AgentrRegistry
from universal_mcp.logger import setup_logger

from universal_mcp.agents.llm import load_chat_model
from universal_mcp.agents.shared.tool_node import build_tool_node_graph


async def main():
    """
    An example of how to run the tool_node graph independently.
    """
    setup_logger(level="INFO")

    user_input = "What are the topics of my meetings today from Google Calendar and who are the attendees? Give a 1-line context for each attendee using LinkedIn or web search."

    print(f"▶️  User Task: [bold cyan]'{user_input}'[/bold cyan]\n")

    llm = load_chat_model("azure/gpt-4.1", thinking=False)
    registry = AgentrRegistry()

    graph = build_tool_node_graph(llm=llm, registry=registry)

    initial_state = {"original_task": user_input}

    print("🚀 Invoking the tool selection graph...")
    final_state = await graph.ainvoke(initial_state)

    execution_plan = final_state.get("execution_plan")

    print("\n[bold green]✅ Graph execution complete![/bold green]")
    print("\n--- Final Execution Plan (Selected Tools) ---")
    if execution_plan:
        print(execution_plan)
    else:
        print("[bold red]No execution plan was created.[/bold red]")
        if messages := final_state.get("messages"):
            print(f"Final Message: {messages[-1].content}")


if __name__ == "__main__":
    asyncio.run(main())
