import ast
import asyncio
import json
import uuid
from typing import List, Dict, Any

from llmevalkit.function_calling.consts import (
    METRIC_AGENTIC_CONSTRAINTS_SATISFACTION,
    METRIC_FUNCTION_SELECTION_APPROPRIATENESS,
    METRIC_GENERAL_HALLUCINATION_CHECK,
    METRIC_GENERAL_VALUE_FORMAT_ALIGNMENT,
    METRIC_PARAMETER_HALLUCINATION_CHECK,
    METRIC_PARAMETER_VALUE_FORMAT_ALIGNMENT,
)
from llmevalkit.function_calling.pipeline.pipeline import ReflectionPipeline
from llmevalkit.function_calling.pipeline.types import ToolCall, ToolSpec
from llmevalkit.llm.base import get_llm


def convert_tool_calls_to_openai_format(
    tool_calls: List[Dict[str, Any]],
) -> List[ToolCall]:
    """
    Convert a list of tool calls into OpenAI-compatible tool call format.

    Args:
        tool_calls (List[Dict[str, Any]]): Input tool calls in format:
            [{"name": "...", "arguments": {...}}]

    Returns:
        List[Dict[str, Any]]: Tool calls in OpenAI format.
    """
    openai_tool_calls = []
    for call in tool_calls:
        openai_tool_calls.append(
            ToolCall(
                **{
                    "id": f"call_{uuid.uuid4().hex[:8]}",  # unique id
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": json.dumps(call.get("arguments", {})),
                    },
                }
            )
        )
    return openai_tool_calls


class ConversationFormatError(ValueError):
    """Raised when the conversation format is invalid for this extractor."""


def extract_tool_specs_from_conversation(
    conversation: List[Dict[str, Any]], remove_turn: bool = False
) -> List[Dict[str, Any]]:
    """
    Extract tool specifications from the system turn in the conversation history.
    The function looks for a system message whose content contains a list of tool specs (as a stringified list of dicts),
    parses it, and returns it as a list of dictionaries.

    Args:
        conversation: List of conversation turns.
        remove_turn: If True, remove the tool specification turn from the conversation.

    Returns:
        List of tool specifications as dictionaries.

    Raises:
        ConversationFormatError: If no valid tool specifications are found in the conversation.
    """
    import ast

    for i, turn in enumerate(conversation):
        if turn.get("role") == "system":
            content = turn.get("content", "")
            # Heuristic: look for a string that looks like a list of dicts (starts with [ and contains 'function')
            # and is not markdown or code block formatted
            # Try to find the first occurrence of a list starting with [ and ending with ]
            start = content.find("[")
            end = content.rfind("]")
            if start != -1 and end != -1 and "function" in content[start:end]:
                possible_list = content[start : end + 1]
                try:
                    # Use ast.literal_eval for safety (content is usually single quotes)
                    tool_specs = ast.literal_eval(possible_list)
                    if isinstance(tool_specs, list):
                        # If requested, remove the turn containing tool specs from the conversation
                        if remove_turn:
                            conversation.pop(i)
                        return tool_specs
                except Exception:
                    pass

    # If we got here, we didn't find any valid tool specifications
    raise ConversationFormatError("No valid tool specifications found in conversation.")


