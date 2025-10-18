from .types import (
    ComparisonStrategy,
    ComparisonConfig,
    ParameterComparisonResult,
    BulkParameterComparisonResult,
    ToolCallComparisonResult,
    ParameterStatus,
    ToolSpecFunction,
    ToolSpecParameter,
)

from .pipeline import ComparisonPipeline

from .comparators.base import BaseComparator
from .comparators.exact_match import ExactMatchComparator
from .comparators.fuzzy_string import FuzzyStringComparator
from .comparators.llm_judge import LLMJudgeComparator
from .comparators.hybrid import HybridComparator

# Code Agent Comparator (requires LangGraph)
try:
    from .comparators.code_agent import CodeAgentComparator

    _code_agent_available = True
except ImportError:
    _code_agent_available = False

    # Create placeholder class to avoid import errors
    class CodeAgentComparator:
        def __init__(self):
            raise ImportError(
                "Code Agent dependencies not available. Install: pip install langgraph langchain-core langchain-experimental"
            )


from .utils import (
    calculate_string_similarity,
    deep_compare_objects,
    validate_tool_call_structure,
)

__all__ = [
    # Core types
    "ComparisonStrategy",
    "ComparisonConfig",
    "ParameterComparisonResult",
    "BulkParameterComparisonResult",
    "ToolCallComparisonResult",
    "ParameterStatus",
    "ToolSpecFunction",
    "ToolSpecParameter",
    # Main pipeline
    "ComparisonPipeline",
    # Comparators
    "BaseComparator",
    "ExactMatchComparator",
    "FuzzyStringComparator",
    "LLMJudgeComparator",
    "HybridComparator",
    "CodeAgentComparator",
    # Utilities
    "calculate_string_similarity",
    "deep_compare_objects",
    "validate_tool_call_structure",
    # Testing
    "ComparisonTester",
    "TestDataGenerator",
    "MockLLMClient",
]


# Quick usage example
def quick_compare(
    predicted_call, ground_truth_call, strategy=ComparisonStrategy.EXACT_MATCH
):
    """
    Quick comparison function for simple use cases.

    Args:
        predicted_call: The predicted tool call
        ground_truth_call: The ground truth tool call
        strategy: Comparison strategy to use

    Returns:
        ToolCallComparisonResult: Comparison result
    """
    config = ComparisonConfig(strategy=strategy)
    pipeline = ComparisonPipeline(config=config)
    return pipeline.compare(predicted_call, ground_truth_call)
