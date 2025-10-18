from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field
from enum import Enum


class ComparisonStrategy(str, Enum):
    EXACT_MATCH = "exact_match"
    NORMALIZED_MATCH = "normalized_match"  # Handle type conversions
    FUZZY_STRING = "fuzzy_string"  # String similarity
    SEMANTIC_SIMILARITY = "semantic_similarity"  # Embeddings-based
    LLM_JUDGE = "llm_judge"
    CODE_AGENT = "code_agent"
    HYBRID = "hybrid"


class ParameterStatus(str, Enum):
    BOTH_PRESENT = "both_present"
    PRED_MISSING = "predicted_missing"
    GT_MISSING = "ground_truth_missing"
    BOTH_MISSING = "both_missing"
    PRED_DEFAULT = "predicted_uses_default"
    GT_DEFAULT = "ground_truth_uses_default"
    BOTH_DEFAULT = "both_use_default"


class ParameterComparisonResult(BaseModel):
    parameter_name: str
    predicted_value: Any
    ground_truth_value: Any
    # Add actual resolved values (after applying defaults)
    predicted_resolved_value: Any
    ground_truth_resolved_value: Any
    parameter_status: ParameterStatus
    comparison_strategy: ComparisonStrategy
    score: float = Field(ge=0.0, le=1.0)  # 0.0 - 1.0
    explanation: str
    evidence: Optional[str] = None
    is_match: bool
    confidence: float = Field(ge=0.0, le=1.0)
    error_type: Optional[str] = None
    # Tool spec information
    parameter_definition: Optional[Dict[str, Any]] = None
    is_required: bool = False
    default_value: Optional[Any] = None


class BulkParameterComparisonResult(BaseModel):
    """Result for bulk parameter comparison in a single LLM prompt."""

    function_name: str
    parameter_results: List[ParameterComparisonResult]
    overall_parameter_score: float = Field(ge=0.0, le=1.0)
    overall_explanation: str = ""
    comparison_strategy: ComparisonStrategy
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ParameterWeight(BaseModel):
    name: str
    weight: float = Field(default=1.0, ge=0.0)
    is_critical: bool = (
        False  # If critical param fails, overall score heavily penalized
    )


class ToolCallComparisonResult(BaseModel):
    predicted_call: Dict[str, Any]
    ground_truth_call: Dict[str, Any]
    function_name_match: bool
    function_name_score: float = Field(ge=0.0, le=1.0)
    parameter_results: List[ParameterComparisonResult]
    overall_score: float = Field(ge=0.0, le=1.0)
    overall_explanation: str
    strategy_used: Union[ComparisonStrategy, List[ComparisonStrategy]]
    # Enhanced metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    missing_required_params: List[str] = Field(default_factory=list)
    unexpected_params: List[str] = Field(default_factory=list)


class ComparisonConfig(BaseModel):
    strategy: ComparisonStrategy
    parameters_to_compare: Optional[List[str]] = (
        None  # If None, compare all including defaults
    )
    strategy_config: Dict[str, Any] = Field(default_factory=dict)
    weight_function_name: float = Field(default=0.3, ge=0.0, le=1.0)
    weight_parameters: float = Field(default=0.7, ge=0.0, le=1.0)
    normalize_scores: bool = True

    # Enhanced parameter handling
    parameter_weights: List[ParameterWeight] = Field(default_factory=list)
    critical_parameter_penalty: float = Field(default=0.5, ge=0.0, le=1.0)
    include_default_parameters: bool = (
        True  # Whether to compare parameters with default values
    )
    missing_parameter_penalty: float = Field(
        default=0.2, ge=0.0, le=1.0
    )  # Penalty for missing non-required params

    # LLM Judge specific settings
    llm_bulk_comparison: bool = Field(
        default=False,
        description="If True, compare all parameters in one LLM prompt instead of individual prompts",
    )

    # Type normalization settings
    normalize_types: bool = True
    string_similarity_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    numeric_tolerance: float = Field(default=0.01, ge=0.0)

    # LLM settings
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    llm_max_retries: int = Field(default=3, ge=1)
    llm_timeout: float = Field(default=30.0, gt=0.0)

    # Fallback strategy
    fallback_strategy: ComparisonStrategy = ComparisonStrategy.EXACT_MATCH


class FunctionCallInput(BaseModel):
    """Input structure for LLM judge evaluation."""

    expected: Dict[str, Any]
    actual: Dict[str, Any]
    context: Optional[str] = None


class ToolSpecParameter(BaseModel):
    """Represents a parameter definition from tool specification."""

    name: str
    type: str
    description: Optional[str] = None
    required: bool = False
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None
    format: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None  # For object types


class ToolSpecFunction(BaseModel):
    """Represents a function definition from tool specification."""

    name: str
    description: Optional[str] = None
    parameters: List[ToolSpecParameter] = Field(default_factory=list)

    @classmethod
    def from_openai_spec(cls, spec: Dict[str, Any]) -> "ToolSpecFunction":
        """Create from OpenAI function specification format."""
        func_def = spec.get("function", {})
        params_schema = func_def.get("parameters", {})
        properties = params_schema.get("properties", {})
        required = set(params_schema.get("required", []))

        parameters = []
        for param_name, param_def in properties.items():
            parameters.append(
                ToolSpecParameter(
                    name=param_name,
                    type=param_def.get("type", "string"),
                    description=param_def.get("description"),
                    required=param_name in required,
                    default=param_def.get("default"),
                    enum=param_def.get("enum"),
                    format=param_def.get("format"),
                    properties=param_def.get("properties"),
                )
            )

        return cls(
            name=func_def.get("name", ""),
            description=func_def.get("description"),
            parameters=parameters,
        )
