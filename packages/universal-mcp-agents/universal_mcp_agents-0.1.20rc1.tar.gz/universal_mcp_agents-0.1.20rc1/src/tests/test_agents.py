from typing import Any

import pytest
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from universal_mcp.tools.registry import ToolRegistry
from universal_mcp.types import ToolFormat

from universal_mcp.agents import get_agent
from universal_mcp.agents.base import BaseAgent
from universal_mcp.agents.builder.builder import BuilderAgent
from universal_mcp.agents.llm import load_chat_model
from universal_mcp.agents.shared.tool_node import build_tool_node_graph


class MockToolRegistry(ToolRegistry):
    """Mock implementation of ToolRegistry with an interface compatible with AgentrRegistry."""

    def __init__(self, **kwargs: Any):
        """Initialize the MockToolRegistry."""
        self._apps = [
            {
                "id": "google_mail",
                "name": "google_mail",
                "description": "Send and manage emails.",
            },
            {
                "id": "slack",
                "name": "slack",
                "description": "Team communication and messaging.",
            },
            {
                "id": "google_calendar",
                "name": "google_calendar",
                "description": "Schedule and manage calendar events.",
            },
            {
                "id": "jira",
                "name": "jira",
                "description": "Project tracking and issue management.",
            },
            {
                "id": "github",
                "name": "github",
                "description": "Code hosting, version control, and collaboration.",
            },
        ]
        self._connected_apps = ["google_mail", "google_calendar", "github"]
        self._tools = {
            "google_mail": [
                {
                    "id": "send_email",
                    "name": "send_email",
                    "description": "Send an email to a recipient.",
                },
                {
                    "id": "read_email",
                    "name": "read_email",
                    "description": "Read emails from inbox.",
                },
                {
                    "id": "create_draft",
                    "name": "create_draft",
                    "description": "Create a draft email.",
                },
            ],
            "slack": [
                {
                    "id": "send_message",
                    "name": "send_message",
                    "description": "Send a message to a team channel.",
                },
                {
                    "id": "read_channel",
                    "name": "read_channel",
                    "description": "Read messages from a channel.",
                },
            ],
            "google_calendar": [
                {
                    "id": "create_event",
                    "name": "create_event",
                    "description": "Create a new calendar event.",
                },
                {
                    "id": "find_event",
                    "name": "find_event",
                    "description": "Find an event in the calendar.",
                },
            ],
            "github": [
                {
                    "id": "create_issue",
                    "name": "create_issue",
                    "description": "Create an issue in a repository.",
                },
                {
                    "id": "get_issue",
                    "name": "get_issue",
                    "description": "Get details of a specific issue.",
                },
                {
                    "id": "create_pull_request",
                    "name": "create_pull_request",
                    "description": "Create a pull request.",
                },
                {
                    "id": "get_repository",
                    "name": "get_repository",
                    "description": "Get details of a repository.",
                },
            ],
        }
        self._tool_mappings = {
            "google_mail": {
                "email": ["send_email", "read_email", "create_draft"],
                "send": ["send_email"],
            },
            "slack": {
                "message": ["send_message", "read_channel"],
                "team": ["send_message"],
            },
            "google_calendar": {
                "meeting": ["create_event", "find_event"],
                "schedule": ["create_event"],
            },
            "github": {
                "issue": ["create_issue", "get_issue"],
                "code": ["create_pull_request", "get_repository"],
            },
        }

    async def list_all_apps(self) -> list[dict[str, Any]]:
        """Get list of available apps."""
        return self._apps

    async def get_app_details(self, app_id: str) -> dict[str, Any]:
        """Get detailed information about a specific app."""
        for app in self._apps:
            if app["id"] == app_id:
                return app
        return {}

    async def search_apps(
        self,
        query: str,
        limit: int = 10,
        distance_threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Search for apps by a query.
        MODIFIED: This mock implementation now returns ALL available apps to ensure
        the graph always has candidates to work with. This makes the test more
        robust by focusing on the agent's selection logic rather than a brittle
        mock search.
        """
        return self._apps[:limit]

    async def list_tools(
        self,
        app_id: str,
    ) -> list[dict[str, Any]]:
        """List all tools available for a specific app."""
        return self._tools.get(app_id, [])

    async def search_tools(
        self,
        query: str,
        limit: int = 10,
        app_id: str | None = None,
        distance_threshold: float = 0.8,
    ) -> list[dict[str, Any]]:
        """
        Search for tools by a query.
        MODIFIED: This mock implementation now returns all available tools for the given app_id
        to ensure robust testing of the tool selection logic, avoiding failures from a
        brittle keyword search.
        """
        if not app_id:
            # General search
            all_tools = []
            for current_app_id, tools in self._tools.items():
                for tool in tools:
                    tool_with_app_id = tool.copy()
                    tool_with_app_id["id"] = f"{current_app_id}__{tool['name']}"
                    all_tools.append(tool_with_app_id)
            return all_tools[:limit]

        # App-specific search
        all_app_tools = self._tools.get(app_id, [])
        tools_with_app_id = []
        for tool in all_app_tools:
            tool_with_app_id = tool.copy()
            tool_with_app_id["id"] = f"{app_id}__{tool['name']}"
            tools_with_app_id.append(tool_with_app_id)
        return tools_with_app_id[:limit]

    async def export_tools(
        self,
        tools: list[str],
        format: ToolFormat,
    ) -> list[Any]:
        """Exports a list of mock LangChain tools."""

        @tool
        async def mock_tool_callable(query: str):
            """A mock tool that confirms the task is done."""
            return {"status": "task has been done"}

        # Return a list of mock tools for the ReAct agent to use
        return [mock_tool_callable]

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> dict[str, Any]:
        """Call a tool with the given name and arguments."""
        return {"status": f"task has been done by tool {tool_name}"}

    async def list_connected_apps(self) -> list[dict[str, str]]:
        """
        Returns a list of apps that the user has connected/authenticated.
        This is a mock function.
        """
        return [{"app_id": app_id} for app_id in self._connected_apps]


class TestToolFinderGraph:
    @pytest.fixture
    def llm(self):
        return load_chat_model("anthropic/claude-sonnet-4-20250514", thinking=False)

    @pytest.fixture
    def registry(self):
        return MockToolRegistry()

    @pytest.mark.asyncio
    async def test_simple_case(self, llm, registry):
        """Test Case 1: Simple task requiring a single app and tool."""
        task = "Send an email to my manager about the project update."
        graph = build_tool_node_graph(llm, registry)
        final_state = await graph.ainvoke(
            {"original_task": task, "messages": [HumanMessage(content=task)], "decomposition_attempts": 0}
        )

        tool_config = final_state.get("execution_plan")

        # FIX: Assert against the correct, hyphenated app ID.
        assert "google_mail" in tool_config
        assert "send_email" in tool_config["google_mail"]

    @pytest.mark.asyncio
    async def test_multi_step_task(self, llm, registry):
        """Test Case 2: A task requiring multiple tools from different apps."""
        task = "Create a new issue for a bug in our github repository, and send a message on slack about the issue."
        graph = build_tool_node_graph(llm, registry)
        final_state = await graph.ainvoke(
            {"original_task": task, "messages": [HumanMessage(content=task)], "decomposition_attempts": 0}
        )

        tool_config = final_state.get("execution_plan")
        assert tool_config, "Execution plan should not be empty"

        assert "github" in tool_config
        assert "create_issue" in tool_config["github"]
        assert "slack" in tool_config
        assert "send_message" in tool_config["slack"]

    @pytest.mark.asyncio
    async def test_no_relevant_app(self, llm, registry):
        """Test Case 3: A task for which no tools or apps are available."""
        task = "Can you create a blog post on my wordpress site?"
        graph = build_tool_node_graph(llm, registry)
        final_state = await graph.ainvoke(
            {"original_task": task, "messages": [HumanMessage(content=task)], "decomposition_attempts": 0}
        )
        plan = final_state.get("execution_plan")
        assert not plan
        last_message = final_state.get("messages", [])[-1].content
        assert "could not create a final plan" in last_message.lower()


@pytest.mark.parametrize(
    "agent_name",
    [
        "react",
        "simple",
        "builder",
        "bigtool",
        # "codeact-script",
        # "codeact-repl",
    ],
)
class TestAgents:
    @pytest.fixture
    def agent(self, agent_name: str):
        """Set up the test environment for the agent."""
        registry = MockToolRegistry()
        agent_class = get_agent(agent_name)
        agent = agent_class(
            name=f"Test {agent_name}",
            instructions="Test instructions",
            model="anthropic/claude-sonnet-4-20250514",
            registry=registry,
        )
        return agent

    @pytest.mark.asyncio
    async def test_end_to_end_with_tool(self, agent: BaseAgent):
        """Tests the full flow from task to tool execution."""
        task = "Send an email to my manager."
        thread_id = f"test-thread-{agent.name.replace(' ', '-')}"

        await agent.ainit()
        # Invoke the agent graph to get the final state
        final_state = await agent.invoke(
            user_input={"userInput": task} if agent.name == "Test builder" else task,
            thread_id=thread_id,
        )

        # Extract the content of the last message
        if agent.name != "Test builder":
            final_messages = final_state.get("messages", [])
            assert final_messages, "The agent should have produced at least one message."
            last_message = final_messages[-1]

            final_response = last_message.content if hasattr(last_message, "content") else str(last_message)

            assert final_response is not None, "The final response should not be None."
            assert final_response != "", "The final response should not be an empty string."


class TestAgentBuilder:
    @pytest.fixture
    def agent_builder(self):
        """Set up the agent builder."""
        registry = MockToolRegistry()
        agent = BuilderAgent(
            name="Test Builder Agent",
            instructions="Test instructions for builder",
            model="gemini/gemini-2.5-flash",
            registry=registry,
        )
        yield agent

    @pytest.mark.asyncio
    async def test_create_agent(self, agent_builder: BuilderAgent):
        """Test case for creating an agent with the builder."""
        task = "Send a daily email to manoj@agentr.dev with daily agenda of the day"
        thread_id = "test-thread-create-agent"

        result = await agent_builder.invoke(thread_id=thread_id, user_input={"userInput": task})

        assert "generated_agent" in result
        generated_agent = result["generated_agent"]

        assert generated_agent.name
        assert generated_agent.description
        assert generated_agent.expertise
        assert "manoj@agentr.dev" in generated_agent.instructions
        assert generated_agent.schedule is not None

        assert "tool_config" in result
        tool_config = result["tool_config"]
        assert "google_mail" in tool_config
