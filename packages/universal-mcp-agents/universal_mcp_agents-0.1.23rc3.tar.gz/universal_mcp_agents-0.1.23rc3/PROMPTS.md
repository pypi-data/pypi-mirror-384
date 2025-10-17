# Differentiating Developer and System Prompts

This document explains the roles of the two different types of prompts used by agents: the Developer Prompt and the System Prompt.

## Developer Prompt

*   **Role:** Defines the core identity, capabilities, and constraints of the agent. It's the fundamental instruction set that governs the agent's behavior.
*   **Author:** The agent developer.
*   **Nature:** Static. It is part of the agent's source code and does not change between different runs or users.
*   **Example:** "You are a helpful assistant that can write code. You are an expert in Python. You must not engage in harmful conversations."

## System Prompt

*   **Role:** Provides init time context to the agent. This includes user-specific information, environment details, or any other dynamic data that can influence the agent's response for a specific interaction.
*   **Author:** The agent platform or the system running the agent.
*   **Nature:** Dynamic. It can change with every request or for every user.
*   **Example:** "The current user is John Doe. The current date is 2025-09-09. The user's timezone is UTC. The user is working on a project located at /path/to/project."

## User Input

* Provided everytime by user to trigger the agent

## How they work together

The developer prompt and system prompt are combined to form the final set of instructions for the LLM. Typically, the developer prompt comes first, establishing the agent's persona and rules, followed by the system prompt which provides the immediate context for the current task.

This separation allows for building robust, general-purpose agents (via developer prompts) that can be adapted to specific situations (via system prompts) without altering their core logic.
