import inspect
import re
from collections.abc import Sequence

from langchain_core.tools import StructuredTool

from universal_mcp.agents.codeact0.utils import schema_to_signature

uneditable_prompt = """
You are **Wingmen**, an AI Assistant created by AgentR — a creative, straight-forward, and direct principal software engineer with access to tools.

Your job is to answer the user's question or perform the task they ask for.
- Answer simple questions (which do not require you to write any code or access any external resources) directly. Note that any operation that involves using ONLY print functions should be answered directly in the chat. NEVER write a string yourself and print it.
- For task requiring operations or access to external resources, you should achieve the task by executing Python code snippets.
- You have access to `execute_ipython_cell` tool that allows you to execute Python code in an IPython notebook cell.
- You also have access to two tools for finding and loading more python functions- `search_functions` and `load_functions`, which you must use for finding functions for using different external applications or additional functionality.
    - Prioritize connected applications over unconnected ones from the output of `search_functions`.
    - When multiple apps are connected, or none of the apps are connected, YOU MUST ask the user to choose the application(s). The search results will inform you when such a case occurs, and you must stop and ask the user if multiple apps are relevant.
- In writing or natural language processing tasks DO NOT answer directly. Instead use `execute_ipython_cell` tool with the AI functions provided to you for tasks like summarizing, text generation, classification, data extraction from text or unstructured data, etc. Avoid hardcoded approaches to classification, data extraction, or creative writing.
- The code you write will be executed in a sandbox environment, and you can use the output of previous executions in your code. variables, functions, imports are retained.
- Read and understand the output of the previous code snippet and use it to answer the user's request. Note that the code output is NOT visible to the user, so after the task is complete, you have to give the output to the user in a markdown format. Similarly, you should only use print/smart_print for your own analysis, the user does not get the output.
- If needed, feel free to ask for more information from the user (without using the `execute_ipython_cell` tool) to clarify the task.

GUIDELINES for writing code:
- Variables defined at the top level of previous code snippets can be referenced in your code.
- External functions which return a dict or list[dict] are ambiguous. Therefore, you MUST explore the structure of the returned data using `smart_print()` statements before using it, printing keys and values. `smart_print` truncates long strings from data, preventing huge output logs.
- When an operation involves running a fixed set of steps on a list of items, run one run correctly and then use a for loop to run the steps on each item in the list.
- In a single code snippet, try to achieve as much as possible.
- You can only import libraries that come pre-installed with Python. However, do consider searching for external functions first, using the search and load tools to access them in the code.
- For displaying final results to the user, you must present your output in markdown format, including image links, so that they are rendered and displayed to the user. The code output is NOT visible to the user.
- Call all functions using keyword arguments only, never positional arguments.
- Async Functions (Critical): Use them only as follows-
Case 1: Top-level await without asyncio.run()
    Wrap in async function and call with asyncio.run():
    async def main():
        result = await some_async_function()
        return result
    asyncio.run(main())
Case 2: Using asyncio.run() directly
If code already contains asyncio.run(), use as-is — do not wrap again:
    asyncio.run(some_async_function())
Rules:
- Never use await outside an async function
- Never use await asyncio.run()
- Never nest asyncio.run() calls
"""

PLAYBOOK_PLANNING_PROMPT = """Now, you are tasked with creating a reusable playbook from the user's previous workflow.

TASK: Analyze the conversation history and code execution to create a step-by-step plan for a reusable function. Do not include the searching and loading of tools. Assume that the tools have already been loaded.

Your plan should:
1. Identify the key steps in the workflow
2. Mark user-specific variables that should become the main playbook function parameters using `variable_name` syntax. Intermediate variables should not be highlighted using ``
3. Keep the logic generic and reusable
4. Be clear and concise

Example:
```
1. Connect to database using `db_connection_string`
2. Query user data for `user_id`
3. Process results and calculate `metric_name`
4. Send notification to `email_address`
```

Now create a plan based on the conversation history. Enclose it between ``` and ```. Ask the user if the plan is okay."""


PLAYBOOK_CONFIRMING_PROMPT = """Now, you are tasked with confirming the playbook plan. Return True if the user is happy with the plan, False otherwise. Do not say anything else in your response. The user response will be the last message in the chain.
"""

PLAYBOOK_GENERATING_PROMPT = """Now, you are tasked with generating the playbook function. Return the function in Python code.
Do not include any other text in your response.
The function should be a single, complete piece of code that can be executed independently, based on previously executed code snippets that executed correctly.
The parameters of the function should be the same as the final confirmed playbook plan.
Do not include anything other than python code in your response
"""


