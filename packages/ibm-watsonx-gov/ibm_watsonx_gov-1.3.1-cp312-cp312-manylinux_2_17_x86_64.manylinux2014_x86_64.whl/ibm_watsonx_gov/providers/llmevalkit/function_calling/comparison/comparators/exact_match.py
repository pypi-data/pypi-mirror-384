from typing import Any, Dict, Optional
import logging

from .base import BaseComparator
from ..types import ParameterComparisonResult, ComparisonStrategy, ParameterStatus

logger = logging.getLogger(__name__)


class ExactMatchComparator(BaseComparator):
    """Enhanced exact value matching comparator with proper default handling."""

    def compare_parameter(
        self,
        param_name: str,
        predicted_value: Any,
        ground_truth_value: Any,
        context: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
    ) -> ParameterComparisonResult:

        context = context or {}
        param_def = context.get("parameter_definition", {})
        param_status = context.get("parameter_status", ParameterStatus.BOTH_PRESENT)

        # Normalize values if configured
        param_type = param_def.get("type", "string") if param_def else "string"

        if self.config.normalize_types:
            predicted_value = self._normalize_value(predicted_value, param_type)
            ground_truth_value = self._normalize_value(ground_truth_value, param_type)

        # Handle None values with context awareness
        if predicted_value is None and ground_truth_value is None:
            return ParameterComparisonResult(
                parameter_name=param_name,
                predicted_value=predicted_value,
                ground_truth_value=ground_truth_value,
                predicted_resolved_value=predicted_value,
                ground_truth_resolved_value=ground_truth_value,
                parameter_status=param_status,
                comparison_strategy=ComparisonStrategy.EXACT_MATCH,
                score=1.0,
                explanation="Both values are None/missing",
                is_match=True,
                confidence=1.0,
            )

        if predicted_value is None or ground_truth_value is None:
            # Check if this is acceptable based on parameter requirements
            is_required = param_def.get("required", False) if param_def else False
            has_default = param_def.get("default") is not None if param_def else False

            if not is_required or has_default:
                # Missing optional parameter or parameter with default - partial penalty
                score = 0.7  # Partial score for missing non-critical parameter
                explanation = f"One value is missing (predicted={predicted_value}, ground_truth={ground_truth_value}), but parameter is {'optional' if not is_required else 'has default'}"
                error_type = "missing_optional_value"
            else:
                # Missing required parameter - major penalty
                score = 0.1
                explanation = f"Missing required parameter: predicted={predicted_value}, ground_truth={ground_truth_value}"
                error_type = "missing_required_value"

            return ParameterComparisonResult(
                parameter_name=param_name,
                predicted_value=predicted_value,
                ground_truth_value=ground_truth_value,
                predicted_resolved_value=predicted_value,
                ground_truth_resolved_value=ground_truth_value,
                parameter_status=param_status,
                comparison_strategy=ComparisonStrategy.EXACT_MATCH,
                score=score,
                explanation=explanation,
                is_match=False,
                confidence=1.0,
                error_type=error_type,
            )

        # Handle special parameter status cases
        if param_status in [
            ParameterStatus.BOTH_DEFAULT,
            ParameterStatus.PRED_DEFAULT,
            ParameterStatus.GT_DEFAULT,
        ]:
            # When comparing values that include defaults, be more lenient
            if predicted_value == ground_truth_value:
                explanation = f"Values match exactly (including default resolution): {predicted_value}"
                score = 1.0
                is_match = True
            else:
                explanation = f"Values differ after default resolution: {predicted_value} != {ground_truth_value}"
                # Less severe penalty for default-related mismatches
                score = 0.5
                is_match = False
        else:
            # Standard exact comparison
            is_match = predicted_value == ground_truth_value
            score = 1.0 if is_match else 0.0

            if is_match:
                explanation = f"Exact match: {predicted_value}"
            else:
                explanation = (
                    f"Values differ: {predicted_value} != {ground_truth_value}"
                )

                # Provide more specific error classification
                if type(predicted_value) != type(ground_truth_value):
                    explanation += f" (type mismatch: {type(predicted_value).__name__} vs {type(ground_truth_value).__name__})"

        return ParameterComparisonResult(
            parameter_name=param_name,
            predicted_value=predicted_value,
            ground_truth_value=ground_truth_value,
            predicted_resolved_value=predicted_value,
            ground_truth_resolved_value=ground_truth_value,
            parameter_status=param_status,
            comparison_strategy=ComparisonStrategy.EXACT_MATCH,
            score=score,
            explanation=explanation,
            is_match=is_match,
            confidence=1.0,
            error_type="value_mismatch" if not is_match and score == 0.0 else None,
        )

    def compare_function_name(
        self,
        predicted_name: str,
        ground_truth_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Exact function name comparison."""
        return 1.0 if predicted_name == ground_truth_name else 0.0
