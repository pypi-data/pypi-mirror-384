from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import json
import logging

from ..types import (
    ParameterComparisonResult,
    ToolCallComparisonResult,
    ComparisonConfig,
    ParameterStatus,
    ToolSpecFunction,
    ToolSpecParameter,
)

logger = logging.getLogger(__name__)


class BaseComparator(ABC):
    """Abstract base class for tool call comparison strategies."""

    def __init__(self, config: ComparisonConfig):
        self.config = config

    @abstractmethod
    def compare_parameter(
        self,
        param_name: str,
        predicted_value: Any,
        ground_truth_value: Any,
        context: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
    ) -> ParameterComparisonResult:
        """Compare a single parameter between predicted and ground truth."""
        pass

    @abstractmethod
    def compare_function_name(
        self,
        predicted_name: str,
        ground_truth_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Compare function names and return similarity score."""
        pass

    def _extract_tool_spec(
        self, function_name: str, tool_specs: Optional[List[Dict[str, Any]]]
    ) -> Optional[ToolSpecFunction]:
        """Extract tool specification for the given function."""
        if not tool_specs:
            return None

        for spec in tool_specs:
            if spec.get("function", {}).get("name") == function_name:
                return ToolSpecFunction.from_openai_spec(spec)

        return None

    def _resolve_parameters_with_defaults(
        self, provided_params: Dict[str, Any], tool_spec: Optional[ToolSpecFunction]
    ) -> Dict[str, Any]:
        """Resolve parameters by applying defaults from tool specification."""
        resolved = provided_params.copy()

        if tool_spec:
            for param_def in tool_spec.parameters:
                if param_def.name not in resolved and param_def.default is not None:
                    resolved[param_def.name] = param_def.default

        return resolved

    def _determine_parameter_status(
        self,
        param_name: str,
        predicted_params: Dict[str, Any],
        ground_truth_params: Dict[str, Any],
        predicted_resolved: Dict[str, Any],
        ground_truth_resolved: Dict[str, Any],
    ) -> ParameterStatus:
        """Determine the status of a parameter in both calls."""
        pred_present = param_name in predicted_params
        gt_present = param_name in ground_truth_params
        pred_resolved = param_name in predicted_resolved
        gt_resolved = param_name in ground_truth_resolved

        if pred_present and gt_present:
            return ParameterStatus.BOTH_PRESENT
        elif not pred_present and not gt_present:
            if pred_resolved and gt_resolved:
                return ParameterStatus.BOTH_DEFAULT
            else:
                return ParameterStatus.BOTH_MISSING
        elif not pred_present and gt_present:
            if pred_resolved:
                return ParameterStatus.PRED_DEFAULT
            else:
                return ParameterStatus.PRED_MISSING
        elif pred_present and not gt_present:
            if gt_resolved:
                return ParameterStatus.GT_DEFAULT
            else:
                return ParameterStatus.GT_MISSING
        else:
            return ParameterStatus.BOTH_MISSING

    def _normalize_value(self, value: Any, expected_type: Optional[str] = None) -> Any:
        """Normalize values for comparison (e.g., string numbers to numbers)."""
        if not self.config.normalize_types:
            return value

        if expected_type == "integer" and isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                pass
        elif expected_type == "boolean" and isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        elif expected_type == "number" and isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                pass
        elif expected_type == "array" and isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                pass
        elif expected_type == "object" and isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                pass

        return value

    def _get_parameter_weight(self, param_name: str) -> float:
        """Get weight for a specific parameter."""
        for weight_config in self.config.parameter_weights:
            if weight_config.name == param_name:
                return weight_config.weight
        return 1.0

    def _is_critical_parameter(self, param_name: str) -> bool:
        """Check if a parameter is marked as critical."""
        for weight_config in self.config.parameter_weights:
            if weight_config.name == param_name:
                return weight_config.is_critical
        return False

    def _calculate_weighted_score(
        self, param_results: List[ParameterComparisonResult]
    ) -> float:
        """Calculate weighted parameter score considering importance."""
        if not param_results:
            return 1.0

        total_weight = 0
        weighted_sum = 0
        critical_failures = 0

        for result in param_results:
            weight = self._get_parameter_weight(result.parameter_name)
            total_weight += weight
            weighted_sum += result.score * weight

            # Check for critical parameter failures
            if (
                self._is_critical_parameter(result.parameter_name)
                and not result.is_match
            ):
                critical_failures += 1

        base_score = weighted_sum / total_weight if total_weight > 0 else 0

        # Apply critical failure penalty
        if critical_failures > 0:
            penalty = self.config.critical_parameter_penalty * critical_failures
            base_score *= 1 - penalty

        return max(0.0, min(1.0, base_score))

    def compare_tool_calls(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tool_specs: Optional[List[Dict[str, Any]]] = None,
    ) -> ToolCallComparisonResult:
        """Main comparison method orchestrating the full comparison."""

        # Extract function names
        pred_name = predicted_call.get("function", {}).get("name", "")
        gt_name = ground_truth_call.get("function", {}).get("name", "")

        # Compare function names
        fn_score = self.compare_function_name(pred_name, gt_name)
        fn_match = fn_score >= 0.95  # High threshold for exact match

        # Extract tool specification
        tool_spec = self._extract_tool_spec(
            gt_name, tool_specs
        ) or self._extract_tool_spec(pred_name, tool_specs)

        # Extract and parse parameters
        pred_params = predicted_call.get("function", {}).get("arguments", {})
        gt_params = ground_truth_call.get("function", {}).get("arguments", {})

        if isinstance(pred_params, str):
            try:
                pred_params = json.loads(pred_params)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse predicted parameters: {pred_params}")
                pred_params = {}

        if isinstance(gt_params, str):
            try:
                gt_params = json.loads(gt_params)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse ground truth parameters: {gt_params}")
                gt_params = {}

        # Resolve parameters with defaults
        pred_resolved = self._resolve_parameters_with_defaults(pred_params, tool_spec)
        gt_resolved = self._resolve_parameters_with_defaults(gt_params, tool_spec)

        # Determine all parameters to compare
        params_to_compare = self.config.parameters_to_compare
        if params_to_compare is None:
            if self.config.include_default_parameters:
                # Include all parameters that appear in either call or have defaults
                params_to_compare = set(pred_resolved.keys()) | set(gt_resolved.keys())
            else:
                # Only explicit parameters
                params_to_compare = set(pred_params.keys()) | set(gt_params.keys())

        # Find missing required parameters and unexpected parameters
        missing_required = []
        unexpected_params = []

        if tool_spec:
            required_params = {p.name for p in tool_spec.parameters if p.required}
            all_defined_params = {p.name for p in tool_spec.parameters}

            # Check for missing required parameters
            for req_param in required_params:
                if req_param not in pred_resolved and req_param not in gt_resolved:
                    missing_required.append(req_param)

            # Check for unexpected parameters
            for param_name in params_to_compare:
                if param_name not in all_defined_params:
                    unexpected_params.append(param_name)

        # Compare each parameter
        param_results = []
        context = {
            "conversation_history": conversation_history,
            "tool_specs": tool_specs,
            "tool_spec": tool_spec,
            "predicted_call": predicted_call,
            "ground_truth_call": ground_truth_call,
            "function_name": gt_name or pred_name,
        }

        for param_name in params_to_compare:
            pred_val = pred_params.get(param_name)
            gt_val = gt_params.get(param_name)
            pred_resolved_val = pred_resolved.get(param_name)
            gt_resolved_val = gt_resolved.get(param_name)

            # Get parameter definition from tool spec
            param_def = None
            if tool_spec:
                param_def = next(
                    (p for p in tool_spec.parameters if p.name == param_name), None
                )

            # Determine parameter status
            param_status = self._determine_parameter_status(
                param_name, pred_params, gt_params, pred_resolved, gt_resolved
            )

            # Enhanced context for this parameter
            param_context = context.copy()
            param_context.update(
                {
                    "parameter_definition": param_def.dict() if param_def else None,
                    "parameter_status": param_status,
                    "predicted_resolved": pred_resolved_val,
                    "ground_truth_resolved": gt_resolved_val,
                }
            )

            param_result = self.compare_parameter(
                param_name,
                pred_resolved_val,
                gt_resolved_val,
                param_context,
                custom_instructions=context.get("custom_instructions"),
            )

            # Enhance result with additional information
            param_result.predicted_resolved_value = pred_resolved_val
            param_result.ground_truth_resolved_value = gt_resolved_val
            param_result.parameter_status = param_status
            param_result.parameter_definition = param_def.dict() if param_def else None
            param_result.is_required = param_def.required if param_def else False
            param_result.default_value = param_def.default if param_def else None

            param_results.append(param_result)

        # Calculate overall score using weighted approach
        param_score = self._calculate_weighted_score(param_results)

        overall_score = (
            self.config.weight_function_name * fn_score
            + self.config.weight_parameters * param_score
        )

        # Apply penalties for missing required parameters
        if missing_required:
            penalty = len(missing_required) * self.config.missing_parameter_penalty
            overall_score *= 1 - penalty
            overall_score = max(0.0, overall_score)

        # Generate overall explanation
        overall_explanation = self._generate_overall_explanation(
            fn_match,
            fn_score,
            param_results,
            overall_score,
            missing_required,
            unexpected_params,
        )

        return ToolCallComparisonResult(
            predicted_call=predicted_call,
            ground_truth_call=ground_truth_call,
            function_name_match=fn_match,
            function_name_score=fn_score,
            parameter_results=param_results,
            overall_score=overall_score,
            overall_explanation=overall_explanation,
            strategy_used=self.config.strategy,
            missing_required_params=missing_required,
            unexpected_params=unexpected_params,
            metadata={
                "tool_spec_used": tool_spec.dict() if tool_spec else None,
                "parameters_compared": list(params_to_compare),
                "default_parameters_included": self.config.include_default_parameters,
            },
        )

    def _generate_overall_explanation(
        self,
        fn_match: bool,
        fn_score: float,
        param_results: List[ParameterComparisonResult],
        overall_score: float,
        missing_required: List[str],
        unexpected_params: List[str],
    ) -> str:
        """Generate human-readable explanation of comparison results."""
        explanations = []

        # Function name analysis
        if fn_match:
            explanations.append("Function names match exactly.")
        else:
            explanations.append(f"Function names differ (similarity: {fn_score:.2f}).")

        # Parameter analysis
        if param_results:
            matches = sum(1 for r in param_results if r.is_match)
            total = len(param_results)
            explanations.append(f"Parameters: {matches}/{total} matches.")

            # Break down by status
            status_counts = {}
            for result in param_results:
                status_counts[result.parameter_status] = (
                    status_counts.get(result.parameter_status, 0) + 1
                )

            if status_counts:
                status_summary = ", ".join(
                    [
                        f"{status.value}: {count}"
                        for status, count in status_counts.items()
                    ]
                )
                explanations.append(f"Parameter status breakdown: {status_summary}")

            if matches < total:
                mismatches = [r.parameter_name for r in param_results if not r.is_match]
                explanations.append(f"Mismatched parameters: {', '.join(mismatches)}")

        # Issues
        if missing_required:
            explanations.append(
                f"Missing required parameters: {', '.join(missing_required)}"
            )

        if unexpected_params:
            explanations.append(
                f"Unexpected parameters: {', '.join(unexpected_params)}"
            )

        explanations.append(f"Overall similarity score: {overall_score:.2f}")

        return " ".join(explanations)
