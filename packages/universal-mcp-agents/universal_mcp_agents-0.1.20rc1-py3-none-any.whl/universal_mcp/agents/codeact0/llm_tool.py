import json
from dataclasses import dataclass
from typing import Any, Literal, cast

from langchain.chat_models import init_chat_model
from langchain_openai import AzureChatOpenAI

from universal_mcp.agents.codeact0.utils import get_message_text, light_copy

MAX_RETRIES = 3


def get_context_str(source: Any | list[Any] | dict[str, Any]) -> str:
    """Converts context to a string representation."""
    if not isinstance(source, dict):
        if isinstance(source, list):
            source = {f"doc_{i + 1}": str(doc) for i, doc in enumerate(source)}
        else:
            source = {"content": str(source)}

    return "\n".join(f"<{k}>\n{str(v)}\n</{k}>" for k, v in source.items())


def smart_print(data: Any) -> None:
    """Prints a dictionary or list of dictionaries with string values truncated to 30 characters.

    Args:
        data: Either a dictionary with string keys, or a list of such dictionaries
    """
    print(light_copy(data))  # noqa: T201


def creative_writer(
    task: str,
    context: Any | list[Any] | dict[str, Any],
    tone: str = "normal",
    format: Literal["markdown", "html", "plain"] = "markdown",
    length: Literal["very-short", "concise", "normal", "long"] = "concise",
) -> str:
    """
    Given a high-level writing task and context, returns a well-written text
    that achieves the task, given the context.

    Example Call:
        creative_writer("Summarize this website with the goal of making it easy to understand.", web_content)
        creative_writer("Make a markdown table summarizing the key differences between doc_1 and doc_2.", {"doc_1": str(doc_1), "doc_2": str(doc_2)})
        creative_writer("Summarize all the provided documents.", [doc_1, doc_2, doc_3])

    Important:
    - Include specifics of the goal in the context verbatim.
    - Be precise and direct in the task, and include as much context as possible.
    - Include relevant high-level goals or intent in the task.
    - You can provide multiple documents as input, and reference them in the task.
    - You MUST provide the contents of any source documents to `creative_writer`.
    - NEVER use `creative_writer` to produce JSON for a Pydantic model.

    Args:
        task: The main writing task or directive.
        context: A single string, list of strings, or dict mapping labels to content.
        tone: The desired tone of the output (e.g., "normal", "flirty", "formal", "casual", "crisp", "poetic", "technical", "internet-chat", "smartass", etc.).
        format: Output format ('markdown', 'html', 'plain-text').
        length: Desired length of the output ('very-short', 'concise', 'normal', 'long').

    Returns:
        str: The generated text output.
    """

    context = get_context_str(context)

    task = task.strip() + "\n\n"
    if format == "markdown":
        task += "Please write in Markdown format.\n\n"
    elif format == "html":
        task += "Please write in HTML format.\n\n"
    else:
        task += "Please write in plain text format. Don't use markdown or HTML.\n\n"

    if tone not in ["normal", "default", ""]:
        task = f"{task} (Tone instructions: {tone})"

    if length not in ["normal", "default", ""]:
        task = f"{task} (Length instructions: {length})"

    prompt = f"{task}\n\nContext:\n{context}\n\n"

    model = AzureChatOpenAI(model="gpt-4o", temperature=0.7)

    response = model.with_retry(stop_after_attempt=MAX_RETRIES).invoke(prompt)
    return get_message_text(response)


def ai_classify(
    classification_task_and_requirements: str,
    context: Any | list[Any] | dict[str, Any],
    class_descriptions: dict[str, str],
) -> dict[str, Any]:
    """
    Classifies and compares data based on given requirements.

    Use `ai_classify` for tasks which need to classify data into one of many categories.
    If making multiple binary classifications, call `ai_classify` for each.

    Guidance:
    - Prefer to use ai_classify operations to compare strings, rather than string ops.
    - Prefer to include an "Unsure" category for classification tasks.
    - The `class_descriptions` dict argument MUST be a map from possible class names to a precise description.
    - Use precise and specific class names and concise descriptions.
    - Pass ALL relevant context, preferably as a dict mapping labels to content.
    - Returned dict maps each possible class name to a probability.

    Example Usage:
        classification_task_and_requirements = "Does the document contain an address?"
        class_descriptions = {
            "Is_Address": "Valid addresses usually have street names, city, and zip codes.",
            "Not_Address": "Not valid addresses."
        }
        classification = ai_classify(
            classification_task_and_requirements,
            {"address": extracted_address},
            class_descriptions
        )
        if classification["probabilities"]["Is_Address"] > 0.5:
            ...

    Args:
        classification_task_and_requirements: The classification question and rules.
        context: The data to classify (string, list, or dict).
        class_descriptions: Mapping from class names to descriptions.

    Returns:
        dict: {
            probabilities: dict[str, float],
            reason: str,
            top_class: str,
        }
    """

    context = get_context_str(context)

    prompt = (
        f"{classification_task_and_requirements}\n\n"
        f"\nThis is classification task\nPossible classes and descriptions:\n"
        f"{json.dumps(class_descriptions, indent=2)}\n"
        f"\nContext:\n{context}\n\n"
        "Return ONLY a valid JSON object, no extra text."
    )

    model = init_chat_model(model="claude-4-sonnet-20250514", temperature=0)

    @dataclass
    class ClassificationResult:
        probabilities: dict[str, float]
        reason: str
        top_class: str

    response = (
        model.with_structured_output(schema=ClassificationResult, method="json_mode")
        .with_retry(stop_after_attempt=MAX_RETRIES)
        .invoke(prompt)
    )
    return cast(dict[str, Any], response)


