import asyncio
from uuid import uuid4

from langgraph.checkpoint.memory import MemorySaver
from loguru import logger
from universal_mcp.agentr.registry import AgentrRegistry
from universal_mcp.types import ToolConfig

from universal_mcp.agents.builder.builder import BuilderAgent
from universal_mcp.agents.builder.state import Agent


async def run_interactive_build():
    """Simulates a multi-turn conversation to build and then modify an agent."""
    logger.info("--- SCENARIO 1: INTERACTIVE AGENT BUILD & MODIFY ---")

    registry = AgentrRegistry()
    memory = MemorySaver()
    agent = BuilderAgent(
        name="Builder Agent",
        instructions="You are a builder agent that creates other agents.",
        model="anthropic/claude-4-sonnet-20250514",
        registry=registry,
        memory=memory,
    )

    thread_id = str(uuid4())

    conversation_script = [
        "Send an email to manoj@agentr.dev with the subject 'Hello' and body 'This is a test of the Gmail agent.' from my Gmail account.",
        "Add the mail to my draft also",
        "also make a reddit post on r/test with the title 'Test Post' and body 'This is a test post from the Reddit agent.'",
    ]

    # These variables will hold the state between turns
    latest_agent: Agent | None = None
    latest_tools: ToolConfig | None = None

    for i, user_input in enumerate(conversation_script):
        logger.info(f"\n--- Conversation Turn {i + 1} ---")
        logger.info(f"User Request: '{user_input}'")

        # Construct the payload based on the current state of the conversation
        payload = {"userInput": user_input}
        if latest_agent:
            # On subsequent turns, pass the existing agent and tools for modification
            payload["agent"] = latest_agent.model_dump()  # Convert Pydantic model to dict
            payload["tools"] = latest_tools

        # The invoke method now takes a single payload dictionary
        result = await agent.invoke(thread_id=thread_id, user_input=payload)

        # Update the latest state for the next turn
        latest_agent = result.get("generated_agent")
        latest_tools = result.get("tool_config")

        if latest_agent:
            logger.info("--- Generated/Modified Agent ---")
            logger.info(f"Name: {latest_agent.name}")
            logger.info(f"Description: {latest_agent.description}")
            logger.info(f"Expertise: {latest_agent.expertise}")
            logger.info(f"Instructions:\n{latest_agent.instructions}")
            logger.info(f"Schedule: {latest_agent.schedule}")

        if latest_tools:
            logger.info("--- Selected Tools ---")
            tools_str = "\n".join(f"- {app}: {', '.join(tool_ids)}" for app, tool_ids in latest_tools.items())
            logger.info(tools_str)
        else:
            logger.info("--- Selected Tools ---")
            logger.info("No tools selected for this agent yet.")


