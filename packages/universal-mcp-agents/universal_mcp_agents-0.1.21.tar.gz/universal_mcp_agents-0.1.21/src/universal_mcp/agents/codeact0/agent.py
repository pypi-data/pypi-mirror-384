import json
import re
from typing import Literal, cast
import uuid

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import START, StateGraph
from langgraph.types import Command, RetryPolicy, StreamWriter
from universal_mcp.tools.registry import ToolRegistry
from universal_mcp.types import ToolConfig, ToolFormat

from universal_mcp.agents.base import BaseAgent
from universal_mcp.agents.codeact0.llm_tool import smart_print
from universal_mcp.agents.codeact0.prompts import (
    PLAYBOOK_GENERATING_PROMPT,
    PLAYBOOK_PLANNING_PROMPT,
    create_default_prompt,
)
from universal_mcp.agents.codeact0.sandbox import eval_unsafe, execute_ipython_cell, handle_execute_ipython_cell
from universal_mcp.agents.codeact0.state import CodeActState, PlaybookCode, PlaybookPlan
from universal_mcp.agents.codeact0.tools import (
    create_meta_tools,
    enter_playbook_mode,
    get_valid_tools,
)
from universal_mcp.agents.codeact0.utils import add_tools
from universal_mcp.agents.llm import load_chat_model
from universal_mcp.agents.utils import convert_tool_ids_to_dict, filter_retry_on, get_message_text


class CodeActPlaybookAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str,
        memory: BaseCheckpointSaver | None = None,
        tools: ToolConfig | None = None,
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
        self.tools_config = tools or {}
        self.registry = registry
        self.playbook_registry = playbook_registry
        self.playbook = playbook_registry.get_agent() if playbook_registry else None
        self.eval_fn = eval_unsafe
        self.sandbox_timeout = sandbox_timeout
        self.default_tools = {
            "llm": ["generate_text", "classify_data", "extract_data", "call_llm"],
            "markitdown": ["convert_to_markdown"],
        }
        add_tools(self.tools_config, self.default_tools)

    async def _build_graph(self):
        meta_tools = create_meta_tools(self.registry)
        additional_tools = [smart_print, meta_tools["web_search"]]
        self.additional_tools = [
            t if isinstance(t, StructuredTool) else StructuredTool.from_function(t) for t in additional_tools
        ]
        if self.tools_config:
            # Convert dict format to list format if needed
            if isinstance(self.tools_config, dict):
                self.tools_config = [
                    f"{provider}__{tool}" for provider, tools in self.tools_config.items() for tool in tools
                ]
            if not self.registry:
                raise ValueError("Tools are configured but no registry is provided")

        async def call_model(state: CodeActState) -> Command[Literal["execute_tools"]]:
            messages = [{"role": "system", "content": self.final_instructions}] + state["messages"]

            # Run the model and potentially loop for reflection
            model_with_tools = self.model_instance.bind_tools(
                tools=[
                    execute_ipython_cell,
                    enter_playbook_mode,
                    meta_tools["search_functions"],
                    meta_tools["load_functions"],
                ],
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
            ask_user = False
            ai_msg = ""
            tool_result = ""
            effective_previous_add_context = state.get("add_context", {})
            effective_existing_context = state.get("context", {})

            for tool_call in tool_calls:
                try:
                    if tool_call["name"] == "enter_playbook_mode":
                        tool_message = ToolMessage(
                            content=json.dumps("Entered Playbook Mode."),
                            name=tool_call["name"],
                            tool_call_id=tool_call["id"],
                        )
                        return Command(
                            goto="playbook",
                            update={"playbook_mode": "planning", "messages": [tool_message]},  # Entered Playbook mode
                        )
                    elif tool_call["name"] == "execute_ipython_cell":
                        code = tool_call["args"]["snippet"]
                        output, new_context, new_add_context = await handle_execute_ipython_cell(
                            code,
                            self.tools_context,
                            self.eval_fn,
                            effective_previous_add_context,
                            effective_existing_context,
                        )
                        effective_existing_context = new_context
                        effective_previous_add_context = new_add_context
                        tool_result = output
                    elif tool_call["name"] == "load_functions":  # Handle load_functions separately
                        valid_tools, unconnected_links = await get_valid_tools(
                            tool_ids=tool_call["args"]["tool_ids"], registry=self.registry
                        )
                        new_tool_ids.extend(valid_tools)
                        # Create tool message response
                        tool_result = f"Successfully loaded {len(valid_tools)} tools: {valid_tools}"
                        links = "\n".join(unconnected_links)
                        if links:
                            ask_user = True
                            ai_msg = f"Please login to the following app(s) using the following links and let me know in order to proceed:\n {links} "
                    elif tool_call["name"] == "search_functions":
                        tool_result = await meta_tools["search_functions"].ainvoke(tool_call["args"])
                    else:
                        raise Exception(
                            f"Unexpected tool call: {tool_call['name']}. "
                            "tool calls must be one of 'enter_playbook_mode', 'execute_ipython_cell', 'load_functions', or 'search_functions'"
                        )
                except Exception as e:
                    tool_result = str(e)

                tool_message = ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
                tool_messages.append(tool_message)

            if new_tool_ids:
                self.tools_config.extend(new_tool_ids)
                self.exported_tools = await self.registry.export_tools(new_tool_ids, ToolFormat.LANGCHAIN)
                self.final_instructions, self.tools_context = create_default_prompt(
                    self.exported_tools, self.additional_tools, self.instructions, playbook=self.playbook
                )
            if ask_user:
                tool_messages.append(AIMessage(content=ai_msg))
                return Command(
                    update={
                        "messages": tool_messages,
                        "selected_tool_ids": new_tool_ids,
                        "context": effective_existing_context,
                        "add_context": effective_previous_add_context,
                    }
                )

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
                writer({
                    "type": "custom",
                    id: plan_id,
                    "name": "planning",
                    "data": {"update": bool(self.playbook)}
                })
                planning_instructions = self.instructions + PLAYBOOK_PLANNING_PROMPT
                messages = [{"role": "system", "content": planning_instructions}] + state["messages"]

                model_with_structured_output = self.playbook_model_instance.with_structured_output(PlaybookPlan)
                response = model_with_structured_output.invoke(messages)
                plan = cast(PlaybookPlan, response)
                
                writer({"type": "custom", id: plan_id, "name": "planning", "data": {"plan": plan.steps}})
                return Command(update={"messages": [AIMessage(content=json.dumps(plan.dict()), additional_kwargs={"type": "planning", "plan": plan.steps, "update": bool(self.playbook)})], "playbook_mode": "confirming", "plan": plan.steps})

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
                    return Command(goto="playbook", update={"playbook_mode": "generating"})
                if t == "i would like to modify the plan":
                    prompt_ai = AIMessage(content="What would you like to change about the plan? Let me know and I'll update the plan accordingly.", additional_kwargs={"stream": "true"})
                    return Command(update={"playbook_mode": "planning", "messages": [prompt_ai]})
                if t == "let's do something else":
                    return Command(goto="call_model", update={"playbook_mode": "inactive"})

                # Fallback safe default
                return Command(goto="call_model", update={"playbook_mode": "inactive"})

            elif playbook_mode == "generating":
                generate_id = str(uuid.uuid4())
                writer({
                    "type": "custom",
                    id: generate_id,
                    "name": "generating",
                    "data": {"update": bool(self.playbook)}
                })
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
                        name=function_name,
                        description=f"Generated playbook: {function_name}",
                        instructions=instructions_payload,
                        tools=tool_dict,
                        visibility="private",
                    )
                except Exception as e:
                    raise e

                writer({
                    "type": "custom",
                    id: generate_id,
                    "name": "generating",
                    "data": {"id": str(res.id), "update": bool(self.playbook)}
                })
                mock_assistant_message = AIMessage(content=json.dumps(response.dict()), additional_kwargs={"type": "generating", "id": str(res.id), "update": bool(self.playbook)})

                return Command(
                    update={"messages": [mock_assistant_message], "playbook_mode": "normal"}
                )

        async def route_entry(state: CodeActState) -> Literal["call_model", "playbook"]:
            """Route to either normal mode or playbook creation"""
            self.exported_tools = []
            self.tools_config.extend(state.get("selected_tool_ids", []))
            self.exported_tools = await self.registry.export_tools(self.tools_config, ToolFormat.LANGCHAIN)
            self.final_instructions, self.tools_context = create_default_prompt(
                self.exported_tools, self.additional_tools, self.instructions, playbook=self.playbook
            )
            if state.get("playbook_mode") in ["planning", "confirming", "generating"]:
                return "playbook"
            return "call_model"

        agent = StateGraph(state_schema=CodeActState)
        agent.add_node(call_model, retry_policy=RetryPolicy(max_attempts=3, retry_on=filter_retry_on))
        agent.add_node(playbook)
        agent.add_node(execute_tools)
        agent.add_conditional_edges(START, route_entry)
        # agent.add_edge(START, "call_model")
        return agent.compile(checkpointer=self.memory)
