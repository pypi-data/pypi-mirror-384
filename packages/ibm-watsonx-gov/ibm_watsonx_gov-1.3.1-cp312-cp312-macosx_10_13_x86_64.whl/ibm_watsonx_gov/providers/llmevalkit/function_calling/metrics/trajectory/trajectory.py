from typing import Any, Dict, List, Union

from llmevalkit.function_calling.metrics.base import FunctionMetricsPrompt

_trajectory_system = (
    "### Task Description and Role:\n\n"
    "{{ task_description }}\n\n"
    "Your output must conform to the following JSON schema, in the same order as the fields appear in the schema:\n"
    "{{ metric_jsonschema }}"
)

_trajectory_user: str = (
    "End-to-end user to agent interaction:\n"
    "{{ trajectory }}\n\n"
    "Tool Specification:\n"
    "{{ tool_inventory }}\n\n"
    "Return a JSON object as specified in the system prompt. You MUST keep the same order of fields in the JSON object as provided in the JSON schema and examples."
)


class TrajectoryReflectionPrompt(FunctionMetricsPrompt):
    """Prompt builder for trajectory reflection metrics."""

    system_template = _trajectory_system
    user_template = _trajectory_user


def get_trajectory_reflection_prompt(
    prompt: TrajectoryReflectionPrompt,
    trajectory: Union[str, List[Dict[str, str]]],
    tool_inventory: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """
    Build the messages for a trajectory reflection evaluation.

    Returns the list of chat messages (system -> [few-shot] -> user).
    """
    return prompt.build_messages(
        user_kwargs={
            "trajectory": trajectory,
            "tool_inventory": tool_inventory,
        }
    )