def make_safe_function_name(name: str) -> str:
    """Convert a tool name to a valid Python function name."""
    # Replace non-alphanumeric characters with underscores
    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    # Ensure the name doesn't start with a digit
    if safe_name and safe_name[0].isdigit():
        safe_name = f"tool_{safe_name}"
    # Handle empty name edge case
    if not safe_name:
        safe_name = "unnamed_tool"
    return safe_name


def dedent(text):
    """Remove any common leading whitespace from every line in `text`.

    This can be used to make triple-quoted strings line up with the left
    edge of the display, while still presenting them in the source code
    in indented form.

    Note that tabs and spaces are both treated as whitespace, but they
    are not equal: the lines "  hello" and "\\thello" are
    considered to have no common leading whitespace.

    Entirely blank lines are normalized to a newline character.
    """
    # Look for the longest leading string of spaces and tabs common to
    # all lines.
    margin = None
    _whitespace_only_re = re.compile("^[ \t]+$", re.MULTILINE)
    _leading_whitespace_re = re.compile("(^[ \t]*)(?:[^ \t\n])", re.MULTILINE)
    text = _whitespace_only_re.sub("", text)
    indents = _leading_whitespace_re.findall(text)
    for indent in indents:
        if margin is None:
            margin = indent

        # Current line more deeply indented than previous winner:
        # no change (previous winner is still on top).
        elif indent.startswith(margin):
            pass

        # Current line consistent with and no deeper than previous winner:
        # it's the new winner.
        elif margin.startswith(indent):
            margin = indent

        # Find the largest common whitespace between current line and previous
        # winner.
        else:
            for i, (x, y) in enumerate(zip(margin, indent)):
                if x != y:
                    margin = margin[:i]
                    break

    # sanity check (testing/debugging only)
    if 0 and margin:
        for line in text.split("\n"):
            assert not line or line.startswith(margin), f"line = {line!r}, margin = {margin!r}"

    if margin:
        text = re.sub(r"(?m)^" + margin, "", text)
    return text


def indent(text, prefix, predicate=None):
    """Adds 'prefix' to the beginning of selected lines in 'text'.

    If 'predicate' is provided, 'prefix' will only be added to the lines
    where 'predicate(line)' is True. If 'predicate' is not provided,
    it will default to adding 'prefix' to all non-empty lines that do not
    consist solely of whitespace characters.
    """
    if predicate is None:
        # str.splitlines(True) doesn't produce empty string.
        #  ''.splitlines(True) => []
        #  'foo\n'.splitlines(True) => ['foo\n']
        # So we can use just `not s.isspace()` here.
        def predicate(s):
            return not s.isspace()

    prefixed_lines = []
    for line in text.splitlines(True):
        if predicate(line):
            prefixed_lines.append(prefix)
        prefixed_lines.append(line)

    return "".join(prefixed_lines)


def create_default_prompt(
    tools: Sequence[StructuredTool],
    additional_tools: Sequence[StructuredTool],
    base_prompt: str | None = None,
):
    system_prompt = uneditable_prompt.strip() + (
        "\n\nIn addition to the Python Standard Library, you can use the following external functions:\n"
    )
    tools_context = {}
    for tool in tools:
        if hasattr(tool, "func") and tool.func is not None:
            tool_callable = tool.func
            is_async = False
        elif hasattr(tool, "coroutine") and tool.coroutine is not None:
            tool_callable = tool.coroutine
            is_async = True
        system_prompt += f'''{"async " if is_async else ""}{schema_to_signature(tool.args, tool.name)}:
    """{tool.description}"""
    ...
    '''
        safe_name = make_safe_function_name(tool.name)
        tools_context[safe_name] = tool_callable

    for tool in additional_tools:
        if hasattr(tool, "func") and tool.func is not None:
            tool_callable = tool.func
            is_async = False
        elif hasattr(tool, "coroutine") and tool.coroutine is not None:
            tool_callable = tool.coroutine
            is_async = True
        system_prompt += f'''{"async " if is_async else ""}def {tool.name} {str(inspect.signature(tool_callable))}:
    """{tool.description}"""
    ...
    '''
        safe_name = make_safe_function_name(tool.name)
        tools_context[safe_name] = tool_callable

    if base_prompt and base_prompt.strip():
        system_prompt += f"Your goal is to perform the following task:\n\n{base_prompt}"

    return system_prompt, tools_context
