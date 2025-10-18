from typing import Any, Dict, List, Optional
import asyncio
import json
import logging

from llmevalkit.llm.output_parser import ValidatingLLMClient
from llmevalkit.metrics import Metric, StandardMetric, MetricPrompt
from .base import BaseComparator
from ..types import (
    ParameterComparisonResult,
    ComparisonStrategy,
    ParameterStatus,
)

logger = logging.getLogger(__name__)


class ParameterComparisonMetric(StandardMetric):
    """Metric for parameter comparison using LLM judge."""

    def __init__(self):
        super().__init__(
            name="parameter_comparison",
            description="Compare two parameter values for semantic equivalence",
            output_range=(0.0, 1.0),
            confidence_range=(0.0, 1.0),
        )

        # Add custom field for match determination
        from llmevalkit.metrics.field import BaseField

        self.add_field(
            BaseField(
                name="is_match",
                json_type="boolean",
                description="Whether the parameters are functionally equivalent",
            )
        )


class ParameterComparisonPrompt(MetricPrompt):
    """Prompt template for individual parameter comparison."""

    system_template = """You are an expert system for comparing function call parameters. Your task is to determine how similar two parameter values are in the context of API function calls.

**SCORING GUIDELINES**:

1. **EXACT MATCH (score = 1.0)**: Identical values
   - "hello" == "hello"
   - 123 == 123
   - true == true

2. **SEMANTIC EQUIVALENCE (score = 0.9-1.0)**: Different representation, same meaning
   - "true" vs true (string vs boolean)
   - "123" vs 123 (string vs number)
   - "2023-01-01" vs "January 1, 2023" (different date formats)
   - "yes" vs true (affirmative equivalents)

3. **PARTIAL MATCH (score = 0.3-0.8)**: Similar but not equivalent
   - "hello world" vs "hello" (partial string match)
   - Related but different values
   - Values with minor formatting differences

4. **NO MATCH (score = 0.0-0.2)**: Completely different values
   - "hello" vs 123
   - true vs "no"
   - Unrelated values

**Context**: Consider the conversation history and tool purpose when determining equivalence.

{% if custom_instructions %}
**CUSTOM EVALUATION INSTRUCTIONS**:
{{ custom_instructions }}

Follow these custom instructions carefully when making your comparison. They take priority over general guidelines when there are conflicts.
{% endif %}

{% if custom_schema %}
**CUSTOM RESPONSE SCHEMA**:
Use this custom JSON schema for your response instead of the default schema:
{{ custom_schema }}

IMPORTANT: Your response must strictly follow this custom schema format.
{% else %}
{{ metric_jsonschema }}
{% endif %}"""

    user_template = """**Parameter Comparison Task**

Parameter Name: {{ parameter_name }}
Parameter Type: {{ parameter_type }}
Required: {{ is_required }}
Status: {{ parameter_status }}
Default Value: {{ default_value }}
Tool Function: {{ function_name }}

**Predicted Value**:
- Value: {{ predicted_value }}
- Type: {{ predicted_type }}

**Ground Truth Value**:
- Value: {{ ground_truth_value }}
- Type: {{ ground_truth_type }}

**Parameter Definition**:
{{ parameter_definition }}

**Tool Specification (OpenAI Format)**:
{% if tool_specification %}
{{ tool_specification }}
{% else %}
No tool specification provided
{% endif %}

**Conversation Context**:
{% for message in conversation_context %}
{{ message.role }}: {{ message.content }}
{% endfor %}

{% if custom_instructions %}
**CUSTOM EVALUATION INSTRUCTIONS**:
{{ custom_instructions }}

IMPORTANT: Follow these custom instructions carefully when making your comparison. They take priority over general guidelines when there are conflicts.
{% endif %}

{% if custom_schema %}
**CUSTOM RESPONSE SCHEMA**:
Use this custom JSON schema for your response instead of the default schema:
{{ custom_schema }}

IMPORTANT: Your response must strictly follow this custom schema format.
{% endif %}

Please compare these parameter values and provide a detailed analysis."""


class BulkParameterComparisonMetric(StandardMetric):
    """Metric for bulk parameter comparison using LLM judge."""

    def __init__(self):
        super().__init__(
            name="bulk_parameter_comparison",
            description="Compare all parameters between predicted and ground truth tool calls in one evaluation",
            output_range=(0.0, 1.0),
            confidence_range=(0.0, 1.0),
        )

        # Add custom field for parameter-level scores
        from llmevalkit.metrics.field import BaseField

        self.add_field(
            BaseField(
                name="parameter_scores",
                json_type="object",
                description="Individual parameter comparison scores and explanations",
            )
        )


