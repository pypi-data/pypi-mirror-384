# agents/base.py
from typing import cast
from uuid import uuid4

from langchain_core.messages import AIMessageChunk
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph
from langgraph.types import Command
from universal_mcp.logger import logger

from .utils import RichCLI


class BaseAgent:
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str,
        memory: BaseCheckpointSaver | None = None,
        **kwargs,
    ):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.memory = memory
        self._graph = None
        self._initialized = False
        self.cli = RichCLI()

    async def ainit(self):
        if not self._initialized:
            self._graph = await self._build_graph()
            self._initialized = True

    async def _build_graph(self) -> StateGraph:
        raise NotImplementedError("Subclasses must implement this method")

    async def stream(self, user_input: str, thread_id: str = str(uuid4()), metadata: dict = None):
        await self.ainit()
        aggregate = None

        run_metadata = {
            "agent_name": self.name,
            "is_background_run": False,  # Default to False
        }

        if metadata:
            run_metadata.update(metadata)

        run_config = {
            "recursion_limit": 50,
            "configurable": {"thread_id": thread_id},
            "metadata": run_metadata,
            "run_id": thread_id,
            "run_name": self.name,
        }

        last_ai_chunk = None
        async for event, meta in self._graph.astream(
            {"messages": [{"role": "user", "content": user_input}]},
            config=run_config,
            context={"system_prompt": self.instructions, "model": self.model},
            stream_mode=["messages", "custom"],
            stream_usage=True,
        ):
            if event == "messages" and isinstance(meta, (tuple, list)) and len(meta) == 2:
                payload, meta_dict = meta
                is_playbook = isinstance(meta_dict, dict) and meta_dict.get("langgraph_node") == "playbook"
                additional_kwargs = getattr(payload, "additional_kwargs", {}) or {}
                if is_playbook and not additional_kwargs.get("stream"):
                    continue
                if isinstance(payload, AIMessageChunk):
                    last_ai_chunk = payload
                    aggregate = payload if aggregate is None else aggregate + payload
                if "finish_reason" in payload.response_metadata:
                    logger.debug(
                        f"Finish event: {payload}, reason: {payload.response_metadata['finish_reason']}, Metadata: {meta_dict}"
                    )
                    pass
                logger.debug(f"Event: {payload}, Metadata: {meta_dict}")
                yield payload

            if event == "custom":
                yield meta

        # Send a final finished message if we saw any AI chunks (to carry usage)
        if last_ai_chunk is not None and aggregate is not None:
            event = cast(AIMessageChunk, last_ai_chunk)
            event.usage_metadata = aggregate.usage_metadata
            logger.debug(f"Usage metadata: {event.usage_metadata}")
            event.content = ""  # Clear the message since it would have already been streamed above
            yield event

    async def stream_interactive(self, thread_id: str, user_input: str):
        await self.ainit()
        with self.cli.display_agent_response_streaming(self.name) as stream_updater:
            async for event in self.stream(thread_id=thread_id, user_input=user_input):
                if isinstance(event.content, list):
                    thinking_content = "".join([c.get("thinking", "") for c in event.content])
                    stream_updater.update(thinking_content, type_="thinking")
                    content = "".join([c.get("text", "") for c in event.content])
                    stream_updater.update(content, type_="text")
                else:
                    stream_updater.update(event.content, type_="text")

    async def invoke(self, user_input: str, thread_id: str = str(uuid4()), metadata: dict = None):
        """Run the agent"""
        await self.ainit()

        run_metadata = {
            "agent_name": self.name,
            "is_background_run": False,  # Default to False
        }

        if metadata:
            run_metadata.update(metadata)

        run_config = {
            "recursion_limit": 50,
            "configurable": {"thread_id": thread_id},
            "metadata": run_metadata,
            "run_id": thread_id,
            "run_name": self.name,
        }

        result = await self._graph.ainvoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=run_config,
            context={"system_prompt": self.instructions, "model": self.model},
        )
        return result

    async def get_state(self, thread_id: str):
        await self.ainit()
        state = await self._graph.aget_state(config={"configurable": {"thread_id": thread_id}})
        return state

    async def run_interactive(self, thread_id: str = str(uuid4())):
        """Main application loop"""

        await self.ainit()
        # Display welcome
        self.cli.display_welcome(self.name)

        # Main loop
        while True:
            try:
                state = await self.get_state(thread_id=thread_id)
                if state.interrupts:
                    value = self.cli.handle_interrupt(state.interrupts[0])
                    self._graph.invoke(
                        Command(resume=value),
                        config={"configurable": {"thread_id": thread_id}},
                    )
                    continue

                user_input = self.cli.get_user_input()
                if not user_input.strip():
                    continue

                # Process commands
                if user_input.startswith("/"):
                    command = user_input.lower().lstrip("/")
                    if command == "about":
                        self.cli.display_info(f"Agent is {self.name}. {self.instructions}")
                        continue
                    elif command in {"exit", "quit", "q"}:
                        self.cli.display_info("Goodbye! 👋")
                        break
                    elif command == "reset":
                        self.cli.clear_screen()
                        self.cli.display_info("Resetting agent...")
                        thread_id = str(uuid4())
                        continue
                    elif command == "help":
                        self.cli.display_info("Available commands: /about, /exit, /quit, /q, /reset")
                        continue
                    else:
                        self.cli.display_error(f"Unknown command: {command}")
                        continue

                # Process with agent
                await self.stream_interactive(thread_id=thread_id, user_input=user_input)

            except KeyboardInterrupt:
                self.cli.display_info("\nGoodbye! 👋")
                break
            except Exception as e:
                self.cli.display_error(f"An error occurred: {str(e)}")
                break