async def run_conversation_build():
    """Simulates a one-shot agent build from a conversation history payload."""
    logger.info("\n\n--- SCENARIO 2: AGENT BUILD FROM CONVERSATION HISTORY ---")

    registry = AgentrRegistry()
    agent = BuilderAgent(
        name="Builder Agent",
        instructions="You build agents from conversation transcripts.",
        model="azure/gpt-4.1",
        registry=registry,
    )

    sample_conversation_history = [
        {"type": "human", "content": "hi"},
        {"type": "ai", "content": "Hello! How can I help you today?"},
        {"type": "human", "content": "use the zenquotes tool to tell me a quote"},
        {"type": "ai", "content": ""},
        {
            "type": "tool",
            "content": "\"Tools from zenquotes (status: connected by user):\\n - zenquotes__get_random_quote: Fetches a random inspirational quote from the Zen Quotes API via an HTTP request. It parses the JSON response to extract the quote and author, returning them as a single formatted string ('quote - author'). This function is the primary tool provided by the ZenquotesApp.\\n - zenquotes__get_random_quote: Fetches a random inspirational quote from the Zen Quotes API via an HTTP request. It parses the JSON response to extract the quote and author, returning them as a single formatted string ('quote - author'). This function is the primary tool provided by the ZenquotesApp.\\n\\nTools from perplexity (status: NOT connected by user):\\n - perplexity__answer_with_search: Queries the Perplexity Chat Completions API for a web-search-grounded answer. It sends the user's prompt and model parameters to the `/chat/completions` endpoint, then parses the response to return the synthesized content and a list of supporting source citations, ideal for real-time information retrieval.\\n - perplexity__answer_with_search: Queries the Perplexity Chat Completions API for a web-search-grounded answer. It sends the user's prompt and model parameters to the `/chat/completions` endpoint, then parses the response to return the synthesized content and a list of supporting source citations, ideal for real-time information retrieval.\\n\\nCall load_tools to select the required tools only.\"",
        },
        {"type": "ai", "content": ""},
        {
            "type": "tool",
            "content": "\"Successfully loaded 1 tools: ['zenquotes__get_random_quote']\"",
            "name": "zenquotes__get_random_quote",
        },
        {"type": "ai", "content": ""},
        {
            "type": "tool",
            "content": '"Decide upon your major definite purpose in life and then organize all your activities around it. - Brian Tracy"',
        },
        {
            "type": "ai",
            "content": 'Here’s your quote:  \n**"Decide upon your major definite purpose in life and then organize all your activities around it." – Brian Tracy**',
        },
        {"type": "human", "content": "send this quote to ankit@agentr.dev using gmail"},
        {"type": "ai", "content": ""},
        {
            "type": "tool",
            "content": '"Tools from google_mail (status: connected by user):\\n - google_mail__send_email: Composes and immediately sends an email message via the Gmail API. It can function as a reply within an existing conversation if a `thread_id` is provided. This action is distinct from `send_draft`, which sends a previously saved draft message, or `create_draft`, which only saves an email.\\n - google_mail__send_draft: Sends a pre-existing Gmail draft identified by its unique ID. It posts to the `/drafts/send` endpoint, converting a saved draft into a sent message. This function acts on drafts from `create_draft` and differs from `send_email`, which composes and sends an email in one step.\\n - google_mail__create_draft: Saves a new email draft in Gmail with a specified recipient, subject, and body. An optional thread ID can create the draft as a reply within an existing conversation, distinguishing it from `send_email`, which sends immediately.\\n - google_mail__get_draft: Retrieves a specific Gmail draft by its unique ID. This function allows specifying the output format (e.g., full, raw) to control the response detail. Unlike `list_drafts`, it fetches a single, known draft rather than a collection of multiple drafts.\\n\\nCall load_tools to select the required tools only."',
        },
        {"type": "ai", "content": ""},
        {
            "type": "tool",
            "content": "\"Successfully loaded 1 tools: ['google_mail__send_email']\"",
            "name": "google_mail__send_email",
        },
        {"type": "ai", "content": ""},
        {"type": "tool", "content": '{"id": "199765690b278b56", "threadId": "199765690b278b56", "labelIds": ["SENT"]}'},
        {"type": "ai", "content": "The quote has been sent to **ankit@agentr.dev** successfully. ✅"},
    ]

    logger.info(f"Payload Conversation History Length: {len(sample_conversation_history)} messages")

    thread_id = str(uuid4())

    # The payload contains the messages and a high-level instruction for the builder
    payload = {
        "userInput": "",
        "messages": sample_conversation_history,
    }

    result = await agent.invoke(thread_id=thread_id, user_input=payload)

    generated_agent = result.get("generated_agent")
    tool_config = result.get("tool_config")

    if generated_agent:
        logger.info("\n--- Generated Agent Profile ---")
        logger.info(f"Name: {generated_agent.name}")
        logger.info(f"Description: {generated_agent.description}")
        logger.info(f"Expertise: {generated_agent.expertise}")
        logger.info(f"Instructions:\n{generated_agent.instructions}")
        logger.info(f"Schedule: {generated_agent.schedule}")
    else:
        logger.error("Error: Agent profile was not generated.")

    if tool_config:
        logger.info("--- Final Tool Configuration ---")
        tools_str = "\n".join(f"- {app}: {', '.join(tool_ids)}" for app, tool_ids in tool_config.items())
        logger.info(tools_str)
    else:
        logger.error("Error: Tool configuration is missing.")


async def run_modification_with_manual_tool():
    """
    Simulates a scenario where a user manually adds a tool to an agent's
    configuration, and then uses the builder to modify the agent for a
    different reason, expecting the manually added tool to be preserved.
    """
    logger.info("\n\n--- SCENARIO 3: MODIFY AGENT WITH MANUAL TOOL ADDITION ---")

    registry = AgentrRegistry()
    memory = MemorySaver()
    agent = BuilderAgent(
        name="Builder Agent",
        instructions="You are a builder agent that creates other agents.",
        model="azure/gpt-4.1",
        registry=registry,
        memory=memory,
    )

    thread_id = str(uuid4())

    initial_request = "Send an email to manoj@agentr.dev with the subject 'Hello' using my Gmail account."
    logger.info(f"User Request: '{initial_request}'")

    # Initial agent creation
    initial_payload = {"userInput": initial_request}
    initial_result = await agent.invoke(thread_id=thread_id, user_input=initial_payload)

    initial_agent = initial_result.get("generated_agent")
    initial_tools = initial_result.get("tool_config")

    logger.info("--- Initial Tools ---")
    tools_str = "\n".join(f"- {app}: {', '.join(tool_ids)}" for app, tool_ids in initial_tools.items())
    logger.info(tools_str)

    # Manually add a new tool to the configuration
    manually_modified_tools = initial_tools.copy()
    manually_modified_tools["reddit"] = ["create_post"]
    logger.info("--- Manually Modified Tools ---")
    tools_str = "\n".join(f"- {app}: {', '.join(tool_ids)}" for app, tool_ids in manually_modified_tools.items())
    logger.info(tools_str)

    modification_request = "Also add the above email to my draft"
    logger.info(f"User Request: '{modification_request}'")

    # Prepare payload for modification, passing the existing agent and the manually updated tools
    modification_payload = {
        "userInput": modification_request,
        "agent": initial_agent.model_dump(),  # Convert Pydantic model to dict
        "tools": manually_modified_tools,
    }

    final_result = await agent.invoke(thread_id=thread_id, user_input=modification_payload)

    final_tools = final_result.get("tool_config")
    logger.info("--- Final Tools After Modification (should include manual addition) ---")
    tools_str = "\n".join(f"- {app}: {', '.join(tool_ids)}" for app, tool_ids in final_tools.items())
    logger.info(tools_str)


async def main():
    # await run_interactive_build()
    await run_conversation_build()
    # await run_modification_with_manual_tool()


if __name__ == "__main__":
    asyncio.run(main())
