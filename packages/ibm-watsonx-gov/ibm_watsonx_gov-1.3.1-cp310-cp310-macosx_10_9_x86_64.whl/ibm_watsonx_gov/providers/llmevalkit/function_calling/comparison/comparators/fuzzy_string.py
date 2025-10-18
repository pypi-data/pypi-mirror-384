from typing import Any, Dict, Optional
import logging

from .base import BaseComparator
from ..types import ParameterComparisonResult, ComparisonStrategy, ParameterStatus
from ..utils import calculate_string_similarity, deep_compare_objects

logger = logging.getLogger(__name__)


class FuzzyStringComparator(BaseComparator):
    """String similarity-based comparator using fuzzy matching."""

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

        # Handle None values
        if predicted_value is None and ground_truth_value is None:
            return ParameterComparisonResult(
                parameter_name=param_name,
                predicted_value=predicted_value,
                ground_truth_value=ground_truth_value,
                predicted_resolved_value=predicted_value,
                ground_truth_resolved_value=ground_truth_value,
                parameter_status=param_status,
                comparison_strategy=ComparisonStrategy.FUZZY_STRING,
                score=1.0,
                explanation="Both values are None/missing",
                is_match=True,
                confidence=1.0,
            )

        if predicted_value is None or ground_truth_value is None:
            return ParameterComparisonResult(
                parameter_name=param_name,
                predicted_value=predicted_value,
                ground_truth_value=ground_truth_value,
                predicted_resolved_value=predicted_value,
                ground_truth_resolved_value=ground_truth_value,
                parameter_status=param_status,
                comparison_strategy=ComparisonStrategy.FUZZY_STRING,
                score=0.0,
                explanation=f"One value is missing: predicted={predicted_value}, ground_truth={ground_truth_value}",
                is_match=False,
                confidence=1.0,
                error_type="missing_value",
            )

        # Use deep comparison for similarity
        score = deep_compare_objects(
            predicted_value, ground_truth_value, tolerance=self.config.numeric_tolerance
        )

        # Determine if it's a match based on threshold
        is_match = score >= self.config.string_similarity_threshold

        # Generate explanation
        if score == 1.0:
            explanation = f"Exact match: {predicted_value}"
        elif score >= 0.9:
            explanation = f"Very high similarity (score: {score:.2f}): {predicted_value} ≈ {ground_truth_value}"
        elif score >= self.config.string_similarity_threshold:
            explanation = f"Good similarity (score: {score:.2f}): {predicted_value} ~ {ground_truth_value}"
        else:
            explanation = f"Low similarity (score: {score:.2f}): {predicted_value} != {ground_truth_value}"

        # Confidence based on score clarity
        confidence = (
            min(1.0, score + 0.1) if is_match else min(1.0, (1.0 - score) + 0.1)
        )

        return ParameterComparisonResult(
            parameter_name=param_name,
            predicted_value=predicted_value,
            ground_truth_value=ground_truth_value,
            predicted_resolved_value=predicted_value,
            ground_truth_resolved_value=ground_truth_value,
            parameter_status=param_status,
            comparison_strategy=ComparisonStrategy.FUZZY_STRING,
            score=score,
            explanation=explanation,
            is_match=is_match,
            confidence=confidence,
            error_type="similarity_mismatch" if not is_match else None,
        )

    def compare_function_name(
        self,
        predicted_name: str,
        ground_truth_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Fuzzy function name comparison."""
        return calculate_string_similarity(predicted_name, ground_truth_name)
