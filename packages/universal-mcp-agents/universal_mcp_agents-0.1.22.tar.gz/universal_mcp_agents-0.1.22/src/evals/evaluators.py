from agentevals.trajectory.llm import (
    TRAJECTORY_ACCURACY_PROMPT,
    create_trajectory_llm_as_judge,
)
from google.ai.generativelanguage_v1beta import ToolConfig
from langsmith.evaluation import EvaluationResult, run_evaluator
from langsmith.schemas import Example, Run
from openevals.llm import create_llm_as_judge

from evals.prompts import CODEACT_EVALUATOR_PROMPT, CORRECTNESS_PROMPT


@run_evaluator
def exact_match_evaluator(run: Run, example: Example | None = None) -> EvaluationResult:
    """
    A simple evaluator that checks for exact match between the agent's output
    and the expected output from the dataset.
    """
    if example is None or "expected_output" not in example.outputs:
        return EvaluationResult(
            key="exact_match", score=0, comment="No expected output provided. Example: " + str(example)
        )

    # The agent's response might be in a list of messages
    agent_response_raw = run.outputs.get("output", "")
    if isinstance(agent_response_raw, list):
        # Extract text from the last dictionary in the list
        agent_response_raw = agent_response_raw[-1]

    final_answer = agent_response_raw.get("content", "").strip().lower()

    expected_output = example.outputs["expected_output"].strip().lower()
    if final_answer == expected_output:
        score = 1
        comment = "Exact match."
    else:
        score = 0
        comment = f"Mismatch: Expected '{expected_output}', but got '{final_answer}'."

    return EvaluationResult(key="exact_match", score=score, comment=comment)


correctness_evaluator = create_llm_as_judge(
    prompt=CORRECTNESS_PROMPT,
    feedback_key="correctness",
    model="anthropic:claude-4-sonnet-20250514",
)


trajectory_evaluator = create_trajectory_llm_as_judge(
    prompt=TRAJECTORY_ACCURACY_PROMPT,
    model="anthropic:claude-4-sonnet-20250514",
)


codeact_evaluator = create_llm_as_judge(
    prompt=CODEACT_EVALUATOR_PROMPT,
    feedback_key="codeact_accuracy",
    model="anthropic:claude-4-sonnet-20250514",
)


@run_evaluator
def tool_node_evaluator(run: Run, example: Example | None = None) -> EvaluationResult:
    """
    A simple evaluator that checks if the agent used the required tools.
    """
    try:
        if example is None or example.outputs is None or "required_tools" not in example.outputs:
            return EvaluationResult(
                key="tool_node", score=0, comment="No required tools provided. Example: " + str(example)
            )
        required_tools: ToolConfig = example.outputs["required_tools"]
        agent_response_raw: ToolConfig = run.outputs.get("tool_config", {})
        # Flatten the tool_configs to a single set of tool_ids
        required_tool_ids = [f"{app_id}___{tool_id}" for app_id, tools in required_tools.items() for tool_id in tools]
        agent_tool_ids = [f"{app_id}___{tool_id}" for app_id, tools in agent_response_raw.items() for tool_id in tools]
        if set(required_tool_ids).issubset(set(agent_tool_ids)):
            return EvaluationResult(key="tool_node", score=1, comment="Tool usage: " + str(required_tools))
        else:
            return EvaluationResult(key="tool_node", score=0, comment="Tool usage: " + str(required_tools))
    except Exception as e:
        return EvaluationResult(key="tool_node", score=0, comment=f"Error evaluating tool usage: {str(e)}")
