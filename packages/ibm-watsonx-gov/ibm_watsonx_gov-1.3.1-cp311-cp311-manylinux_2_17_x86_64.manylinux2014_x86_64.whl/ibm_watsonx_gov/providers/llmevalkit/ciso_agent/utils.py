import copy
import re

_JSON_TYPE_ALIASES = {
    "str": "string",
    "string": "string",
    "int": "integer",
    "integer": "integer",
    "float": "number",
    "double": "number",
    "number": "number",
    "bool": "boolean",
    "boolean": "boolean",
    "dict": "object",
    "object": "object",
    "list": "array",
    "array": "array",
    "null": "null",
}

_ALLOWED_JSON_TYPES = set(_JSON_TYPE_ALIASES.values())

_NAME_RE = re.compile(r"^[A-Za-z0-9_]{1,64}$")

def _sanitize_name(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_]", "_", str(name))
    if not name:
        name = "tool"
    if name[0].isdigit():
        name = f"fn_{name}"
    return name[:64]

def _normalize_type(t):
    if isinstance(t, list):
        fixed = list({ _JSON_TYPE_ALIASES.get(x, x) for x in t })
        return [x for x in fixed if x in _ALLOWED_JSON_TYPES] or ["string"]
    if isinstance(t, str):
        return _JSON_TYPE_ALIASES.get(t, t) if _JSON_TYPE_ALIASES.get(t, t) in _ALLOWED_JSON_TYPES else "string"
    return "string"

def _clean_description(desc):
    if desc is None:
        return None
    s = str(desc).strip()
    # collapse excessive whitespace
    s = re.sub(r"\s+\n", "\n", s)
    s = re.sub(r"\n\s+", "\n", s)
    return s

def _fix_schema(schema, notes, path="parameters"):
    """
    Recursively fix a JSON Schema-ish dict in place.
    """
    if not isinstance(schema, dict):
        notes.append(f"{path}: non-dict schema replaced with empty object")
        return {"type": "object"}

    out = dict(schema)

    # type
    if "type" in out:
        out["type"] = _normalize_type(out["type"])
    # For top-level parameters or any object-like node, ensure properties shape if object
    if out.get("type") == "object":
        props = out.get("properties", {})
        if not isinstance(props, dict):
            notes.append(f"{path}.properties: not a dict, replaced with empty dict")
            props = {}
        fixed_props = {}
        for k, v in props.items():
            fixed_props[k] = _fix_schema(v if isinstance(v, dict) else {"type": v}, notes, f"{path}.properties.{k}")
        out["properties"] = fixed_props

        # required: only keep keys that exist in properties and are strings
        if "required" in out:
            req = out["required"]
            if isinstance(req, list):
                req_clean = [r for r in req if isinstance(r, str) and r in out["properties"]]
                if req_clean != req:
                    notes.append(f"{path}.required: pruned invalid entries")
                out["required"] = req_clean
            else:
                notes.append(f"{path}.required: not a list, removed")
                out.pop("required", None)

        # additionalProperties is fine as is if present
    elif out.get("type") == "array":
        # ensure items
        items = out.get("items")
        if not isinstance(items, dict):
            notes.append(f"{path}.items: missing or invalid, set to permissive object")
            out["items"] = {}
        else:
            out["items"] = _fix_schema(items, notes, f"{path}.items")

    # description
    if "description" in out:
        cleaned = _clean_description(out.get("description"))
        if cleaned != out.get("description"):
            notes.append(f"{path}.description: normalized whitespace")
        out["description"] = cleaned

    # normalize leaf shorthand like {"type": "str"} already handled
    return out

def to_valid_openai_tool(spec: dict):
    """
    Convert a possibly-invalid tool specification dict into a valid
    OpenAI tool spec dict. Returns (converted_dict, notes).
    """
    notes = []
    if not isinstance(spec, dict):
        raise TypeError("spec must be a dict")

    spec = copy.deepcopy(spec)

    # Unwrap or detect shape
    if spec.get("type") == "function" and isinstance(spec.get("function"), dict):
        fn = spec["function"]
    else:
        # Maybe user passed just the function block
        fn = spec

    name = fn.get("name")
    if not name:
        notes.append("function.name missing, set to 'tool'")
        name = "tool"
    new_name = _sanitize_name(name)
    if new_name != name:
        notes.append(f"function.name sanitized to '{new_name}'")
    name = new_name

    description = fn.get("description")
    description = _clean_description(description) if description is not None else ""
    if not isinstance(description, str):
        notes.append("function.description not a string, coerced")
        description = str(description)

    # Parameters
    raw_params = fn.get("parameters")
    if not isinstance(raw_params, dict):
        if raw_params is not None:
            notes.append("function.parameters not a dict, replaced with empty object schema")
        raw_params = {}
    # Ensure object type
    if raw_params.get("type") != "object":
        raw_params["type"] = "object"
        raw_params.setdefault("properties", {})
    parameters = _fix_schema(raw_params, notes, "parameters")

    # Final envelope
    out = {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        }
    }

    return out, notes

# --------- Example usage ---------
if __name__ == "__main__":
    messy = {
        "type": "function",
        "function": {
            "name": "GenerateKyvernoTool!",
            "description": "The tool to generate a Kyverno policy.\n",
            "parameters": {
                "type": "object",
                "properties": {
                    "sentence": {"type": "str", "description": "...\n"},
                    "policy_file": {"type": "str", "description": "filepath."},
                    "current_policy_file": {"type": "str", "description": "optional", "default": ""}
                },
                "required": ["sentence", "policy_file", "nonexistent_param"]
            }
        }
    }

    fixed, notes = to_valid_openai_tool(messy)
    print(fixed)
    print("Notes:")
    for n in notes:
        print("-", n)