def extract_tool_calls_to_reflect(
    conversation: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract tool calls to reflect by identifying patterns in the conversation.

    The function looks for two patterns:
    1. An assistant message with content 'Act: (Please return only a JSON string)'
       followed by a user message containing the JSON tool calls
    2. An assistant message containing "Act:" followed by a tool call in JSON format
       within the same message

    Args:
        conversation: List of conversation turns

    Returns:
        A flat list of tool call dicts: [{"name": "GenerateKyvernoTool", "arguments": {...}}, ...]

    Raises:
        ConversationFormatError: On validation or parsing issues
    """
    if not conversation:
        raise ConversationFormatError("Conversation is empty.")

    tool_calls = []

    # Pattern 1: Look for the pattern where the tool call is in the message following "Act:" message
    for i in range(len(conversation) - 1):  # Stop at the second-to-last message
        current_turn = conversation[i]
        next_turn = conversation[i + 1]

        # Look for assistant message with the specific marker
        if (
            current_turn.get("role") == "assistant"
            and isinstance(current_turn.get("content"), str)
            and "Act: (Please return only a JSON string)" in current_turn.get("content")
        ):
            # The next message should contain the JSON for the tool call
            content = next_turn.get("content", "")
            if isinstance(content, str):
                # Try to parse the content directly first
                try:
                    parsed = ast.literal_eval(content)
                    if isinstance(parsed, list):
                        for item in parsed:
                            if isinstance(item, dict) and "name" in item:
                                tool_calls.append(item)
                except (SyntaxError, ValueError):
                    # Continue to next pattern if this fails
                    pass

    # Pattern 2: Look for "Act:" followed by JSON tool call in the same message
    if not tool_calls:
        for turn in conversation:
            if turn.get("role") == "assistant" and isinstance(turn.get("content"), str):
                content = turn.get("content", "")
                # Look for the pattern "Act: \n[{...}]"
                if "Act:" in content:
                    act_start = content.find("Act:")
                    if act_start != -1:
                        # Find the start of the JSON array after "Act:"
                        json_start = content.find("[", act_start)
                        json_end = content.rfind("]", act_start)

                        if (
                            json_start != -1
                            and json_end != -1
                            and json_start < json_end
                        ):
                            # Extract the JSON array
                            json_str = content[json_start : json_end + 1]
                            try:
                                # Try to parse the content
                                parsed = json.loads(json_str)
                                if isinstance(parsed, list):
                                    for item in parsed:
                                        if (
                                            isinstance(item, dict)
                                            and "name" in item
                                            and "arguments" in item
                                        ):
                                            tool_calls.append(item)
                            except json.JSONDecodeError:
                                # Try with ast.literal_eval as a fallback
                                try:
                                    parsed = ast.literal_eval(json_str)
                                    if isinstance(parsed, list):
                                        for item in parsed:
                                            if (
                                                isinstance(item, dict)
                                                and "name" in item
                                                and "arguments" in item
                                            ):
                                                tool_calls.append(item)
                                except (SyntaxError, ValueError):
                                    # Continue to next message if this fails
                                    pass

    if not tool_calls:
        raise ConversationFormatError(
            "No valid tool calls found to reflect in the conversation."
        )

    return tool_calls


async def reflect_ciso_agent_conversation(
    conversation: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Reflect the CISO agent conversation by extracting relevant information from the conversation history.
    """
    # Extract tool specifications and remove that turn from conversation
    tool_specs = extract_tool_specs_from_conversation(conversation, remove_turn=True)

    tool_specs_objs = [
        ToolSpec(**spec) for spec in tool_specs if isinstance(spec, dict)
    ]

    # Extract tool calls from the conversation
    tool_calls = extract_tool_calls_to_reflect(conversation)
    converted_tool_calls = convert_tool_calls_to_openai_format(tool_calls)

    # Define ReflectionPipeline object
    MetricsClientCls = get_llm("litellm.rits.output_val")
    metrics_client = MetricsClientCls(
        model_name="meta-llama/llama-4-maverick-17b-128e-instruct-fp8",
    )
    reflection_pipeline = ReflectionPipeline(
        metrics_client=metrics_client,
        general_metrics=[
            METRIC_GENERAL_HALLUCINATION_CHECK,
            METRIC_GENERAL_VALUE_FORMAT_ALIGNMENT,
        ],
        function_metrics=[
            METRIC_FUNCTION_SELECTION_APPROPRIATENESS,
            METRIC_AGENTIC_CONSTRAINTS_SATISFACTION,
        ],
        parameter_metrics=[
            # METRIC_PARAMETER_VALUE_FORMAT_ALIGNMENT,
            # METRIC_PARAMETER_HALLUCINATION_CHECK,
        ],
        runtime_pipeline=True,  # Uncomment this line to enable evaluation pipeline,
        # i.e. with actionable recommendations for the agent development.
    )

    # Reflect the tool calls in the conversation
    reflection_outputs = []
    for tool_call_to_reflect in converted_tool_calls:
        reflection_outputs.append(
            await reflection_pipeline.run_async(
                conversation=conversation,
                inventory=tool_specs_objs,
                call=tool_call_to_reflect,
                continue_on_static=True,
            )
        )

    return reflection_outputs


def create_reflection_result_summary(
    reflection_output: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate the final result with syntactic_errors, semantic_errors, and corrections.
    """
    original_tool_call = reflection_output["inputs"]["tool_call"]["function"]
    result = {
        "syntactic_errors": {},
        "semantic_errors": {},
        "corrections": {},
        "overall_valid": reflection_output.get("overall_valid"),
        "original_tool_call": {
            "name": original_tool_call["name"],
            "arguments": original_tool_call["parsed_arguments"],
        },
    }

    # 1. Process syntactic errors from static metrics
    static = reflection_output.get("static", {})
    static_metrics = static.get("metrics", {})
    for metric_name, metric_data in static_metrics.items():
        if not metric_data.get("valid", True):
            explanation = metric_data.get("explanation", "No explanation provided")
            result["syntactic_errors"][metric_name] = explanation

    # 2. Process semantic errors - prioritize function_selection over general
    semantic = reflection_output.get("semantic", {})

    # Check function_selection metrics first
    function_selection = semantic.get("function_selection", {})
    if function_selection:  # Only process if function_selection exists
        function_selection_metrics = function_selection.get("metrics", {})

        for metric_name, metric_data in function_selection_metrics.items():
            if metric_data.get("is_issue", False):
                raw_response = metric_data.get("raw_response", {})
                explanation = raw_response.get("explanation", "No explanation provided")
                result["semantic_errors"][metric_name] = explanation

                # Add corrections from function_selection based on specific error types
                correction = raw_response.get("correction", {})
                if metric_name == "function_selection_appropriateness" and (
                    "corrected_function" in correction
                    or "corrected_function_name" in correction
                ):
                    # For function selection errors, we only need the tool name
                    corrected_func = correction.get(
                        "corrected_function"
                    ) or correction.get("corrected_function_name")
                    if corrected_func == "no_function":
                        pass
                    elif isinstance(corrected_func, dict) and "name" in corrected_func:
                        result["corrections"]["corrected_tool_name"] = corrected_func[
                            "name"
                        ]
                    elif isinstance(corrected_func, str):
                        try:
                            parsed = json.loads(corrected_func)
                            if isinstance(parsed, dict) and "name" in parsed:
                                result["corrections"]["corrected_tool_name"] = parsed[
                                    "name"
                                ]
                        except json.JSONDecodeError:
                            result["corrections"][
                                "corrected_tool_name"
                            ] = corrected_func
                elif (
                    metric_name == "agentic_constraints_satisfaction"
                    and "prerequisite_tool_calls" in correction
                ):
                    if correction["prerequisite_tool_calls"]:  # Only add if not empty
                        result["corrections"]["prerequisite_tool_calls"] = correction[
                            "prerequisite_tool_calls"
                        ]

    # Only process general metrics if no function_selection errors
    # if not has_function_selection_errors:
    general = semantic.get("general", {})
    if general:  # Only process if general exists
        general_metrics = general.get("metrics", {})

        for metric_name, metric_data in general_metrics.items():
            if metric_data.get("is_issue", False):
                raw_response = metric_data.get("raw_response", {})
                explanation = raw_response.get("explanation", "No explanation provided")
                result["semantic_errors"][metric_name] = explanation

                # Add corrections from general metrics based on specific error types
                correction = raw_response.get("correction", {})
                if (
                    metric_name
                    in ["general_hallucination_check", "value_format_alignment"]
                    and "tool_call" in correction
                ):
                    # For general errors, we provide the complete corrected tool call
                    corrected_call = correction["tool_call"]
                    if isinstance(corrected_call, str):
                        try:
                            corrected_call = json.loads(corrected_call)
                        except json.JSONDecodeError:
                            pass  # Keep as string if parsing fails
                    if corrected_call:
                        result["corrections"]["corrected_tool_call"] = corrected_call

    return result


if __name__ == "__main__":
    # Example usage
    # tool_call = [
    #     {
    #         "name": "GenerateKyvernoTool",
    #         "arguments": {
    #             "sentence": "Generate a Kyverno policy to check if the cluster-admin role is only used where required.",
    #             "policy_file": "/tmp/agent/20250122154450/policy.yaml",
    #         },
    #     }
    # ]

    # tool_calls_converted = convert_tool_calls_to_openai_format(tool_call)
    # for tool_call in tool_calls_converted:
    #     print(tool_call.model_dump_json(indent=2))

    # tool_specs = [
    #     {
    #         "type": "function",
    #         "function": {
    #             "name": "GenerateKyvernoTool",
    #             "description": "The tool to generate a Kyverno policy. This tool returns the generated Kyverno policy. This can be used for updating existing Kyverno policy.\n",
    #             "parameters": {
    #                 "type": "object",
    #                 "properties": {
    #                     "sentence": {
    #                         "type": "str",
    #                         "description": "A comprehensive description to request Kyverno policy generation.\nThis must be containing any level of details about the Kyverno policy to be generated.\nIf you got any errors especially about syntax when you invoked this function previously, mention it here for improving the generation result this time.\nFor example, when you got an error like `.spec.rules[0].match.any[0].selector: field not declared in schema`, add the following to the sentence: `previous trial failed because .spec.rules[0].match.any[0].selector is not available field for Kyverno policy`\n",
    #                     },
    #                     "policy_file": {
    #                         "type": "str",
    #                         "description": "filepath for the Kyverno policy to be saved.",
    #                     },
    #                     "current_policy_file": {
    #                         "type": "str",
    #                         "description": "filepath of the current Kyverno policy to be updated. Only needed when updating an existing policy",
    #                         "default": "",
    #                     },
    #                 },
    #                 "required": ["sentence", "policy_file"],
    #             },
    #         },
    #     },
    #     {
    #         "type": "function",
    #         "function": {
    #             "name": "RunKubectlTool",
    #             "description": 'The tool to execute a kubectl command.\nThis tool returns the following:\n  - return_code: if 0, the command was successful, otherwise, failure.\n  - stdout: standard output of the command (only when `return_output` is True)\n  - stderr: standard error of the command (only when error occurred)\n  - script_file: saved script path if applicable\n\nFor example, to execute `kubectl get pod -n default --kubeconfig kubeconfig.yaml`,\nTool Input should be the following:\n{"args": "get pod -n default --kubeconfig kubeconfig.yaml", "output_file": "", "return_output": "True", "script_file": ""}\n\nHint:\n- If you need to get all pods in all namespaces, you can do it by `kubectl get pods --all-namespaces --kubeconfig <kubeconfig_path> -o json`\n',
    #             "parameters": {
    #                 "type": "object",
    #                 "properties": {
    #                     "args": {
    #                         "type": "str",
    #                         "description": "command arguments after `kubectl`. `--kubeconfig` should be specified here. Multiple commands with `;` or `&&` is not allowed. Using pipe `|` for jq are not allowed too. Just save the entire JSON if you want.",
    #                     },
    #                     "output_file": {
    #                         "type": "str",
    #                         "description": "The filepath to save the result. If empty string, not save anything",
    #                         "default": "",
    #                     },
    #                     "return_output": {
    #                         "type": "str",
    #                         "description": 'A boolean string. Set this to "True" if you want to get the command output',
    #                         "default": "False",
    #                     },
    #                     "script_file": {
    #                         "type": "str",
    #                         "description": "A filepath. If provided, save the kubectl command as a script at the specified file.",
    #                         "default": "",
    #                     },
    #                 },
    #                 "required": ["args"],
    #             },
    #         },
    #     },
    # ]

    conversation_history = [
        {
            "role": "system",
            "content": "<|start_header_id|>system<|end_header_id|>\nYou are a helpful assistant with access to the following function calls. Your task is to produce a sequence of function calls necessary to generate response to the user utterance. Use the following function calls as required. Do not make up an original tool not listed below. All function arguments must be defined under `arguments` attribute.\n<|eot_id|>\n",
        },
        {
            "role": "system",
            "content": '<|start_header_id|>user<|end_header_id|>\nWhat profession does Nicholas Ray and Elia Kazan have in common?\n<|eot_id|>\n<|start_header_id|>assistant<|end_header_id|>\nTho: I need to search Nicholas Ray and Elia Kazan, find their professions, then find the profession they have in common.\nAct: \n[{"name": "Search", "arguments": {"topic": "Nicholas Ray"}}]\nObs: Nicholas Ray (born Raymond Nicholas Kienzle Jr., August 7, 1911 - June 16, 1979) was an American film director, screenwriter, and actor best known for the 1955 film Rebel Without a Cause.\nTho: Professions of Nicholas Ray are director, screenwriter, and actor. I need to search Elia Kazan next and find his professions.\nAct: \n[{"name": "Search", "arguments": {"topic": "Elia Kazan"}}]\nObs: Elia Kazan was an American film and theatre director, producer, screenwriter and actor.\nTho: Professions of Elia Kazan are director, producer, screenwriter, and actor. So profession Nicholas Ray and Elia Kazan have in common is director, screenwriter, and actor.\nAct: \n[{"name": "Finish"}]\n<|eot_id|>\n',
        },
        {
            "role": "user",
            "content": '<|start_header_id|>system<|end_header_id|>\nThe above dialog is an example flow to solve the original question.\nTho (thought) comes first to describe your thought in a natural language text, then Act (action) in JSON to execute functions, and Obs (observation) is a feedback of the action and then the next thought is a reasoning of the next action.\nEach "Tho" must be a reasoning description to come up with the next action. This must not be an action string because it may cause confusion of the action history.\nEach "Act" must be a list object like the following\n  [{"name": "<FUNC_NAME>", "arguments": {"<KEY>": "<VALUE>"}}]\nWhen you got an answer, you must return an action [{"name": "Finish"}]\nWhen you see errors and you can\'t fix them, previous personas before you might be cause. To get back to them, call `Error` function with some error report like `[{"name": "Error", "arguments": {"error": "<ERROR DETAILS>"}}]`\nThe function names in the dialog are just examples, you must use functions you have.\nYou must simplify your answer as much as possible.\nLong explanation is not needed.\nEven when you need to do multiple actions, generate just the very next 1 action.\nWhen you are seeing the same error again and again, please forget the details and remind your original goal.\n<|eot_id|>\n',
        },
        {
            "role": "user",
            "content": '<|start_header_id|>system<|end_header_id|>\nYou are requested to achieve the given `Goal`. When an `Original Goal` is given, it contains requests to other people and tools you can use are not always sufficient to achieve this original goal. In such case, you can quit our work. Then next person will continue the task.\nYour thought is not directly transfered to actions, so you must transfer them to actions especially about errors.\nThe action you thought must be a SINGLE LINE JSON and do not include any explanation for it in Act: step.\nWhen you perform policy evaluation and the result was false, which means the compliance requirement is not satisfied, just report them and do not remediate it.\nWhen an action has an argument `sentence`, it is an input text for LLM service to generate something (e.g. Playbook). You have to specify details here as much as possible.\nWhen you want to use newline in the sentence arguemnts, you have to escape it like {"sentence": "this is the first line.\\\\nthis is the second line."} and escape all quoation in the arguments like {"sentence": "escape quotes like \\"this\\" when you use quotes"}\nSpecify `script_file` as "script.sh" when you want to use RunKubectl to get `collected_data.json`.\nWhen the goal says `Minimize something`, it means no instances are allowed.\nWhen the goal says `role` for Kubernetes, it means both RoleBinding and ClusterRoleBinding should be in scope.\nWhen the goal mentions some extra conditions like `exclude xxxx namespace` and `apply this policy only to resources labeled as yyyy=zzzz`, then these conditions must be included in `sentence` of GenerateKyvernoTool\nAfter deploying a Kyverno policy, do not validate it by deploying other resources. Just finish.\nAfter generating a Playbook, you have to run it with RunPlaybook.\n  When it is required to get some existing Kyverno policies, you can do `kubectl get clusterpolicies --kubeconfig /path/to/kubeconfig`.\nWhen getting names of exisintg kyverno clusterpolicies, you should not specify "-o" option. Just to do kubectl get without name and -o\n\n<|eot_id|>\n',
        },
        {
            "role": "system",
            "content": "<|start_header_id|>system<|end_header_id|>\nYour Goal:\n```\nGenerate a Kyverno policy to check if the cluster-admin role is only used where required.\nSave the generated policy to policy.yaml in the workdir.\nDeploy the generated policy to the Kubernetes cluster with kubeconfig /tmp/agent/20250122154450/kubeconfig.yaml.\n\n```\n\nOriginal Goal (NOTE: This is NOT your goal; Do not do everything here):\n```\nI would like to check if the following condition is satisfiled, given a Kubernetes cluster with `kubeconfig.yaml`\n    Ensure that the cluster-admin role is only used where required.\n\nTo check the condition, do the following steps.\n- deploy a Kyverno policy to the cluster\n- chcek if the policy is correctly deployed.\n\n\nIf deploying the policy failed and if you can fix the issue, you will do it and try deploying again.\nOnce you get a final answer, you can quit the work.\n\nThe cluster's kubeconfig is at `/tmp/agent/20250122154450/kubeconfig.yaml`.\nYou can use `/tmp/agent/20250122154450/` as your workdir.\n\n```\n\n\nSteps Already Done and Results:\n```yaml\n- input:\n    goal: |\n      Generate a Kyverno policy to check if the cluster-admin role is only used where required.\n      Save the generated policy to policy.yaml in the workdir.\n      Deploy the generated policy to the Kubernetes cluster with kubeconfig /tmp/agent/20250122154450/kubeconfig.yaml.\n    kubeconfig: /tmp/agent/20250122154450/kubeconfig.yaml\n    workdir: /tmp/agent/20250122154450/\n  node: kyverno\n  output:\n    deployed_resource:\n      kind: ClusterPolicy\n      name: restrict-cluster-admin\n    path_to_generated_kyverno_policy: /tmp/agent/20250122154450/policy.yaml\n- input:\n    goal: |\n      Get the deployed Kyverno policy from the cluster with kubeconfig /tmp/agent/20250122154450/kubeconfig.yaml.\n      Save the result to deployed_policy.json.\n    kubeconfig: /tmp/agent/20250122154450/kubeconfig.yaml\n    workdir: /tmp/agent/20250122154450/\n  node: kubernetes\n  output:\n    error: error message\n\n```\n\n<|eot_id|>\n",
        },
        {
            "role": "system",
            "content": "<|start_header_id|>system<|end_header_id|>\n[{'type': 'function', 'function': {'name': 'GenerateKyvernoTool', 'description': 'The tool to generate a Kyverno policy. This tool returns the generated Kyverno policy. This can be used for updating existing Kyverno policy.\\n', 'parameters': {'type': 'object', 'properties': {'sentence': {'type': 'str', 'description': 'A comprehensive description to request Kyverno policy generation.\\nThis must be containing any level of details about the Kyverno policy to be generated.\\nIf you got any errors especially about syntax when you invoked this function previously, mention it here for improving the generation result this time.\\nFor example, when you got an error like `.spec.rules[0].match.any[0].selector: field not declared in schema`, add the following to the sentence: `previous trial failed because .spec.rules[0].match.any[0].selector is not available field for Kyverno policy`\\n'}, 'policy_file': {'type': 'str', 'description': 'filepath for the Kyverno policy to be saved.'}, 'current_policy_file': {'type': 'str', 'description': 'filepath of the current Kyverno policy to be updated. Only needed when updating an existing policy', 'default': ''}}, 'required': ['sentence', 'policy_file']}}}, {'type': 'function', 'function': {'name': 'RunKubectlTool', 'description': 'The tool to execute a kubectl command.\\nThis tool returns the following:\\n  - return_code: if 0, the command was successful, otherwise, failure.\\n  - stdout: standard output of the command (only when `return_output` is True)\\n  - stderr: standard error of the command (only when error occurred)\\n  - script_file: saved script path if applicable\\n\\nFor example, to execute `kubectl get pod -n default --kubeconfig kubeconfig.yaml`,\\nTool Input should be the following:\\n{\"args\": \"get pod -n default --kubeconfig kubeconfig.yaml\", \"output_file\": \"\", \"return_output\": \"True\", \"script_file\": \"\"}\\n\\nHint:\\n- If you need to get all pods in all namespaces, you can do it by `kubectl get pods --all-namespaces --kubeconfig <kubeconfig_path> -o json`\\n', 'parameters': {'type': 'object', 'properties': {'args': {'type': 'str', 'description': 'command arguments after `kubectl`. `--kubeconfig` should be specified here. Multiple commands with `;` or `&&` is not allowed. Using pipe `|` for jq are not allowed too. Just save the entire JSON if you want.'}, 'output_file': {'type': 'str', 'description': 'The filepath to save the result. If empty string, not save anything', 'default': ''}, 'return_output': {'type': 'str', 'description': 'A boolean string. Set this to \"True\" if you want to get the command output', 'default': False}, 'script_file': {'type': 'str', 'description': 'A filepath. If provided, save the kubectl command as a script at the specified file.', 'default': ''}}, 'required': ['args']}}}]\n<|eot_id|>\n",
        },
        {
            "role": "assistant",
            "content": "<|start_header_id|>assistant<|end_header_id|>Tho: ",
        },
        {
            "role": "assistant",
            "content": " To achieve the given goal, I need to generate a Kyverno policy to check if the cluster-admin role is only used where required, save it to policy.yaml, and then deploy it to the Kubernetes cluster. First, I will generate the Kyverno policy using the GenerateKyvernoTool function.\nAct:",
        },
        {
            "role": "assistant",
            "content": "<|start_header_id|>assistant<|end_header_id|>Act: (Please return only a JSON string)\n",
        },
        {
            "role": "assistant",
            "content": '[{"name": "GenerateKyvernoTool", "arguments": {"sentence": "Generate a Kyverno policy to check if the cluster-admin role is only used where required. The policy should validate ClusterRoleBindings and check if the role is bound to a user or a service account.", "policy_file": "policy.yaml"}}]',
        },
        {
            "role": "user",
            "content": "[{'name': 'GenerateKyvernoTool', 'arguments': {'sentence': 'Generate a Kyverno policy to check if the cluster-admin role is only used where required. The policy should validate ClusterRoleBindings and check if the role is bound to a user or a service account.', 'policy_file': 'policy.yaml'}}]",
        },
        {
            "role": "assistant",
            "content": "<|start_header_id|>assistant<|end_header_id|>Obs: <|eot_id|>",
        },
        {
            "role": "user",
            "content": 'The generated policy is below:\n```yaml\n\napiVersion: kyverno.io/v1\nkind: ClusterPolicy\nmetadata:\n  name: restrict-cluster-admin-role\nspec:\n  rules:\n  - name: validate-cluster-admin-binding\n    match:\n      any:\n      - resources:\n          kinds:\n          - ClusterRoleBinding\n    validate:\n      message: "ClusterRoleBinding for cluster-admin role should be reviewed."\n      pattern:\n        roleRef:\n          name: "cluster-admin"\n          kind: "ClusterRole"\n        subjects:\n        - kind: "ServiceAccount"\n\n```\n\nThis policy file has been saved at /tmp/agent/20250122154450/policy.yaml.\n',
        },
    ]

    # Extract tool calls to reflect
    # raw_tool_calls = extract_tool_calls_to_reflect(conversation_history)
    #
    # print("Extracted tool calls:")
    # print(json.dumps(raw_tool_calls, indent=2))

    # Convert them to OpenAI tool_call objects
    # openai_tool_calls = convert_tool_calls_to_openai_format(raw_tool_calls)
    #
    # print("Converted OpenAI tool calls:")
    # for call in openai_tool_calls:
    #     print(f"{call.model_dump_json(indent=2)}")

    # Call the main reflection function
    reflections = asyncio.run(reflect_ciso_agent_conversation(conversation_history))

    print(reflections)
