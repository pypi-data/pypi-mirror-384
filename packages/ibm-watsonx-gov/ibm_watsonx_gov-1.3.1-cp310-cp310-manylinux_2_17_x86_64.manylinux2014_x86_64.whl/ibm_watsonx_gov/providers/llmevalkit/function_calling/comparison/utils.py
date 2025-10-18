"""
Utility functions for tool call comparison.
"""

import json
import re
from typing import Any, Dict, List, Optional, Union
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


def normalize_json_string(value: str) -> Union[Dict, List, str]:
    """Attempt to parse JSON string, return original if parsing fails."""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def calculate_string_similarity(str1: str, str2: str) -> float:
    """Calculate similarity between two strings using difflib."""
    if str1 == str2:
        return 1.0

    # Normalize strings for comparison
    norm_str1 = str1.lower().strip()
    norm_str2 = str2.lower().strip()

    if norm_str1 == norm_str2:
        return 0.95  # Close match with case/whitespace differences

    # Use sequence matcher for fuzzy matching
    matcher = SequenceMatcher(None, norm_str1, norm_str2)
    return matcher.ratio()


def extract_numeric_value(value: Any) -> Optional[float]:
    """Extract numeric value from various formats."""
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        # Try to extract number from string
        numeric_match = re.search(r"-?\d+\.?\d*", value.strip())
        if numeric_match:
            try:
                return float(numeric_match.group())
            except ValueError:
                pass

    return None


def is_semantically_equivalent_boolean(val1: Any, val2: Any) -> bool:
    """Check if two values represent the same boolean state."""
    # Define truthy and falsy values
    truthy_values = {
        True,
        "true",
        "True",
        "TRUE",
        "yes",
        "Yes",
        "YES",
        "1",
        1,
        "on",
        "On",
        "ON",
    }
    falsy_values = {
        False,
        "false",
        "False",
        "FALSE",
        "no",
        "No",
        "NO",
        "0",
        0,
        "off",
        "Off",
        "OFF",
    }

    val1_is_truthy = val1 in truthy_values
    val2_is_truthy = val2 in truthy_values
    val1_is_falsy = val1 in falsy_values
    val2_is_falsy = val2 in falsy_values

    # Both are truthy or both are falsy
    return (val1_is_truthy and val2_is_truthy) or (val1_is_falsy and val2_is_falsy)


def compare_numeric_with_tolerance(
    val1: Any, val2: Any, tolerance: float = 0.01
) -> bool:
    """Compare numeric values with tolerance."""
    num1 = extract_numeric_value(val1)
    num2 = extract_numeric_value(val2)

    if num1 is None or num2 is None:
        return False

    return abs(num1 - num2) <= tolerance


def safe_json_dumps(obj: Any) -> str:
    """Safely convert object to JSON string."""
    try:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(obj)


def deep_compare_objects(obj1: Any, obj2: Any, tolerance: float = 0.01) -> float:
    """
    Deep comparison of objects with similarity score.

    Returns:
        float: Similarity score between 0.0 and 1.0
    """
    # Exact match
    if obj1 == obj2:
        return 1.0

    # Type compatibility checks
    if type(obj1) != type(obj2):
        # Try semantic equivalence for common type mismatches
        if is_semantically_equivalent_boolean(obj1, obj2):
            return 0.95

        if compare_numeric_with_tolerance(obj1, obj2, tolerance):
            return 0.9

        # String comparison if one is string
        if isinstance(obj1, str) or isinstance(obj2, str):
            return calculate_string_similarity(str(obj1), str(obj2))

        return 0.0

    # Same type comparisons
    if isinstance(obj1, str):
        return calculate_string_similarity(obj1, obj2)

    elif isinstance(obj1, (int, float)):
        if compare_numeric_with_tolerance(obj1, obj2, tolerance):
            return 1.0
        else:
            # Partial score based on relative difference
            try:
                max_val = max(abs(obj1), abs(obj2), 1)  # Avoid division by zero
                diff_ratio = abs(obj1 - obj2) / max_val
                return max(0.0, 1.0 - diff_ratio)
            except (TypeError, ZeroDivisionError):
                return 0.0

    elif isinstance(obj1, bool):
        return 1.0 if obj1 == obj2 else 0.0

    elif isinstance(obj1, list):
        return _compare_lists(obj1, obj2, tolerance)

    elif isinstance(obj1, dict):
        return _compare_dicts(obj1, obj2, tolerance)

    # For other types, fall back to string comparison
    return calculate_string_similarity(str(obj1), str(obj2))


