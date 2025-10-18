import asyncio
import json
import re
from typing import Dict, List, Any

from llmevalkit.ciso_agent.main import create_reflection_result_summary, reflect_ciso_agent_conversation

_HEADER_RE = re.compile(r"<\|start_header_id\|>.*?<\|end_header_id\|>\n?", re.DOTALL)
_CONTROL_TOKENS = [
    "<|eot_id|>",
    "<|python_end|>",
    "<|eom|>",
]

def _clean_content(text: str) -> str:
    if not text:
        return ""
    # Keep only the part before the first end of turn marker, if present
    parts = text.split("<|eot_id|>", 1)
    text = parts[0]
    # Remove any residual header blocks like <|start_header_id|>role<|end_header_id|>
    text = _HEADER_RE.sub("", text)
    # Remove stray control tokens that sometimes appear inline
    for tok in _CONTROL_TOKENS:
        text = text.replace(tok, "")
    return text.strip()

def convert_langtrace_to_openai_messages(
    data: Dict[str, Any],
    key_prefix: str = "gen_ai.prompt",
    merge_consecutive: bool = True,
) -> List[Dict[str, str]]:
    """
    Convert a flat dict that contains keys like:
      gen_ai.prompt.0.role, gen_ai.prompt.0.content, ...
    into an OpenAI messages list:
      [{"role": "system", "content": "..."}, ...]

    Args:
        data: source dictionary
        key_prefix: base prefix for prompt entries
        merge_consecutive: if True, merge adjacent messages that share the same role

    Returns:
        List of messages suitable for OpenAI chat completions
    """
    # Collect all indices N for which a role exists
    indices = []
    prefix_dot = f"{key_prefix}."
    role_suffix = ".role"
    for k in data.keys():
        if k.startswith(prefix_dot) and k.endswith(role_suffix):
            try:
                n = int(k[len(prefix_dot):-len(role_suffix)])
                indices.append(n)
            except ValueError:
                continue
    indices.sort()

    # Build raw messages
    messages: List[Dict[str, str]] = []
    for i in indices:
        role = data.get(f"{key_prefix}.{i}.role")
        # Skip entries without a valid role
        if not role:
            continue
        content = data.get(f"{key_prefix}.{i}.content", "") or ""
        content = _clean_content(content)

        # Some traces split a single assistant turn across multiple numbered entries
        if merge_consecutive and messages and messages[-1]["role"] == role:
            # Append with a single newline separator
            joined = (messages[-1]["content"] + ("\n" if messages[-1]["content"] and content else "") + content).strip()
            messages[-1]["content"] = joined
        else:
            messages.append({"role": role, "content": content})

    # Optional final cleanup, remove empty messages if any
    # messages = [m for m in messages if m.get("content", "") != "" or m.get("role") == "system"]

    return messages

# Example:
# msgs = convert_langtrace_to_openai_messages(your_dict)
# print(msgs)
if __name__ == "__main__":
    log_path = "/Users/korenlazar/workspace/LLMEvalKit/tests/ciso_agent/agent_analytics_with_manually_modified_wrong_tool_call.log"
    with open(log_path, "r") as f:
        log_json = json.load(f)
    
    log_attributes = log_json.get("attributes", {})
    conversation_history = convert_langtrace_to_openai_messages(log_attributes, merge_consecutive=False)
    
    reflections = asyncio.run(reflect_ciso_agent_conversation(conversation_history))

    with open("reflections.json", "w") as f:
        for reflection_output in reflections:
            json.dump(reflection_output.model_dump(), f)
            f.write("\n")

    # with open("reflections.json", "r") as f:
    #     reflections = [json.loads(line) for line in f]

    reflection_jsons = [reflection.model_dump() if hasattr(reflection, "model_dump") else reflection for reflection in reflections]

    with open("reflections_summary.json", "w") as f:
        for reflection_output in reflection_jsons:
            json.dump(create_reflection_result_summary(reflection_output), f)
            f.write("\n")

    print(reflections)
