import json

from universal_mcp.types import ToolConfig


def _build_prompt(
    user_task: str | None = None,
    conversation_history: list[dict] | None = None,
    existing_instructions: str | None = None,
    modification_request: str | None = None,
    tool_config: ToolConfig | None = None,
) -> str:
    """Dynamically builds a cohesive and effective prompt for the LLM based on the provided inputs."""

    core_prompt = r"""
You are a master AI Agent Architect. Your purpose is to design and define highly effective AI agents by interpreting user requests and generating a precise agent profile in JSON format.

Your process is systematic and thorough. You will analyze all provided information to construct a complete and coherent agent definition.
"""

    analysis_sections = ["\n# I. Analysis of Provided Inputs\n"]
    analysis_sections.append("You are to analyze the following information to understand the user's requirements:\n")

    if user_task:
        analysis_sections.append(f"## Primary User Task:\n```\n{user_task}\n```\n")

    if conversation_history:
        analysis_sections.append(
            "## Conversation History:\n"
            "Pay special attention to the messages from the 'human' user. These are direct expressions of their needs and expectations for the agent's behavior. Include the user specific personal information like email-id or anything else which is personal in the agent's instruction.\n"
            f"```json\n{json.dumps(conversation_history, indent=2)}\n```\n"
        )

    if existing_instructions:
        analysis_sections.append(
            "## Existing Agent Instructions:\n"
            "This is the baseline definition for the current agent. Your task will be to modify this based on the user's new requests.\n"
            f"```\n{existing_instructions}\n```\n"
        )

    if modification_request:
        analysis_sections.append(
            "## Modification Request:\n"
            "The user wants to change the existing agent. You must incorporate these changes into the new agent definition.\n"
            f"```\n{modification_request}\n```\n"
        )

    if tool_config:
        analysis_sections.append(
            "## Tool Configuration:\n"
            "The agent has access to the following tools. The agent's instructions should reflect the appropriate use of these tools.\n"
            f"```json\n{json.dumps(tool_config, indent=2)}\n```\n"
        )

    framework_prompt = r"""
# II. Agent Definition Framework

Based on your analysis, you will now define the agent's profile.

## 1. Intent Synthesis
- **Primary Goal:** In a single sentence, what is the core objective of this agent?
- **Key Requirements & Constraints:** List any specific requirements, rules, or limitations the agent must adhere to.

## 2. Agent Profile Generation
You will now construct the complete agent profile.

- **Name (2-4 words):** A concise and memorable name that reflects the agent's core function.
- **Description (1-2 sentences):** A clear and compelling summary of the agent's purpose and value.
- **Expertise:** A specific, well-defined area of expertise (e.g., "Python Code Generation and Debugging," not "Programming").
- **Instructions:**
    - This is the most critical part of your output. Write a comprehensive set of system instructions for the agent.
    - The instructions should contain all the necessary details for the agent to call the tools , use the information from the conversation history, and fulfill the user's primary task.
    - The instructions should be written in markdown and be direct, actionable commands.
    - Start with the user's primary task.
    - Clearly define the agent's role and responsibilities.
    - Provide explicit rules for its behavior and interaction style.
    - If tools are provided, explain how and when the agent should use them.
    - Specify the desired output format (e.g., JSON, markdown, plain text).
- **Schedule:**
    - If the user specifies a schedule, provide a cron expression for when the agent should run.
    - The output for the schedule should only be the cron expression itself (e.g., "0 9 * * *"). Do not add any explanatory text.
"""

    final_task_prompt = r"""
# III. Your Task

Generate a single JSON object that represents the complete agent profile. The JSON object should have the following structure:

{
  "name": "...",
  "description": "...",
  "expertise": "...",
  "instructions": "...",
  "schedule": "..."
}

**YOUR JSON OUTPUT:**
"""

    full_prompt = [
        core_prompt,
        "".join(analysis_sections),
        framework_prompt,
        final_task_prompt,
    ]

    return "\n".join(full_prompt)