class BulkParameterComparisonPrompt(MetricPrompt):
    """Prompt template for bulk parameter comparison."""

    system_template = """You are an expert system for comparing function call parameters. Your task is to evaluate ALL parameters between two tool calls simultaneously and provide both individual parameter scores and an overall assessment.

**SCORING GUIDELINES**:

1. **EXACT MATCH (score = 1.0)**: Identical values
2. **SEMANTIC EQUIVALENCE (score = 0.9-1.0)**: Different representation, same meaning
3. **PARTIAL MATCH (score = 0.3-0.8)**: Similar but not equivalent  
4. **NO MATCH (score = 0.0-0.2)**: Completely different values

**EVALUATION PROCESS**:
1. Compare each parameter individually using the scoring guidelines
2. Consider parameter importance (required vs optional)
3. Account for default values and missing parameters
4. Provide an overall score that weights individual parameter scores appropriately

**OUTPUT REQUIREMENTS**:
- Overall score: Weighted average considering parameter importance
- Individual parameter scores: For each compared parameter
- Detailed explanations: For both overall and individual assessments

{% if custom_instructions %}
**CUSTOM EVALUATION INSTRUCTIONS**:
{{ custom_instructions }}

Follow these custom instructions carefully when making your comparison. They take priority over general guidelines when there are conflicts.
{% endif %}

{% if custom_schema %}
**CUSTOM RESPONSE SCHEMA**:
Use this custom JSON schema for your response instead of the default schema:
{{ custom_schema }}

IMPORTANT: Your response must strictly follow this custom schema format.
{% else %}
{{ metric_jsonschema }}
{% endif %}"""

    user_template = """**Bulk Parameter Comparison Task**

Function Name: {{ function_name }}

**Predicted Call Arguments**:
{{ predicted_arguments_json }}

**Ground Truth Call Arguments**:  
{{ ground_truth_arguments_json }}

**Tool Specification (OpenAI Format)**:
{% if tool_specification %}
{{ tool_specification }}
{% else %}
No tool specification provided
{% endif %}

**Parameters to Compare**:
{% for param_name, param_info in parameters_info.items() %}
- **{{ param_name }}**:
  - Required: {{ param_info.is_required }}
  - Type: {{ param_info.parameter_type }}
  - Default: {{ param_info.default_value }}
  - Status: {{ param_info.status }}
  - Predicted: {{ param_info.predicted_value }} ({{ param_info.predicted_type }})
  - Ground Truth: {{ param_info.ground_truth_value }} ({{ param_info.ground_truth_type }})
{% endfor %}

**Conversation Context**:
{% for message in conversation_context %}
{{ message.role }}: {{ message.content }}
{% endfor %}

{% if custom_instructions %}
**CUSTOM EVALUATION INSTRUCTIONS**:
{{ custom_instructions }}

IMPORTANT: Follow these custom instructions carefully when making your comparison. They take priority over general guidelines when there are conflicts.
{% endif %}

{% if custom_schema %}
**CUSTOM RESPONSE SCHEMA**:
Use this custom JSON schema for your response instead of the default schema:
{{ custom_schema }}

IMPORTANT: Your response must strictly follow this custom schema format.
{% endif %}

Please evaluate all parameters and provide individual scores plus an overall assessment."""


