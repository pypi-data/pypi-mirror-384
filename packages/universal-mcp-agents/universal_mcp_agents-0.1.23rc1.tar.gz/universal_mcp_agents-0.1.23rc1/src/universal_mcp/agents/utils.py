import json
from contextlib import contextmanager
from http import HTTPStatus

import httpx
import requests
from langchain_core.messages.base import BaseMessage
from loguru import logger
from pydantic import ValidationError
from requests import JSONDecodeError
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table


class RichCLI:
    def __init__(self):
        self.console = Console()

    def display_welcome(self, agent_name: str):
        """Display welcome message"""
        welcome_text = f"""
# Welcome to {agent_name}!

Available commands:
- Type your questions naturally
- `/help` - Show help
- `/tools` - List available tools
- `/exit` - Exit the application
        """
        self.console.print(Panel(Markdown(welcome_text), title="🤖 AI Agent CLI", border_style="blue"))

    def display_agent_response(self, response: str, agent_name: str):
        """Display agent response with formatting"""
        self.console.print(f"[green]🤖 {agent_name}:[/green]")
        self.console.print(Markdown(response), style="green")

    @contextmanager
    def display_agent_response_streaming(self, agent_name: str):
        """Context manager for streaming agent response updates."""

        with Live(refresh_per_second=10, console=self.console) as live:

            class StreamUpdater:
                type_ = ""
                content = []

                def update(self, chunk: str, type_: str):
                    if not chunk:
                        return

                    # Check if type has changed and reset content if so
                    if self.type_ != type_:
                        if type_ == "thinking":
                            self.content += "\n[bold yellow]💭 Thinking:[/bold yellow] :"
                        elif type_ == "text":
                            self.content += f"\n[bold green]🤖 {agent_name}[/bold green] :"
                        self.type_ = type_
                    self.content += chunk
                    content_text = "".join(self.content)
                    live.update(content_text)

            yield StreamUpdater()

    def display_thinking(self, thought: str):
        """Display agent's thinking process"""
        if thought:
            self.console.print("[bold yellow]💭 Thinking:[/bold yellow]")
            self.console.print(thought, style="yellow")

    def display_tools(self, tools: list):
        """Display available tools in a table"""
        table = Table(title="🛠️ Available Tools")
        table.add_column("Tool Name", style="cyan")
        table.add_column("Description", style="white")

        for tool in tools:
            func_info = tool["function"]
            table.add_row(func_info["name"], func_info["description"])

        self.console.print(table)

    def display_tool_call(self, tool_call: dict):
        """Display tool call"""
        tool_call_str = json.dumps(tool_call, indent=2)
        self.console.print("[green]🛠️ Tool Call:[/green]")
        self.console.print(tool_call_str, style="green")

    def display_tool_result(self, tool_result: dict):
        """Display tool result"""
        tool_result_str = json.dumps(tool_result, indent=2)
        self.console.print("[green]🛠️ Tool Result:[/green]")
        self.console.print(tool_result_str, style="green")

    def display_error(self, error: str):
        """Display error message"""
        self.console.print(f"[red]❌ Error: {error}[/red]")

    def get_user_input(self) -> str:
        """Get user input with rich prompt"""
        return Prompt.ask("[bold blue]You[/bold blue]", console=self.console)

    def display_info(self, message: str):
        """Display info message"""
        self.console.print(f"[bold cyan]ℹ️ {message}[/bold cyan]")

    def clear_screen(self):
        """Clear the screen"""
        self.console.clear()

    def handle_interrupt(self, interrupt) -> str | bool:
        interrupt_type = interrupt.value["type"]
        if interrupt_type == "text":
            value = Prompt.ask(interrupt.value["question"])
            return value
        elif interrupt_type == "bool":
            value = Prompt.ask(interrupt.value["question"], choices=["y", "n"], default="y")
            return value
        elif interrupt_type == "choice":
            value = Prompt.ask(
                interrupt.value["question"],
                choices=interrupt.value["choices"],
                default=interrupt.value["choices"][0],
            )
            return value
        else:
            raise ValueError(f"Invalid interrupt type: {interrupt.value['type']}")


def messages_to_list(messages: list[BaseMessage]):
    return [{"type": message.type, "content": message.content} for message in messages]


def get_message_text(message: BaseMessage):
    try:
        if isinstance(message.content, str):
            return message.content
        elif isinstance(message.content, dict):
            return message.content.get("text", "")
        elif isinstance(message.content, list):
            return " ".join([c.get("text", "") for c in message.content])
        else:
            return ""
    except Exception as e:
        logger.error(f"Error getting message text: {e}")
        logger.error(f"Message: {message}")
        raise e


def filter_retry_on(exc: Exception) -> bool:
    # Transient local/network issues and parsing hiccups
    if isinstance(
        exc,
        (
            TimeoutError,
            ConnectionError,
            JSONDecodeError,
            ValidationError,
        ),
    ):
        return True

    # httpx transient request-layer errors
    if isinstance(
        exc,
        (
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadError,
        ),
    ):
        return True

    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
        return True

    # HTTP status based retries: 408 (timeout), 429 (rate limit), and 5xx
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return (
            status in {408, 429}
            or HTTPStatus.INTERNAL_SERVER_ERROR.value <= status <= HTTPStatus.NETWORK_AUTHENTICATION_REQUIRED.value
        )
    if isinstance(exc, requests.HTTPError):
        if exc.response is None:
            return True
        status = exc.response.status_code
        return (
            status in {408, 429}
            or HTTPStatus.INTERNAL_SERVER_ERROR.value <= status <= HTTPStatus.NETWORK_AUTHENTICATION_REQUIRED.value
        )

    if isinstance(
        exc,
        (
            ValueError,
            TypeError,
            ArithmeticError,
            ImportError,
            LookupError,
            NameError,
            SyntaxError,
            RuntimeError,
            ReferenceError,
            StopIteration,
            StopAsyncIteration,
            OSError,
        ),
    ):
        return False

    # Default: do not retry unknown exceptions
    return False


def convert_tool_ids_to_dict(tool_ids: list[str]) -> dict[str, list[str]]:
    """Convert list of tool ids like 'provider__tool' into a provider->tools dict.

    Any ids without the expected delimiter are ignored.
    """
    provider_to_tools: dict[str, list[str]] = {}
    for tool_id in tool_ids or []:
        if "__" not in tool_id:
            continue
        provider, tool = tool_id.split("__", 1)
        if not provider or not tool:
            continue
        if provider not in provider_to_tools:
            provider_to_tools[provider] = []
        provider_to_tools[provider].append(tool)
    return provider_to_tools
