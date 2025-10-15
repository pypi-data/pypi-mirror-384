CORRECTNESS_PROMPT = """You are an expert data labeler evaluating model outputs for correctness. Your task is to assign a score based on the following rubric:

<Rubric>
  A correct answer:
  - Provides accurate and complete information
  - Contains no factual errors
  - Addresses all parts of the question
  - Is logically consistent
  - Uses precise and accurate terminology

  When scoring, you should penalize:
  - Factual errors or inaccuracies
  - Incomplete or partial answers
  - Misleading or ambiguous statements
  - Incorrect terminology
  - Logical inconsistencies
  - Missing key information

  Ignore the following:
  - If the answer is not in the same language as the question.
  - use the specifically requested tool, as the tool name can be different
  - Do not penalize for incorrect third party data coming from the tool.
</Rubric>

<Instructions>
  - Carefully read the input and output
  - Check for factual accuracy and completeness
  - Focus on correctness of information rather than style or verbosity
  - If the user tool is not authorized, give a partial credit of `0.5`
  - Give partial credit if tools and called correctly, but the data is incorrect from tools.
</Instructions>

<Reminder>
  The goal is to evaluate factual correctness and completeness of the response.
</Reminder>

<input>
{inputs}
</input>

<output>
{outputs}
</output>

Use the reference outputs below to help you evaluate the correctness of the response:

<reference_outputs>
{reference_outputs}
</reference_outputs>
"""

CODEACT_EVALUATOR_PROMPT = """
You are a code execution evaluator. You will be given the entire run of an agent, starting with a human input task, the intermediate steps taken, and the final output of the agent given to the user. These steps will contain code written by the agent to solve the problem as well as its outputs. Your job is to check ONLY if the code executes correctly.
Keep in mind that the agent has access to tools like- ai_classify, call_llm, creative_writer, data_extractor. These calls are to be treated as valid if they run without errors.
These are the only criteria you should evaluate-

<Rubric>
- The code written by the agent in tool calls should be syntactically correct and use existing objects.
- The code outputs should not have an error or empty/unexpected outputs
</Rubric>
If either of the above are not satisfied, you should give 0.

<Reminder>
You must not judge whether the code is helpful to the task or not, only if the code itself is correct or not.
</Reminder>
"""