class LLMJudgeComparator(BaseComparator):
    """LLM-based semantic comparison using ValidatingLLMClient and metrics framework."""

    def __init__(self, config, llm_client):
        super().__init__(config)

        # Accept ValidatingLLMClient or compatible objects (for testing)
        if not (
            isinstance(llm_client, ValidatingLLMClient)
            or hasattr(llm_client, "generate")
            or hasattr(llm_client, "generate_async")
        ):
            raise TypeError(
                "LLMJudgeComparator requires a ValidatingLLMClient or compatible client"
            )

        self.llm_client = llm_client

        # Initialize metrics and prompts for both individual and bulk comparison
        self.metric = ParameterComparisonMetric()
        self.prompt = ParameterComparisonPrompt(
            metric=self.metric,
            system_template=ParameterComparisonPrompt.system_template,
            user_template=ParameterComparisonPrompt.user_template,
        )

        # Initialize bulk comparison metric and prompt
        self.bulk_metric = BulkParameterComparisonMetric()
        self.bulk_prompt = BulkParameterComparisonPrompt(
            metric=self.bulk_metric,
            system_template=BulkParameterComparisonPrompt.system_template,
            user_template=BulkParameterComparisonPrompt.user_template,
        )

        # Add few-shot examples
        self._add_examples()

    @staticmethod
    def get_default_individual_schema():
        """Get default JSON schema for individual parameter comparison."""
        return {
            "type": "object",
            "properties": {
                "score": {
                    "type": "number",
                    "description": "Similarity score between 0.0 and 1.0",
                },
                "is_match": {
                    "type": "boolean",
                    "description": "Whether the parameters are functionally equivalent",
                },
                "explanation": {
                    "type": "string",
                    "description": "Brief explanation of the comparison result",
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence in the assessment between 0.0 and 1.0",
                },
            },
            "required": ["score", "is_match", "explanation", "confidence"],
        }

    @staticmethod
    def get_default_bulk_schema():
        """Get default JSON schema for bulk parameter comparison."""
        return {
            "type": "object",
            "properties": {
                "overall_score": {
                    "type": "number",
                    "description": "Overall similarity score between 0.0 and 1.0",
                },
                "overall_explanation": {
                    "type": "string",
                    "description": "Detailed explanation of the comparison",
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence in the assessment between 0.0 and 1.0",
                },
                "parameter_scores": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "score": {
                                "type": "number",
                                "description": "Individual parameter score",
                            },
                            "explanation": {
                                "type": "string",
                                "description": "Explanation for this parameter",
                            },
                            "is_match": {
                                "type": "boolean",
                                "description": "Whether this parameter matches",
                            },
                        },
                        "required": ["score", "explanation", "is_match"],
                    },
                },
            },
            "required": [
                "overall_score",
                "overall_explanation",
                "confidence",
                "parameter_scores",
            ],
        }

    def _add_examples(self):
        """Add few-shot examples to improve LLM performance."""
        examples = [
            {
                "user_kwargs": {
                    "parameter_name": "enabled",
                    "function_name": "set_feature",
                    "parameter_type": "boolean",
                    "is_required": "true",
                    "parameter_status": "both_present",
                    "default_value": "null",
                    "predicted_value": "true",
                    "predicted_type": "string",
                    "ground_truth_value": "true",
                    "ground_truth_type": "boolean",
                    "conversation_context": [],
                    "parameter_definition": "Boolean flag to enable feature",
                },
                "output": {
                    "explanation": "String 'true' is semantically equivalent to boolean true",
                    "evidence": "Both values represent the same boolean state despite different types",
                    "output": 1.0,
                    "confidence": 0.95,
                    "is_match": True,
                    "correction": {
                        "has_issues": False,
                        "issue_type": "none",
                        "corrected_value": None,
                    },
                },
            },
            {
                "user_kwargs": {
                    "parameter_name": "count",
                    "function_name": "process_items",
                    "parameter_type": "integer",
                    "is_required": "true",
                    "parameter_status": "both_present",
                    "default_value": "null",
                    "predicted_value": "10",
                    "predicted_type": "string",
                    "ground_truth_value": "10",
                    "ground_truth_type": "integer",
                    "conversation_context": [],
                    "parameter_definition": "Number of items to process",
                },
                "output": {
                    "explanation": "String '10' represents the same numeric value as integer 10",
                    "evidence": "Both values represent the same quantity despite type difference",
                    "output": 1.0,
                    "confidence": 0.98,
                    "is_match": True,
                    "correction": {
                        "has_issues": False,
                        "issue_type": "none",
                        "corrected_value": None,
                    },
                },
            },
            {
                "user_kwargs": {
                    "parameter_name": "message",
                    "function_name": "send_notification",
                    "parameter_type": "string",
                    "is_required": "true",
                    "parameter_status": "both_present",
                    "default_value": "null",
                    "predicted_value": "Hello World",
                    "predicted_type": "string",
                    "ground_truth_value": "Hello world",
                    "ground_truth_type": "string",
                    "conversation_context": [],
                    "parameter_definition": "Message text to display",
                },
                "output": {
                    "explanation": "Minor capitalization difference in otherwise identical strings",
                    "evidence": "Content is essentially the same with only case variation",
                    "output": 0.9,
                    "confidence": 0.8,
                    "is_match": False,
                    "correction": {
                        "has_issues": True,
                        "issue_type": "formatting",
                        "corrected_value": "Hello world",
                    },
                },
            },
        ]

        for example in examples:
            self.prompt.add_example(example["user_kwargs"], example["output"])

    def compare_parameter(
        self,
        param_name: str,
        predicted_value: Any,
        ground_truth_value: Any,
        context: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
        custom_schema: Optional[Dict[str, Any]] = None,
    ) -> ParameterComparisonResult:
        """Compare parameters with optional custom instructions - SYNC VERSION"""

        context = context or {}
        param_def = context.get("parameter_definition", {})
        param_status = context.get("parameter_status", ParameterStatus.BOTH_PRESENT)

        # Normalize values if configured
        param_type = param_def.get("type", "string") if param_def else "string"

        if self.config.normalize_types:
            predicted_value = self._normalize_value(predicted_value, param_type)
            ground_truth_value = self._normalize_value(ground_truth_value, param_type)

        # Build prompt arguments
        user_kwargs = {
            "parameter_name": param_name,
            "function_name": context.get("function_name", "unknown"),
            "parameter_type": param_type,
            "is_required": (
                str(param_def.get("required", False)) if param_def else "false"
            ),
            "parameter_status": (
                param_status.value
                if hasattr(param_status, "value")
                else str(param_status)
            ),
            "default_value": (
                str(param_def.get("default"))
                if param_def and param_def.get("default") is not None
                else "null"
            ),
            "predicted_value": str(predicted_value),
            "predicted_type": type(predicted_value).__name__,
            "ground_truth_value": str(ground_truth_value),
            "ground_truth_type": type(ground_truth_value).__name__,
            "conversation_context": context.get("conversation_history", []),
            "parameter_definition": (
                param_def.get("description", "") if param_def else ""
            ),
            "tool_specification": context.get("tool_specification", None),
            "custom_instructions": custom_instructions or " ",
        }

        # Build messages using the prompt template
        messages = self.prompt.build_messages(user_kwargs)

        try:
            # Use ValidatingLLMClient with schema - try metric schema first, fallback to default
            schema = None
            try:
                schema = self.metric.to_jsonschema()
            except Exception:
                # Fallback to default schema if metric schema fails
                schema = self.get_default_individual_schema()

            response = self.llm_client.generate(
                prompt=messages,
                schema=schema,
            )

            # Parse the validated response
            if isinstance(response, str):
                result_data = json.loads(response)
            else:
                result_data = response

            score = float(result_data.get("output", 0.0))
            explanation = result_data.get("explanation", "")
            confidence = float(result_data.get("confidence", 0.5))
            is_match = bool(result_data.get("is_match", False))
            evidence = result_data.get("evidence", "")

            # Clamp score to valid range
            score = max(0.0, min(1.0, score))
            confidence = max(0.0, min(1.0, confidence))

        except Exception as e:
            logger.warning(f"LLM comparison failed for parameter {param_name}: {e}")

            # Fallback to exact match
            is_match = predicted_value == ground_truth_value
            score = 1.0 if is_match else 0.0
            explanation = f"LLM comparison failed ({str(e)}), using exact match. Result: {is_match}"
            confidence = 0.3  # Low confidence due to fallback
            evidence = "Fallback comparison due to LLM error"

        return ParameterComparisonResult(
            parameter_name=param_name,
            predicted_value=predicted_value,
            ground_truth_value=ground_truth_value,
            predicted_resolved_value=predicted_value,
            ground_truth_resolved_value=ground_truth_value,
            parameter_status=param_status,
            comparison_strategy=ComparisonStrategy.LLM_JUDGE,
            score=score,
            explanation=explanation,
            evidence=evidence,
            is_match=is_match,
            confidence=confidence,
        )

    def compare_function_name(
        self,
        predicted_name: str,
        ground_truth_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Compare function names with semantic understanding."""

        # Exact match gets perfect score
        if predicted_name == ground_truth_name:
            return 1.0

        # Use LLM for semantic function name comparison
        system_prompt = """You are comparing two function names for semantic similarity. 
        Consider:
        1. Exact matches = 1.0
        2. Synonymous functions (e.g., "get_user" vs "fetch_user") = 0.8-0.9
        3. Related functions (e.g., "get_user" vs "get_profile") = 0.3-0.7
        4. Unrelated functions = 0.0-0.2
        
        Return only a numeric score between 0.0 and 1.0."""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Function 1: {predicted_name}\nFunction 2: {ground_truth_name}",
            },
        ]

        try:
            response = self.llm_client.generate(prompt=messages)

            # Extract numeric score
            import re

            score_match = re.search(r"\b([0-1](?:\.\d+)?)\b", str(response))
            if score_match:
                score = float(score_match.group(1))
                return max(0.0, min(1.0, score))

        except Exception as e:
            logger.warning(f"LLM function name comparison failed: {e}")

        # Conservative fallback
        return 0.0

    async def compare_parameter_async(
        self,
        param_name: str,
        predicted_value: Any,
        ground_truth_value: Any,
        context: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
        custom_schema: Optional[Dict[str, Any]] = None,
    ) -> ParameterComparisonResult:
        """Async version of parameter comparison."""

        context = context or {}
        param_def = context.get("parameter_definition", {})
        param_status = context.get("parameter_status", ParameterStatus.BOTH_PRESENT)

        # Normalize values if configured
        param_type = param_def.get("type", "string") if param_def else "string"

        if self.config.normalize_types:
            predicted_value = self._normalize_value(predicted_value, param_type)
            ground_truth_value = self._normalize_value(ground_truth_value, param_type)

        # Build prompt arguments
        user_kwargs = {
            "parameter_name": param_name,
            "function_name": context.get("function_name", "unknown"),
            "parameter_type": param_type,
            "is_required": (
                str(param_def.get("required", False)) if param_def else "false"
            ),
            "parameter_status": (
                param_status.value
                if hasattr(param_status, "value")
                else str(param_status)
            ),
            "default_value": (
                str(param_def.get("default"))
                if param_def and param_def.get("default") is not None
                else "null"
            ),
            "predicted_value": str(predicted_value),
            "predicted_type": type(predicted_value).__name__,
            "ground_truth_value": str(ground_truth_value),
            "ground_truth_type": type(ground_truth_value).__name__,
            "conversation_context": context.get("conversation_history", []),
            "parameter_definition": (
                param_def.get("description", "") if param_def else ""
            ),
            "tool_specification": context.get("tool_specification", None),
            "custom_instructions": custom_instructions or " ",
        }

        # Build messages using the prompt template
        messages = self.prompt.build_messages(user_kwargs)

        try:
            # Use ValidatingLLMClient with schema - try metric schema first, fallback to default
            schema = None
            try:
                schema = self.metric.to_jsonschema()
            except Exception:
                # Fallback to default schema if metric schema fails
                schema = self.get_default_individual_schema()

            response = await self.llm_client.generate_async(
                prompt=messages,
                schema=schema,
            )

            # Parse the validated response
            if isinstance(response, str):
                result_data = json.loads(response)
            else:
                result_data = response

            score = float(result_data.get("output", 0.0))
            explanation = result_data.get("explanation", "")
            confidence = float(result_data.get("confidence", 0.5))
            is_match = bool(result_data.get("is_match", False))
            evidence = result_data.get("evidence", "")

            # Clamp score to valid range
            score = max(0.0, min(1.0, score))
            confidence = max(0.0, min(1.0, confidence))

        except Exception as e:
            logger.warning(
                f"Async LLM comparison failed for parameter {param_name}: {e}"
            )

            # Fallback to exact match
            is_match = predicted_value == ground_truth_value
            score = 1.0 if is_match else 0.0
            explanation = f"LLM comparison failed ({str(e)}), using exact match. Result: {is_match}"
            confidence = 0.3  # Low confidence due to fallback
            evidence = "Fallback comparison due to LLM error"

        return ParameterComparisonResult(
            parameter_name=param_name,
            predicted_value=predicted_value,
            ground_truth_value=ground_truth_value,
            predicted_resolved_value=predicted_value,
            ground_truth_resolved_value=ground_truth_value,
            parameter_status=param_status,
            comparison_strategy=ComparisonStrategy.LLM_JUDGE,
            score=score,
            explanation=explanation,
            evidence=evidence,
            is_match=is_match,
            confidence=confidence,
        )

    async def compare_tool_calls_async(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tool_specs: Optional[List[Dict[str, Any]]] = None,
        custom_instructions: Optional[str] = None,
    ) -> Any:  # Return type imported dynamically to avoid circular imports
        """Async version of tool call comparison with parameter-level async support."""

        # Import here to avoid circular imports
        from ..types import ToolCallComparisonResult, FunctionCallInput

        # Use the base class logic but with async parameter comparison
        # Extract function names
        pred_name = predicted_call.get("function", {}).get("name", "")
        gt_name = ground_truth_call.get("function", {}).get("name", "")

        # Compare function names (sync operation)
        fn_score = self.compare_function_name(pred_name, gt_name)
        fn_match = fn_score >= 0.95

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
                params_to_compare = set(pred_resolved.keys()) | set(gt_resolved.keys())
            else:
                params_to_compare = set(pred_params.keys()) | set(gt_params.keys())

        # Compare each parameter asynchronously
        param_tasks = []
        context = {
            "conversation_history": conversation_history,
            "tool_specs": tool_specs,
            "tool_spec": tool_spec,
            "predicted_call": predicted_call,
            "ground_truth_call": ground_truth_call,
            "function_name": gt_name or pred_name,
        }

        import asyncio

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

            # Create async task for parameter comparison
            task = self.compare_parameter_async(
                param_name,
                pred_resolved_val,
                gt_resolved_val,
                param_context,
                custom_instructions=custom_instructions,
            )
            param_tasks.append(task)

        # Wait for all parameter comparisons to complete
        param_results = await asyncio.gather(*param_tasks)

        # Enhance results with additional information
        for result, param_name in zip(param_results, params_to_compare):
            pred_resolved_val = pred_resolved.get(param_name)
            gt_resolved_val = gt_resolved.get(param_name)
            param_status = self._determine_parameter_status(
                param_name, pred_params, gt_params, pred_resolved, gt_resolved
            )

            param_def = None
            if tool_spec:
                param_def = next(
                    (p for p in tool_spec.parameters if p.name == param_name), None
                )

            result.predicted_resolved_value = pred_resolved_val
            result.ground_truth_resolved_value = gt_resolved_val
            result.parameter_status = param_status
            result.parameter_definition = param_def.dict() if param_def else None
            result.is_required = param_def.required if param_def else False
            result.default_value = param_def.default if param_def else None

        # Calculate overall score using weighted approach
        param_score = self._calculate_weighted_score(param_results)

        overall_score = (
            self.config.weight_function_name * fn_score
            + self.config.weight_parameters * param_score
        )

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
                "execution_mode": "async",
            },
        )

    def compare_tool_calls(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tool_specs: Optional[List[Dict[str, Any]]] = None,
        custom_instructions: Optional[str] = None,
        custom_schema: Optional[str] = None,
    ) -> Any:
        """
        Sync version that checks if bulk comparison is enabled.
        """
        if self.config.llm_bulk_comparison:
            return self._compare_tool_calls_bulk(
                predicted_call,
                ground_truth_call,
                conversation_history,
                tool_specs,
                custom_instructions,
            )
        else:
            # Use the base class implementation (individual parameter comparison)
            # Note: Base class doesn't support custom_instructions yet, but we can still call it
            return super().compare_tool_calls(
                predicted_call, ground_truth_call, conversation_history, tool_specs
            )

    async def _compare_tool_calls_individual_async(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tool_specs: Optional[List[Dict[str, Any]]] = None,
        custom_instructions: Optional[str] = None,
        custom_schema: Optional[str] = None,
    ) -> Any:
        """
        Async version that checks if bulk comparison is enabled.
        """
        if self.config.llm_bulk_comparison:
            return await self._compare_tool_calls_bulk_async(
                predicted_call,
                ground_truth_call,
                conversation_history,
                tool_specs,
                custom_instructions,
                custom_schema,
            )
        else:
            # Use individual parameter comparison async (already implemented above)
            return await self._compare_tool_calls_individual_async(
                predicted_call,
                ground_truth_call,
                conversation_history,
                tool_specs,
                custom_instructions,
            )

    def _compare_tool_calls_bulk(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tool_specs: Optional[List[Dict[str, Any]]] = None,
        custom_instructions: Optional[str] = None,
    ) -> Any:
        """Sync bulk comparison of all parameters in one LLM call."""

        # Import here to avoid circular imports
        from ..types import ToolCallComparisonResult

        # Extract function names
        pred_name = predicted_call.get("function", {}).get("name", "")
        gt_name = ground_truth_call.get("function", {}).get("name", "")

        # Compare function names (sync operation)
        fn_score = self.compare_function_name(pred_name, gt_name)
        fn_match = fn_score >= 0.95

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
                params_to_compare = set(pred_resolved.keys()) | set(gt_resolved.keys())
            else:
                params_to_compare = set(pred_params.keys()) | set(gt_params.keys())

        # Build bulk comparison context
        parameters_info = {}
        for param_name in params_to_compare:
            pred_val = pred_resolved.get(param_name)
            gt_val = gt_resolved.get(param_name)
            param_status = self._determine_parameter_status(
                param_name, pred_params, gt_params, pred_resolved, gt_resolved
            )

            # Get parameter definition from tool spec
            param_def = None
            if tool_spec:
                param_def = next(
                    (p for p in tool_spec.parameters if p.name == param_name), None
                )

            parameters_info[param_name] = {
                "predicted_value": pred_val,
                "ground_truth_value": gt_val,
                "predicted_type": type(pred_val).__name__,
                "ground_truth_type": type(gt_val).__name__,
                "is_required": param_def.required if param_def else False,
                "parameter_type": param_def.type if param_def else "unknown",
                "default_value": param_def.default if param_def else None,
                "status": (
                    param_status.value
                    if hasattr(param_status, "value")
                    else str(param_status)
                ),
            }

        # Build prompt arguments for bulk comparison
        user_kwargs = {
            "function_name": gt_name or pred_name,
            "predicted_arguments_json": json.dumps(pred_resolved, indent=2),
            "ground_truth_arguments_json": json.dumps(gt_resolved, indent=2),
            "tool_specification": json.dumps(
                tool_spec.dict() if tool_spec else {}, indent=2
            ),
            "parameters_info": parameters_info,
            "conversation_context": conversation_history or [],
            "custom_instructions": custom_instructions or " ",
        }

        # Build messages using the bulk prompt template
        messages = self.bulk_prompt.build_messages(user_kwargs)

        try:
            # Use ValidatingLLMClient with schema - try bulk metric schema first, fallback to default
            schema = None
            try:
                schema = self.bulk_metric.to_jsonschema()
            except Exception:
                # Fallback to default schema if bulk metric schema fails
                schema = self.get_default_bulk_schema()

            response = self.llm_client.generate(
                prompt=messages,
                schema=schema,
            )

            # Parse the validated response
            if isinstance(response, str):
                result_data = json.loads(response)
            else:
                result_data = response

            overall_score = float(result_data.get("overall_score", 0.0))
            overall_explanation = result_data.get("overall_explanation", "")
            confidence = float(result_data.get("confidence", 0.5))
            parameter_scores = result_data.get("parameter_scores", {})

            # Convert bulk result to individual parameter results
            param_results = []
            for param_name in params_to_compare:
                param_score_data = parameter_scores.get(param_name, {})
                param_score = float(param_score_data.get("score", 0.0))
                param_explanation = param_score_data.get(
                    "explanation", f"No explanation for {param_name}"
                )
                param_is_match = bool(param_score_data.get("is_match", False))

                param_info = parameters_info[param_name]
                param_status = self._determine_parameter_status(
                    param_name, pred_params, gt_params, pred_resolved, gt_resolved
                )

                param_result = ParameterComparisonResult(
                    parameter_name=param_name,
                    predicted_value=pred_params.get(param_name),
                    ground_truth_value=gt_params.get(param_name),
                    predicted_resolved_value=param_info["predicted_value"],
                    ground_truth_resolved_value=param_info["ground_truth_value"],
                    parameter_status=param_status,
                    comparison_strategy=ComparisonStrategy.LLM_JUDGE,
                    score=param_score,
                    explanation=param_explanation,
                    evidence=f"Bulk LLM comparison (confidence: {confidence:.2f})",
                    is_match=param_is_match,
                    confidence=confidence,
                )
                param_results.append(param_result)

        except Exception as e:
            logger.warning(f"Bulk LLM comparison failed: {e}")

            # Fallback to individual parameter comparison
            return super().compare_tool_calls(
                predicted_call, ground_truth_call, conversation_history, tool_specs
            )

        # Calculate overall score (already provided by bulk LLM)
        overall_score = max(0.0, min(1.0, overall_score))

        # Apply function name weight
        final_score = (
            self.config.weight_function_name * fn_score
            + self.config.weight_parameters * overall_score
        )

        # Find missing required parameters and unexpected parameters
        missing_required = []
        unexpected_params = []

        if tool_spec:
            required_params = {p.name for p in tool_spec.parameters if p.required}
            all_defined_params = {p.name for p in tool_spec.parameters}

            for req_param in required_params:
                if req_param not in pred_resolved and req_param not in gt_resolved:
                    missing_required.append(req_param)

            for param_name in params_to_compare:
                if param_name not in all_defined_params:
                    unexpected_params.append(param_name)

        # Apply penalties for missing required parameters
        if missing_required:
            penalty = len(missing_required) * self.config.missing_parameter_penalty
            final_score *= 1 - penalty
            final_score = max(0.0, final_score)

        return ToolCallComparisonResult(
            predicted_call=predicted_call,
            ground_truth_call=ground_truth_call,
            function_name_match=fn_match,
            function_name_score=fn_score,
            parameter_results=param_results,
            overall_score=final_score,
            overall_explanation=f"Bulk LLM comparison: {overall_explanation}",
            strategy_used=self.config.strategy,
            missing_required_params=missing_required,
            unexpected_params=unexpected_params,
            metadata={
                "tool_spec_used": tool_spec.dict() if tool_spec else None,
                "parameters_compared": list(params_to_compare),
                "default_parameters_included": self.config.include_default_parameters,
                "bulk_comparison": True,
                "llm_confidence": confidence,
                "execution_mode": "sync_bulk",
            },
        )

    async def _compare_tool_calls_bulk_async(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tool_specs: Optional[List[Dict[str, Any]]] = None,
        custom_instructions: Optional[str] = None,
    ) -> Any:
        """Async bulk comparison of all parameters in one LLM call."""

        # Most of the logic is the same as sync version, but with async LLM call
        # Import here to avoid circular imports
        from ..types import ToolCallComparisonResult

        # [Same parameter extraction and processing logic as sync version]
        # Extract function names
        pred_name = predicted_call.get("function", {}).get("name", "")
        gt_name = ground_truth_call.get("function", {}).get("name", "")

        # Compare function names (sync operation)
        fn_score = self.compare_function_name(pred_name, gt_name)
        fn_match = fn_score >= 0.95

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
                params_to_compare = set(pred_resolved.keys()) | set(gt_resolved.keys())
            else:
                params_to_compare = set(pred_params.keys()) | set(gt_params.keys())

        # Build bulk comparison context
        parameters_info = {}
        for param_name in params_to_compare:
            pred_val = pred_resolved.get(param_name)
            gt_val = gt_resolved.get(param_name)
            param_status = self._determine_parameter_status(
                param_name, pred_params, gt_params, pred_resolved, gt_resolved
            )

            # Get parameter definition from tool spec
            param_def = None
            if tool_spec:
                param_def = next(
                    (p for p in tool_spec.parameters if p.name == param_name), None
                )

            parameters_info[param_name] = {
                "predicted_value": pred_val,
                "ground_truth_value": gt_val,
                "predicted_type": type(pred_val).__name__,
                "ground_truth_type": type(gt_val).__name__,
                "is_required": param_def.required if param_def else False,
                "parameter_type": param_def.type if param_def else "unknown",
                "default_value": param_def.default if param_def else None,
                "status": (
                    param_status.value
                    if hasattr(param_status, "value")
                    else str(param_status)
                ),
            }

        # Build prompt arguments for bulk comparison
        user_kwargs = {
            "function_name": gt_name or pred_name,
            "predicted_arguments_json": json.dumps(pred_resolved, indent=2),
            "ground_truth_arguments_json": json.dumps(gt_resolved, indent=2),
            "tool_specification": json.dumps(
                tool_spec.dict() if tool_spec else {}, indent=2
            ),
            "parameters_info": parameters_info,
            "conversation_context": conversation_history or [],
        }

        # Build messages using the bulk prompt template
        messages = self.bulk_prompt.build_messages(user_kwargs)

        try:
            # Use ValidatingLLMClient with schema - try bulk metric schema first, fallback to default
            schema = None
            try:
                schema = self.bulk_metric.to_jsonschema()
            except Exception:
                # Fallback to default schema if bulk metric schema fails
                schema = self.get_default_bulk_schema()

            response = await self.llm_client.generate_async(
                prompt=messages,
                schema=schema,
            )

            # Parse the validated response
            if isinstance(response, str):
                result_data = json.loads(response)
            else:
                result_data = response

            overall_score = float(result_data.get("overall_score", 0.0))
            overall_explanation = result_data.get("overall_explanation", "")
            confidence = float(result_data.get("confidence", 0.5))
            parameter_scores = result_data.get("parameter_scores", {})

            # Convert bulk result to individual parameter results
            param_results = []
            for param_name in params_to_compare:
                param_score_data = parameter_scores.get(param_name, {})
                param_score = float(param_score_data.get("score", 0.0))
                param_explanation = param_score_data.get(
                    "explanation", f"No explanation for {param_name}"
                )
                param_is_match = bool(param_score_data.get("is_match", False))

                param_info = parameters_info[param_name]
                param_status = self._determine_parameter_status(
                    param_name, pred_params, gt_params, pred_resolved, gt_resolved
                )

                param_result = ParameterComparisonResult(
                    parameter_name=param_name,
                    predicted_value=pred_params.get(param_name),
                    ground_truth_value=gt_params.get(param_name),
                    predicted_resolved_value=param_info["predicted_value"],
                    ground_truth_resolved_value=param_info["ground_truth_value"],
                    parameter_status=param_status,
                    comparison_strategy=ComparisonStrategy.LLM_JUDGE,
                    score=param_score,
                    explanation=param_explanation,
                    evidence=f"Bulk LLM comparison (confidence: {confidence:.2f})",
                    is_match=param_is_match,
                    confidence=confidence,
                )
                param_results.append(param_result)

        except Exception as e:
            logger.warning(f"Async bulk LLM comparison failed: {e}")

            # Fallback to individual parameter comparison async
            return await self._compare_tool_calls_individual_async(
                predicted_call, ground_truth_call, conversation_history, tool_specs
            )

        # Calculate overall score (already provided by bulk LLM)
        overall_score = max(0.0, min(1.0, overall_score))

        # Apply function name weight
        final_score = (
            self.config.weight_function_name * fn_score
            + self.config.weight_parameters * overall_score
        )

        # Find missing required parameters and unexpected parameters
        missing_required = []
        unexpected_params = []

        if tool_spec:
            required_params = {p.name for p in tool_spec.parameters if p.required}
            all_defined_params = {p.name for p in tool_spec.parameters}

            for req_param in required_params:
                if req_param not in pred_resolved and req_param not in gt_resolved:
                    missing_required.append(req_param)

            for param_name in params_to_compare:
                if param_name not in all_defined_params:
                    unexpected_params.append(param_name)

        # Apply penalties for missing required parameters
        if missing_required:
            penalty = len(missing_required) * self.config.missing_parameter_penalty
            final_score *= 1 - penalty
            final_score = max(0.0, final_score)

        return ToolCallComparisonResult(
            predicted_call=predicted_call,
            ground_truth_call=ground_truth_call,
            function_name_match=fn_match,
            function_name_score=fn_score,
            parameter_results=param_results,
            overall_score=final_score,
            overall_explanation=f"Bulk LLM comparison: {overall_explanation}",
            strategy_used=self.config.strategy,
            missing_required_params=missing_required,
            unexpected_params=unexpected_params,
            metadata={
                "tool_spec_used": tool_spec.dict() if tool_spec else None,
                "parameters_compared": list(params_to_compare),
                "default_parameters_included": self.config.include_default_parameters,
                "bulk_comparison": True,
                "llm_confidence": confidence,
                "execution_mode": "async_bulk",
            },
        )

    async def _compare_tool_calls_individual_async(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tool_specs: Optional[List[Dict[str, Any]]] = None,
        custom_instructions: Optional[str] = None,
    ) -> Any:
        """Wrapper for the original async individual parameter comparison logic."""

        # This is the existing async logic that was in compare_tool_calls_async
        # Import here to avoid circular imports
        from ..types import ToolCallComparisonResult, FunctionCallInput

        # Use the base class logic but with async parameter comparison
        # Extract function names
        pred_name = predicted_call.get("function", {}).get("name", "")
        gt_name = ground_truth_call.get("function", {}).get("name", "")

        # Compare function names (sync operation)
        fn_score = self.compare_function_name(pred_name, gt_name)
        fn_match = fn_score >= 0.95

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
                params_to_compare = set(pred_resolved.keys()) | set(gt_resolved.keys())
            else:
                params_to_compare = set(pred_params.keys()) | set(gt_params.keys())

        # Compare each parameter asynchronously
        param_tasks = []
        context = {
            "conversation_history": conversation_history,
            "tool_specs": tool_specs,
            "tool_spec": tool_spec,
            "predicted_call": predicted_call,
            "ground_truth_call": ground_truth_call,
            "function_name": gt_name or pred_name,
        }

        import asyncio

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

            # Create async task for parameter comparison
            task = self.compare_parameter_async(
                param_name,
                pred_resolved_val,
                gt_resolved_val,
                param_context,
                custom_instructions=custom_instructions,
            )
            param_tasks.append(task)

        # Wait for all parameter comparisons to complete
        param_results = await asyncio.gather(*param_tasks)

        # Enhance results with additional information
        for result, param_name in zip(param_results, params_to_compare):
            pred_resolved_val = pred_resolved.get(param_name)
            gt_resolved_val = gt_resolved.get(param_name)
            param_status = self._determine_parameter_status(
                param_name, pred_params, gt_params, pred_resolved, gt_resolved
            )

            param_def = None
            if tool_spec:
                param_def = next(
                    (p for p in tool_spec.parameters if p.name == param_name), None
                )

            result.predicted_resolved_value = pred_resolved_val
            result.ground_truth_resolved_value = gt_resolved_val
            result.parameter_status = param_status
            result.parameter_definition = param_def.dict() if param_def else None
            result.is_required = param_def.required if param_def else False
            result.default_value = param_def.default if param_def else None

        # Calculate overall score using weighted approach
        param_score = self._calculate_weighted_score(param_results)

        overall_score = (
            self.config.weight_function_name * fn_score
            + self.config.weight_parameters * param_score
        )

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
                "execution_mode": "async_individual",
            },
        )

    # Enhanced LLM Judge Methods with Custom Schema Support

    async def compare_tool_calls_with_custom_schema(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tool_specs: Optional[List[Dict[str, Any]]] = None,
        custom_instructions: Optional[str] = None,
        custom_schema: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compare tool calls using custom schema and instructions.

        Args:
            predicted_call: The predicted function call
            ground_truth_call: The ground truth function call
            conversation_history: Optional conversation context
            tool_specs: Optional tool specifications
            custom_instructions: Custom evaluation instructions
            custom_schema: Custom JSON schema for response format

        Returns:
            Comparison result following the custom schema format
        """

        # Build detailed context for evaluation
        user_prompt = self._build_custom_evaluation_prompt(
            predicted_call=predicted_call,
            ground_truth_call=ground_truth_call,
            conversation_history=conversation_history or [],
            tool_specs=tool_specs or [],
            custom_instructions=custom_instructions,
        )

        # Build system prompt with custom schema
        system_prompt = self._build_custom_system_prompt(
            custom_instructions=custom_instructions,
            custom_schema=custom_schema,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            # Use custom schema if provided, otherwise fallback to default
            schema = None
            if custom_schema:
                try:
                    schema = json.loads(custom_schema)
                except json.JSONDecodeError as e:
                    logger.warning(
                        f"Invalid custom schema JSON: {e}. Using default schema."
                    )
                    schema = self.get_default_bulk_schema()
            else:
                schema = self.get_default_bulk_schema()

            # Generate response with schema validation
            response = await self.llm_client.generate_async(
                prompt=messages,
                schema=schema,
            )

            # Parse response
            if isinstance(response, str):
                result_data = json.loads(response)
            else:
                result_data = response

            # Create result object with custom schema data
            from llmevalkit.function_calling.comparison.types import (
                ToolCallComparisonResult,
            )

            # Extract standard fields with fallbacks
            overall_score = self._extract_overall_score(result_data)
            overall_explanation = self._extract_overall_explanation(result_data)
            function_name_match = self._extract_function_match(
                predicted_call, ground_truth_call
            )

            # Create result object
            result = ToolCallComparisonResult(
                predicted_call=predicted_call,
                ground_truth_call=ground_truth_call,
                function_name_match=function_name_match,
                function_name_score=1.0 if function_name_match else 0.0,
                parameter_results=[],  # Can be populated from custom schema
                overall_score=overall_score,
                overall_explanation=overall_explanation,
                strategy_used=ComparisonStrategy.LLM_JUDGE,
                metadata={
                    "custom_schema_response": result_data,
                    "custom_schema_used": True,
                    "execution_mode": "async_custom_schema",
                },  # Store full custom response
            )

            return result

        except Exception as e:
            logger.error(f"Custom schema comparison failed: {e}")
            # Fallback to standard comparison
            return await self.compare_tool_calls_async(
                predicted_call=predicted_call,
                ground_truth_call=ground_truth_call,
                conversation_history=conversation_history,
                tool_specs=tool_specs,
                custom_instructions=custom_instructions,
            )

    def _build_custom_system_prompt(
        self,
        custom_instructions: Optional[str] = None,
        custom_schema: Optional[str] = None,
    ) -> str:
        """Build system prompt with custom instructions and schema."""

        base_prompt = """You are an expert system for comparing function call parameters and tool calls. Your task is to evaluate the similarity and functional equivalence between predicted and ground truth function calls.

**EVALUATION PRINCIPLES**:
1. Focus on functional equivalence rather than literal matching
2. Consider context and user intent when making comparisons
3. Account for different representations of the same logical concepts
4. Provide detailed reasoning for your assessments

**SCORING GUIDELINES**:
- 1.0: Perfect functional equivalence
- 0.9-0.99: Semantically equivalent with minor differences
- 0.7-0.89: Mostly equivalent with some differences
- 0.5-0.69: Partially equivalent
- 0.3-0.49: Some similarity but significant differences
- 0.0-0.29: Not functionally equivalent
"""

        if custom_instructions:
            base_prompt += f"""

**CUSTOM EVALUATION INSTRUCTIONS**:
{custom_instructions}

IMPORTANT: Follow these custom instructions carefully. They take priority over general guidelines when there are conflicts.
"""

        if custom_schema:
            base_prompt += f"""

**RESPONSE FORMAT**:
You must respond using this exact JSON schema format:

{custom_schema}

Your response must be valid JSON that strictly follows this schema structure.
"""
        else:
            base_prompt += """

**RESPONSE FORMAT**:
Provide your response as a JSON object with detailed analysis and scoring.
"""

        return base_prompt

    def _build_custom_evaluation_prompt(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        tool_specs: List[Dict[str, Any]],
        custom_instructions: Optional[str] = None,
    ) -> str:
        """Build the user evaluation prompt with all context."""

        prompt = "**FUNCTION CALL COMPARISON TASK**\n\n"

        # Add function calls
        prompt += "**Predicted Function Call**:\n"
        prompt += f"```json\n{json.dumps(predicted_call, indent=2)}\n```\n\n"

        prompt += "**Ground Truth Function Call**:\n"
        prompt += f"```json\n{json.dumps(ground_truth_call, indent=2)}\n```\n\n"

        # Add tool specifications if provided
        if tool_specs:
            prompt += "**Tool Specifications**:\n"
            for spec in tool_specs:
                prompt += f"```json\n{json.dumps(spec, indent=2)}\n```\n"
            prompt += "\n"

        # Add conversation history if provided
        if conversation_history:
            prompt += "**Conversation Context**:\n"
            for msg in conversation_history:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                prompt += f"**{role.title()}**: {content}\n"
            prompt += "\n"

        # Add custom instructions if provided
        if custom_instructions:
            prompt += "**SPECIAL INSTRUCTIONS**:\n"
            prompt += f"{custom_instructions}\n\n"

        prompt += "Please evaluate these function calls and provide a detailed comparison following the specified schema format."

        return prompt

    def _extract_overall_score(self, result_data: Dict[str, Any]) -> float:
        """Extract overall score from custom schema response."""
        # Try different possible locations for the score
        score_paths = [
            ["overall_assessment", "overall_score"],
            ["overall_score"],
            ["score"],
            ["output"],
        ]

        for path in score_paths:
            value = result_data
            try:
                for key in path:
                    value = value[key]
                return float(value)
            except (KeyError, TypeError, ValueError):
                continue

        # Fallback: estimate from parameter scores
        param_scores = result_data.get("parameter_scores", {})
        if param_scores:
            scores = []
            for param_data in param_scores.values():
                if isinstance(param_data, dict) and "score" in param_data:
                    scores.append(float(param_data["score"]))
            if scores:
                return sum(scores) / len(scores)

        return 0.5  # Default fallback

    def _extract_overall_explanation(self, result_data: Dict[str, Any]) -> str:
        """Extract overall explanation from custom schema response."""
        explanation_paths = [
            ["overall_assessment", "summary"],
            ["overall_assessment", "explanation"],
            ["summary"],
            ["explanation"],
            ["reasoning"],
        ]

        for path in explanation_paths:
            value = result_data
            try:
                for key in path:
                    value = value[key]
                return str(value)
            except (KeyError, TypeError):
                continue

        return "Custom schema evaluation completed"

    def _extract_function_match(
        self, predicted_call: Dict[str, Any], ground_truth_call: Dict[str, Any]
    ) -> bool:
        """Extract function name match."""
        pred_name = predicted_call.get("function", {}).get(
            "name"
        ) or predicted_call.get("name")
        gt_name = ground_truth_call.get("function", {}).get(
            "name"
        ) or ground_truth_call.get("name")
        return pred_name == gt_name
