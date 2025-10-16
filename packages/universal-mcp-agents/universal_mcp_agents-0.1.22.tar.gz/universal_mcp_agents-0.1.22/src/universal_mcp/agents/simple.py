import asyncio
from typing import Annotated

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from rich import print
from typing_extensions import TypedDict

from universal_mcp.agents.base import BaseAgent
from universal_mcp.agents.llm import load_chat_model
from universal_mcp.agents.utils import messages_to_list

DEVELOPER_PROMPT = """
You are {name}, an helpful assistant who can answer simple questions.

Adhere to the following instructions strictly:
{instructions}
"""


class State(TypedDict):
    messages: Annotated[list, add_messages]


class SimpleAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str,
        memory: BaseCheckpointSaver = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            instructions=instructions,
            model=model,
            memory=memory,
            **kwargs,
        )
        self.llm = load_chat_model(model)

    def _build_system_message(self):
        return DEVELOPER_PROMPT.format(name=self.name, instructions=self.instructions)

    async def _build_graph(self):
        graph_builder = StateGraph(State)

        async def chatbot(state: State):
            messages = [
                {"role": "system", "content": self._build_system_message()},
                *state["messages"],
            ]
            return {"messages": [await self.llm.ainvoke(messages)]}

        graph_builder.add_node("chatbot", chatbot)
        graph_builder.add_edge(START, "chatbot")
        graph_builder.add_edge("chatbot", END)
        return graph_builder.compile(checkpointer=self.memory)


async def main():
    agent = SimpleAgent(
        name="Simple Agent",
        instructions="Act as a 14 year old kid, reply in Gen-Z lingo",
        model="azure/gpt-5-mini",
    )
    output = await agent.invoke("What is the capital of France?")
    print(messages_to_list(output["messages"]))


if __name__ == "__main__":
    asyncio.run(main())
