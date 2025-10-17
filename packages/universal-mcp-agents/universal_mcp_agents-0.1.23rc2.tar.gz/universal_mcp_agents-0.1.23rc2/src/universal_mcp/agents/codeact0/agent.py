import copy
import json
import re
import uuid
from typing import Literal, cast

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import START, StateGraph
from langgraph.types import Command, RetryPolicy, StreamWriter
from universal_mcp.tools.registry import ToolRegistry
from universal_mcp.types import ToolFormat

from universal_mcp.agents.base import BaseAgent
from universal_mcp.agents.codeact0.llm_tool import smart_print
from universal_mcp.agents.codeact0.prompts import (
    PLAYBOOK_GENERATING_PROMPT,
    PLAYBOOK_META_PROMPT,
    PLAYBOOK_PLANNING_PROMPT,
    create_default_prompt,
)
from universal_mcp.agents.codeact0.sandbox import eval_unsafe, execute_ipython_cell, handle_execute_ipython_cell
from universal_mcp.agents.codeact0.state import CodeActState, PlaybookCode, PlaybookMeta, PlaybookPlan
from universal_mcp.agents.codeact0.tools import (
    create_meta_tools,
    enter_playbook_mode,
    get_valid_tools,
)
from universal_mcp.agents.codeact0.utils import build_anthropic_cache_message, get_connected_apps_string
from universal_mcp.agents.llm import load_chat_model
from universal_mcp.agents.utils import convert_tool_ids_to_dict, filter_retry_on, get_message_text


class CodeActPlaybookAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str,
        memory: BaseCheckpointSaver | None = None,
        registry: ToolRegistry | None = None,
        playbook_registry: object | None = None,
        sandbox_timeout: int = 20,
        **kwargs,
    ):
        super().__init__(
            name=name,
            instructions=instructions,
            model=model,
            memory=memory,
            **kwargs,
        )
        self.model_instance = load_chat_model(model)
        self.playbook_model_instance = load_chat_model("azure/gpt-4.1")
        self.registry = registry
        self.playbook_registry = playbook_registry
        self.playbook = playbook_registry.get_agent() if playbook_registry else None
        self.tools_config = self.playbook.tools if self.playbook else {}
        self.eval_fn = eval_unsafe
        self.sandbox_timeout = sandbox_timeout
        self.default_tools_config = {
            "llm": ["generate_text", "classify_data", "extract_data", "call_llm"],
        }
        self.final_instructions = ""
        self.tools_context = {}
        self.exported_tools = []

    async def _build_graph(self):
        meta_tools = create_meta_tools(self.registry)
        additional_tools = [smart_print, meta_tools["web_search"]]
        self.additional_tools = [
            t if isinstance(t, StructuredTool) else StructuredTool.from_function(t) for t in additional_tools
        ]

        if self.tools_config:
            if isinstance(self.tools_config, dict):
                self.tools_config = [
                    f"{provider}__{tool}" for provider, tools in self.tools_config.items() for tool in tools
                ]
                if not self.registry:
                    raise ValueError("Tools are configured but no registry is provided")
            await self.registry.export_tools(self.tools_config, ToolFormat.LANGCHAIN)

        await self.registry.export_tools(self.default_tools_config, ToolFormat.LANGCHAIN)

        async def call_model(state: CodeActState) -> Command[Literal["execute_tools"]]:
            """This node now only ever binds the four meta-tools to the LLM."""
            messages = build_anthropic_cache_message(self.final_instructions) + state["messages"]

            agent_facing_tools = [
                execute_ipython_cell,
                enter_playbook_mode,
                meta_tools["search_functions"],
                meta_tools["load_functions"],
            ]

            if isinstance(self.model_instance, ChatAnthropic):
                model_with_tools = self.model_instance.bind_tools(
                    tools=agent_facing_tools,
                    tool_choice="auto",
                    cache_control={"type": "ephemeral", "ttl": "1h"},
                )
                if isinstance(messages[-1].content, str):
                    pass
                else:
                    last = copy.deepcopy(messages[-1])
                    last.content[-1]["cache_control"] = {"type": "ephemeral", "ttl": "5m"}
                    messages[-1] = last
            else:
                model_with_tools = self.model_instance.bind_tools(
                    tools=agent_facing_tools,
                    tool_choice="auto",
                )

            response = cast(AIMessage, model_with_tools.invoke(messages))
            if response.tool_calls:
                return Command(goto="execute_tools", update={"messages": [response]})
            else:
                return Command(update={"messages": [response], "model_with_tools": model_with_tools})

        async def execute_tools(state: CodeActState) -> Command[Literal["call_model", "playbook"]]:
            """Execute tool calls"""
            last_message = state["messages"][-1]
            tool_calls = last_message.tool_calls if isinstance(last_message, AIMessage) else []

            tool_messages = []
            new_tool_ids = []
            tool_result = ""
            effective_previous_add_context = state.get("add_context", {})
            effective_existing_context = state.get("context", {})
            # logging.info(f"Initial new_tool_ids_for_context: {new_tool_ids_for_context}")

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                try:
                    if tool_name == "enter_playbook_mode":
                        tool_message = ToolMessage(
                            content=json.dumps("Entered Playbook Mode."),
                            name=tool_call["name"],
                            tool_call_id=tool_call["id"],
                        )
                        return Command(
                            goto="playbook",
                            update={"playbook_mode": "planning", "messages": [tool_message]},  # Entered Playbook mode
                        )
                    elif tool_name == "execute_ipython_cell":
                        code = tool_call["args"]["snippet"]
                        output, new_context, new_add_context = await handle_execute_ipython_cell(
                            code,
                            self.tools_context,  # Uses the dynamically updated context
                            self.eval_fn,
                            effective_previous_add_context,
                            effective_existing_context,
                        )
                        effective_existing_context = new_context
                        effective_previous_add_context = new_add_context
                        tool_result = output
                    elif tool_name == "load_functions":
                        # The tool now does all the work of validation and formatting.
                        tool_result = await meta_tools["load_functions"].ainvoke(tool_args)

                        # We still need to update the sandbox context for `execute_ipython_cell`
                        valid_tools, _ = await get_valid_tools(tool_ids=tool_args["tool_ids"], registry=self.registry)
                        new_tool_ids.extend(valid_tools)
                        if new_tool_ids:
                            newly_exported = await self.registry.export_tools(new_tool_ids, ToolFormat.LANGCHAIN)
                            _, new_context_for_sandbox = create_default_prompt(
                                newly_exported, [], "", "", None
                            )  # is_initial_prompt is False by default
                            self.tools_context.update(new_context_for_sandbox)

                    elif tool_name == "search_functions":
                        tool_result = await meta_tools["search_functions"].ainvoke(tool_args)
                    else:
                        raise Exception(
                            f"Unexpected tool call: {tool_call['name']}. "
                            "tool calls must be one of 'enter_playbook_mode', 'execute_ipython_cell', 'load_functions', or 'search_functions'. For using functions, call them in code using 'execute_ipython_cell'."
                        )
                except Exception as e:
                    tool_result = str(e)

                tool_message = ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
                tool_messages.append(tool_message)

            return Command(
                goto="call_model",
                update={
                    "messages": tool_messages,
                    "selected_tool_ids": new_tool_ids,
                    "context": effective_existing_context,
                    "add_context": effective_previous_add_context,
                },
            )

        def playbook(state: CodeActState, writer: StreamWriter) -> Command[Literal["call_model"]]:
            playbook_mode = state.get("playbook_mode")
            if playbook_mode == "planning":
                plan_id = str(uuid.uuid4())
                writer({"type": "custom", id: plan_id, "name": "planning", "data": {"update": bool(self.playbook)}})
                planning_instructions = self.instructions + PLAYBOOK_PLANNING_PROMPT
                messages = [{"role": "system", "content": planning_instructions}] + state["messages"]

                model_with_structured_output = self.playbook_model_instance.with_structured_output(PlaybookPlan)
                response = model_with_structured_output.invoke(messages)
                plan = cast(PlaybookPlan, response)

                writer({"type": "custom", id: plan_id, "name": "planning", "data": {"plan": plan.steps}})
                return Command(
                    update={
                        "messages": [
                            AIMessage(
                                content=json.dumps(plan.model_dump()),
                                additional_kwargs={
                                    "type": "planning",
                                    "plan": plan.steps,
                                    "update": bool(self.playbook),
                                },
                            )
                        ],
                        "playbook_mode": "confirming",
                        "plan": plan.steps,
                    }
                )

            elif playbook_mode == "confirming":
                # Deterministic routing based on three exact button inputs from UI
                user_text = ""
                for m in reversed(state["messages"]):
                    try:
                        if getattr(m, "type", "") in {"human", "user"}:
                            user_text = (get_message_text(m) or "").strip()
                            if user_text:
                                break
                    except Exception:
                        continue

                t = user_text.lower()
                if t == "yes, this is great":
                    self.meta_id = str(uuid.uuid4())
                    name, description = None, None
                    if self.playbook:
                        # Update flow: use existing name/description and do not re-generate
                        name = getattr(self.playbook, "name", None)
                        description = getattr(self.playbook, "description", None)
                        writer(
                            {
                                "type": "custom",
                                id: self.meta_id,
                                "name": "generating",
                                "data": {
                                    "update": True,
                                    "name": name,
                                    "description": description,
                                },
                            }
                        )
                    else:
                        writer({"type": "custom", id: self.meta_id, "name": "generating", "data": {"update": False}})

                        meta_instructions = self.instructions + PLAYBOOK_META_PROMPT
                        messages = [{"role": "system", "content": meta_instructions}] + state["messages"]

                        model_with_structured_output = self.playbook_model_instance.with_structured_output(PlaybookMeta)
                        meta_response = model_with_structured_output.invoke(messages)
                        meta = cast(PlaybookMeta, meta_response)
                        name, description = meta.name, meta.description

                        # Emit intermediary UI update with created name/description
                        writer(
                            {
                                "type": "custom",
                                id: self.meta_id,
                                "name": "generating",
                                "data": {"update": False, "name": name, "description": description},
                            }
                        )

                    return Command(
                        goto="playbook",
                        update={
                            "playbook_mode": "generating",
                            "playbook_name": name,
                            "playbook_description": description,
                        },
                    )
                if t == "i would like to modify the plan":
                    prompt_ai = AIMessage(
                        content="What would you like to change about the plan? Let me know and I'll update the plan accordingly.",
                        additional_kwargs={"stream": "true"},
                    )
                    return Command(update={"playbook_mode": "planning", "messages": [prompt_ai]})
                if t == "let's do something else":
                    return Command(goto="call_model", update={"playbook_mode": "inactive"})

                # Fallback safe default
                return Command(goto="call_model", update={"playbook_mode": "inactive"})

            elif playbook_mode == "generating":
                generating_instructions = self.instructions + PLAYBOOK_GENERATING_PROMPT
                messages = [{"role": "system", "content": generating_instructions}] + state["messages"]

                model_with_structured_output = self.playbook_model_instance.with_structured_output(PlaybookCode)
                response = model_with_structured_output.invoke(messages)
                func_code = cast(PlaybookCode, response).code

                # Extract function name (handle both regular and async functions)
                match = re.search(r"^\s*(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", func_code, re.MULTILINE)
                if match:
                    function_name = match.group(1)
                else:
                    function_name = "generated_playbook"

                # Use generated metadata if available
                final_name = state.get("playbook_.pyname") or function_name
                final_description = state.get("playbook_description") or f"Generated playbook: {function_name}"

                # Save or update an Agent using the helper registry
                try:
                    if not self.playbook_registry:
                        raise ValueError("Playbook registry is not configured")

                    # Build instructions payload embedding the plan and function code
                    instructions_payload = {
                        "playbookPlan": state["plan"],
                        "playbookScript": func_code,
                    }

                    # Convert tool ids list to dict
                    tool_dict = convert_tool_ids_to_dict(state["selected_tool_ids"])

                    res = self.playbook_registry.upsert_agent(
                        name=final_name,
                        description=final_description,
                        instructions=instructions_payload,
                        tools=tool_dict,
                        visibility="private",
                    )
                except Exception as e:
                    raise e

                writer(
                    {
                        "type": "custom",
                        id: self.meta_id,
                        "name": "generating",
                        "data": {
                            "id": str(res.id),
                            "update": bool(self.playbook),
                            "name": final_name,
                            "description": final_description,
                        },
                    }
                )
                mock_assistant_message = AIMessage(
                    content=json.dumps(response.model_dump()),
                    additional_kwargs={
                        "type": "generating",
                        "id": str(res.id),
                        "update": bool(self.playbook),
                        "name": final_name,
                        "description": final_description,
                    },
                )

                return Command(update={"messages": [mock_assistant_message], "playbook_mode": "normal"})

        async def route_entry(state: CodeActState) -> Literal["call_model", "playbook"]:
            """Route to either normal mode or playbook creation"""
            all_tools = await self.registry.export_tools(state["selected_tool_ids"], ToolFormat.LANGCHAIN)
            # print(all_tools)

            # Create the initial system prompt and tools_context in one go
            self.final_instructions, self.tools_context = create_default_prompt(
                all_tools,
                self.additional_tools,
                self.instructions,
                await get_connected_apps_string(self.registry),
                self.playbook,
                is_initial_prompt=True,
            )
            if state.get("playbook_mode") in ["planning", "confirming", "generating"]:
                return "playbook"
            return "call_model"

        agent = StateGraph(state_schema=CodeActState)
        agent.add_node(call_model, retry_policy=RetryPolicy(max_attempts=3, retry_on=filter_retry_on))
        agent.add_node(playbook)
        agent.add_node(execute_tools)
        agent.add_conditional_edges(START, route_entry)
        return agent.compile(checkpointer=self.memory)
