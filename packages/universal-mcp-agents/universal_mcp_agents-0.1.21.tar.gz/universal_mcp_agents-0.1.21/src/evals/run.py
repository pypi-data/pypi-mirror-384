import asyncio
from datetime import datetime
from enum import Enum
from typing import Annotated, Any

import typer
from langsmith import Client, aevaluate
from langsmith.evaluation import RunEvaluator
from universal_mcp.agentr.client import AgentrClient
from universal_mcp.agentr.registry import AgentrRegistry

from evals.dataset import load_dataset
from evals.evaluators import (
    codeact_evaluator,
    correctness_evaluator,
    exact_match_evaluator,
    tool_node_evaluator,
    trajectory_evaluator,
)
from universal_mcp.agents import get_agent
from universal_mcp.agents.utils import messages_to_list

# 2. Evaluator Registry
EVALUATORS: dict[str, Any] = {
    "llm_as_judge": correctness_evaluator,
    "exact_match": exact_match_evaluator,
    "trajectory": trajectory_evaluator,
    "tool_node": tool_node_evaluator,
    "codeact": codeact_evaluator,
}


class EvaluatorName(str, Enum):
    llm_as_judge = "llm_as_judge"
    exact_match = "exact_match"
    trajectory = "trajectory"
    tool_node = "tool_node"
    codeact = "codeact"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


def get_evaluator(evaluator_name: str) -> RunEvaluator:
    """
    Retrieves an evaluator from the registry.
    """
    evaluator = EVALUATORS.get(evaluator_name)
    if evaluator is None:
        raise ValueError(f"Unknown evaluator: {evaluator_name}. Available evaluators: {', '.join(EVALUATORS.keys())}")
    return evaluator


async def agent_runner(agent_name: str, inputs: dict) -> dict:
    """
    Runs the agent and returns a dictionary with the final output.
    """
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client = AgentrClient()
    registry = AgentrRegistry(client=client) if agent_name != "simple" else None
    common_params = {
        "instructions": f"You are a helpful assistant. Keep your responses short and concise. Do not provide with any explanation. The current date and time is {current_date_time}",
        "model": "azure/gpt-4.1",
        "registry": registry,
        "tools": inputs.get("tools", {}),
    }
    agent = get_agent(agent_name)(name=agent_name, **common_params)
    result = await agent.invoke(user_input=inputs["user_input"], thread_id="evals")
    messages = messages_to_list(result["messages"])
    return_result = {"output": messages}
    if "tool_config" in result:
        return_result["tool_config"] = result["tool_config"]
    return return_result


async def run_evaluation(
    agent_name: str,
    dataset_path: str,
    evaluator_name: str,
    difficulty_split: str | None = None,
    max_concurrency: int = 1,
):
    """
    The main async function for the evaluation.
    """

    # 1. Get the agent and evaluator

    evaluator = get_evaluator(evaluator_name)

    # Create a callable for aevaluate
    async def target_func(inputs: dict):
        return await agent_runner(agent_name, inputs)

    # 2. Load the dataset from file
    dataset_examples = load_dataset(dataset_path, difficulty_split=difficulty_split)

    # 3. Upload dataset to LangSmith for the evaluation run
    client = Client()
    dataset_name = f"{dataset_path.split('/')[-1].split('.')[0]}"
    if difficulty_split:
        dataset_name = f"{dataset_name}-{difficulty_split}"
    try:
        # If dataset with same name and examples exists, read it.
        # Otherwise, a new one is created.
        dataset = client.create_dataset(
            dataset_name,
            description=f"Dataset for {agent_name} evaluation with {evaluator_name}.",
        )
        for example in dataset_examples:
            client.create_example(
                inputs={"user_input": example["user_input"], "tools": example.get("required_tools", {})},
                outputs={
                    "expected_output": example.get("expected_output", ""),
                    "required_tools": example.get("required_tools", {}),
                },
                dataset_id=dataset.id,
            )
    except Exception:
        pass

    # 4. Run the evaluation
    await aevaluate(
        target_func,
        data=dataset_name,  # Pass the dataset name
        evaluators=[evaluator],
        experiment_prefix=f"{agent_name}-{evaluator_name}-eval",
        max_concurrency=max_concurrency,
    )


app = typer.Typer()


@app.command()
def main(
    agent: Annotated[str, typer.Argument(help="The name of the agent to evaluate.")],
    dataset: Annotated[
        str,
        typer.Argument(help="Path to the dataset file (e.g., src/evals/datasets/tasks.jsonl)."),
    ],
    evaluator: Annotated[EvaluatorName, typer.Argument(help="The name of the evaluator to use.")],
    difficulty: Annotated[
        Difficulty | None,
        typer.Option(
            help="The difficulty split to use from the dataset.",
            case_sensitive=False,
        ),
    ] = None,
    concurrency: Annotated[
        int,
        typer.Option(
            help="The number of concurrent runs to execute.",
        ),
    ] = 5,
):
    """
    Run evaluations on different agents.
    """
    difficulty_value = difficulty.value if difficulty else None
    asyncio.run(
        run_evaluation(
            agent_name=agent,
            dataset_path=dataset,
            evaluator_name=evaluator.value,
            difficulty_split=difficulty_value,
            max_concurrency=concurrency,
        )
    )


if __name__ == "__main__":
    app()