def _compare_lists(list1: List, list2: List, tolerance: float) -> float:
    """Compare two lists with similarity scoring."""
    if len(list1) == 0 and len(list2) == 0:
        return 1.0

    if len(list1) == 0 or len(list2) == 0:
        return 0.0

    # If same length, compare element by element
    if len(list1) == len(list2):
        scores = []
        for item1, item2 in zip(list1, list2):
            scores.append(deep_compare_objects(item1, item2, tolerance))
        return sum(scores) / len(scores) if scores else 0.0

    # Different lengths - find best matches
    max_len = max(len(list1), len(list2))
    min_len = min(len(list1), len(list2))

    # Calculate similarity for overlapping elements
    scores = []
    for i in range(min_len):
        scores.append(deep_compare_objects(list1[i], list2[i], tolerance))

    avg_score = sum(scores) / len(scores) if scores else 0.0

    # Apply penalty for length difference
    length_penalty = min_len / max_len

    return avg_score * length_penalty


def _compare_dicts(dict1: Dict, dict2: Dict, tolerance: float) -> float:
    """Compare two dictionaries with similarity scoring."""
    if not dict1 and not dict2:
        return 1.0

    if not dict1 or not dict2:
        return 0.0

    all_keys = set(dict1.keys()) | set(dict2.keys())
    common_keys = set(dict1.keys()) & set(dict2.keys())

    if not all_keys:
        return 1.0

    # Score for common keys
    scores = []
    for key in common_keys:
        scores.append(deep_compare_objects(dict1[key], dict2[key], tolerance))

    # Average score for common keys
    common_score = sum(scores) / len(scores) if scores else 0.0

    # Penalty for missing keys
    key_coverage = len(common_keys) / len(all_keys)

    return common_score * key_coverage


def sanitize_parameter_name(name: str) -> str:
    """Sanitize parameter name for consistent comparison."""
    # Remove common prefixes/suffixes that might be added by different systems
    name = re.sub(r"^(param_|parameter_|arg_|argument_)", "", name.lower())
    name = re.sub(r"(_param|_parameter|_arg|_argument)$", "", name)

    # Normalize common variations
    replacements = {
        "id": "identifier",
        "num": "number",
        "qty": "quantity",
        "amt": "amount",
        "desc": "description",
    }

    for old, new in replacements.items():
        if name == old:
            return new

    return name


def validate_tool_call_structure(tool_call: Dict[str, Any]) -> List[str]:
    """
    Validate tool call structure and return list of issues.

    Returns:
        List of validation error messages
    """
    issues = []

    if not isinstance(tool_call, dict):
        issues.append("Tool call must be a dictionary")
        return issues

    # Check for required top-level structure
    if "function" not in tool_call:
        issues.append("Missing 'function' key in tool call")
        return issues

    function_data = tool_call["function"]
    if not isinstance(function_data, dict):
        issues.append("'function' value must be a dictionary")
        return issues

    # Check function name
    if "name" not in function_data:
        issues.append("Missing 'name' in function data")
    elif not isinstance(function_data["name"], str):
        issues.append("Function 'name' must be a string")
    elif not function_data["name"].strip():
        issues.append("Function 'name' cannot be empty")

    # Check arguments
    if "arguments" in function_data:
        args = function_data["arguments"]
        if isinstance(args, str):
            # Try to parse JSON string
            try:
                json.loads(args)
            except json.JSONDecodeError:
                issues.append("Function 'arguments' string is not valid JSON")
        elif not isinstance(args, dict):
            issues.append("Function 'arguments' must be a dictionary or JSON string")

    return issues