def call_llm(
    task_instructions: str, context: Any | list[Any] | dict[str, Any], output_json_schema: dict[str, Any]
) -> dict[str, Any]:
    """
    Call a Large Language Model (LLM) with an instruction and contextual information,
    returning a dictionary matching the given output_json_schema.
    Can be used for tasks like creative writing, llm reasoning based content generation, etc.

    You MUST anticipate Exceptions in reasoning based tasks which will lead to some empty fields
    in the returned output; skip this item if applicable.

    General Guidelines:
    - Be comprehensive, specific, and precise on the task instructions.
    - Include as much context as possible.
    - You can provide multiple items in context, and reference them in the task.
    - Include relevant high-level goals or intent in the task.
    - In the output_json_schema, use required field wherever necessary.
    - The more specific your task instructions and output_json_schema are, the better the results.

    Guidelines for content generation tasks:
    - Feel free to add instructions for tone, length, and format (markdown, html, plain-text, xml)
    - Some examples of tone are: "normal", "flirty", "formal", "casual", "crisp", "poetic", "technical", "internet-chat", "smartass", etc.
    - Prefer length to be concise by default. Other examples are: "very-short", "concise", "normal", "long", "2-3 lines", etc.
    - In format prefer plain-text but you can also use markdown and html wherever useful.

    Args:
        instruction: The main directive for the LLM (e.g., "Summarize the article" or "Extract key entities").
        context:
            A dictionary containing named text elements that provide additional
            information for the LLM. Keys are labels (e.g., 'article', 'transcript'),
            values are strings of content.
        output_json_schema: must be a valid JSON schema with top-level 'title' and 'description' keys.

    Returns:
        dict: Parsed JSON object matching the desired output_json_schema.

    """
    context = get_context_str(context)

    prompt = f"{task_instructions}\n\nContext:\n{context}\n\nReturn ONLY a valid JSON object, no extra text."

    model = init_chat_model(model="claude-4-sonnet-20250514", temperature=0)

    response = (
        model.with_structured_output(schema=output_json_schema, method="json_mode")
        .with_retry(stop_after_attempt=MAX_RETRIES)
        .invoke(prompt)
    )
    return cast(dict[str, Any], response)


def data_extractor(
    extraction_task: str, source: Any | list[Any] | dict[str, Any], output_json_schema: dict[str, Any]
) -> dict[str, Any]:
    """
    Extracts structured data from unstructured data (documents, webpages, images, large bodies of text),
    returning a dictionary matching the given output_json_schema.

    You MUST anticipate Exception raised for unextractable data; skip this item if applicable.

    Strongly prefer to:
    - Be comprehensive, specific, and precise on the data you want to extract.
    - Use optional fields everywhere.
    - Extract multiple items from each source unless otherwise specified.
    - The more specific your extraction task and output_json_schema are, the better the results.

    Args:
        extraction_task: The directive describing what to extract.
        source: The unstructured data to extract from.
        output_json_schema: must be a valid JSON schema with top-level 'title' and 'description' keys.

    Returns:
        dict: Parsed JSON object matching the desired output_json_schema.

    Example:
        news_articles_schema = {
            "title": "NewsArticleList",
            "description": "A list of news articles with headlines and URLs",
            "type": "object",
            "properties": {
                "articles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "headline": {
                                "type": "string"
                            },
                            "url": {
                                "type": "string"
                            }
                        },
                        "required": ["headline", "url"]
                    }
                }
            },
            "required": ["articles"]
        }

        news_articles = data_extractor("Extract headlines and their corresponding URLs.", content, news_articles_schema)
    """

    context = get_context_str(source)

    prompt = f"{extraction_task}\n\nContext:\n{context}\n\nReturn ONLY a valid JSON object, no extra text."

    model = init_chat_model(model="claude-4-sonnet-20250514", temperature=0)

    response = (
        model.with_structured_output(schema=output_json_schema, method="json_mode")
        .with_retry(stop_after_attempt=MAX_RETRIES)
        .invoke(prompt)
    )
    return cast(dict[str, Any], response)
