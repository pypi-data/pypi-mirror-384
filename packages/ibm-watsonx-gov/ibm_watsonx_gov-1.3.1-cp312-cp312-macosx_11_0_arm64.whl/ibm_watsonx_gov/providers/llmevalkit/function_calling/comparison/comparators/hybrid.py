from typing import Any, Dict, Optional, List
import logging

from .base import BaseComparator
from .exact_match import ExactMatchComparator
from .fuzzy_string import FuzzyStringComparator
from .llm_judge import LLMJudgeComparator
from ..types import (
    ParameterComparisonResult,
    ComparisonStrategy,
    ParameterStatus,
    ComparisonConfig,
)

# Import code agent conditionally to avoid dependency issues
try:
    from .code_agent import CodeAgentComparator

    CODE_AGENT_AVAILABLE = True
except ImportError:
    CODE_AGENT_AVAILABLE = False

logger = logging.getLogger(__name__)


class HybridComparator(BaseComparator):
    """
    Hybrid comparator that uses multiple strategies and picks the best result.

    Strategy order:
    1. Exact match (if perfect match found)
    2. Fuzzy string similarity (for near matches)
    3. LLM judge (for semantic understanding) - now with enhanced capabilities
    4. Code agent (for complex programmatic analysis) - if available

    Enhanced LLM Judge capabilities:
    - Supports custom instructions for specialized evaluation scenarios
    - Supports custom schemas for tailored response formats
    - Both sync and async operation modes
    - Bulk and individual parameter comparison modes
    """

    def __init__(self, config: ComparisonConfig, llm_client=None):
        super().__init__(config)
        self.llm_client = llm_client

        # Initialize sub-comparators
        self.exact_comparator = ExactMatchComparator(config)
        self.fuzzy_comparator = FuzzyStringComparator(config)

        # Only initialize LLM comparator if client is available
        self.llm_comparator = None
        if llm_client:
            try:
                self.llm_comparator = LLMJudgeComparator(config, llm_client)
            except Exception as e:
                logger.warning(f"Failed to initialize LLM comparator: {e}")

        # Only initialize Code Agent comparator if available and client provided
        self.code_agent_comparator = None
        if CODE_AGENT_AVAILABLE and llm_client:
            try:
                self.code_agent_comparator = CodeAgentComparator(config, llm_client)
            except Exception as e:
                logger.warning(f"Failed to initialize Code Agent comparator: {e}")

    def compare_parameter(
        self,
        param_name: str,
        predicted_value: Any,
        ground_truth_value: Any,
        context: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
        custom_schema: Optional[Dict[str, Any]] = None,
    ) -> ParameterComparisonResult:

        results = []
        strategies_used = []

        # 1. Try exact match first
        try:
            exact_result = self.exact_comparator.compare_parameter(
                param_name,
                predicted_value,
                ground_truth_value,
                context,
                custom_instructions,
            )
            results.append(exact_result)
            strategies_used.append(ComparisonStrategy.EXACT_MATCH)

            # If exact match is perfect, return it
            if exact_result.score >= 0.95:
                exact_result.comparison_strategy = ComparisonStrategy.HYBRID
                return exact_result

        except Exception as e:
            logger.warning(f"Exact match comparison failed: {e}")

        # 2. Try fuzzy string matching
        try:
            fuzzy_result = self.fuzzy_comparator.compare_parameter(
                param_name,
                predicted_value,
                ground_truth_value,
                context,
                custom_instructions,
            )
            results.append(fuzzy_result)
            strategies_used.append(ComparisonStrategy.FUZZY_STRING)

        except Exception as e:
            logger.warning(f"Fuzzy string comparison failed: {e}")

        # 3. Try LLM judge if available and other methods haven't given high confidence
        if self.llm_comparator and (not results or max(r.score for r in results) < 0.8):
            try:
                llm_result = self.llm_comparator.compare_parameter(
                    param_name,
                    predicted_value,
                    ground_truth_value,
                    context,
                    custom_instructions,
                    custom_schema,
                )
                results.append(llm_result)
                strategies_used.append(ComparisonStrategy.LLM_JUDGE)

            except Exception as e:
                logger.warning(f"LLM judge comparison failed: {e}")

        # 4. Try Code Agent if available and other methods haven't given high confidence
        if self.code_agent_comparator and (
            not results or max(r.score for r in results) < 0.85
        ):
            try:
                # Code agent typically doesn't support custom_schema, so pass other params
                code_result = self.code_agent_comparator.compare_parameter(
                    param_name,
                    predicted_value,
                    ground_truth_value,
                    context,
                    custom_instructions,
                )
                results.append(code_result)
                strategies_used.append(ComparisonStrategy.CODE_AGENT)

            except Exception as e:
                logger.warning(f"Code agent comparison failed: {e}")

        # Select the best result
        if not results:
            # Fallback to basic exact match
            return ParameterComparisonResult(
                parameter_name=param_name,
                predicted_value=predicted_value,
                ground_truth_value=ground_truth_value,
                predicted_resolved_value=predicted_value,
                ground_truth_resolved_value=ground_truth_value,
                parameter_status=(
                    context.get("parameter_status", ParameterStatus.BOTH_PRESENT)
                    if context
                    else ParameterStatus.BOTH_PRESENT
                ),
                comparison_strategy=ComparisonStrategy.HYBRID,
                score=0.0,
                explanation="All comparison strategies failed",
                is_match=False,
                confidence=0.1,
                error_type="comparison_failed",
            )

        # Choose best result based on combination of score and confidence
        best_result = self._select_best_result(results, strategies_used)

        # Update the strategy to reflect hybrid approach
        best_result.comparison_strategy = ComparisonStrategy.HYBRID

        # Enhance explanation with strategy information
        strategy_names = [s.value for s in strategies_used]
        best_result.explanation += (
            f" (Hybrid strategies used: {', '.join(strategy_names)})"
        )

        return best_result

    def _select_best_result(
        self,
        results: List[ParameterComparisonResult],
        strategies: List[ComparisonStrategy],
    ) -> ParameterComparisonResult:
        """Select the best result from multiple comparison strategies."""

        if len(results) == 1:
            return results[0]

        # Calculate weighted scores
        strategy_weights = {
            ComparisonStrategy.EXACT_MATCH: 1.0,  # Highest priority for exact matches
            ComparisonStrategy.CODE_AGENT: 0.95,  # Very high priority for code analysis
            ComparisonStrategy.LLM_JUDGE: 0.9,  # High priority for LLM understanding
            ComparisonStrategy.FUZZY_STRING: 0.7,  # Medium priority for fuzzy matching
        }

        best_result = None
        best_weighted_score = -1

        for result, strategy in zip(results, strategies):
            # Weighted score combines result score, confidence, and strategy preference
            weight = strategy_weights.get(strategy, 0.5)
            weighted_score = (result.score * 0.6 + result.confidence * 0.2) * weight

            # Bonus for exact matches
            if result.score >= 0.95:
                weighted_score += 0.1

            # Bonus for high confidence
            if result.confidence >= 0.9:
                weighted_score += 0.05

            if weighted_score > best_weighted_score:
                best_weighted_score = weighted_score
                best_result = result

        return best_result or results[0]

    def compare_function_name(
        self,
        predicted_name: str,
        ground_truth_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Hybrid function name comparison."""

        # Try exact match first
        exact_score = self.exact_comparator.compare_function_name(
            predicted_name, ground_truth_name, context
        )

        if exact_score >= 0.95:
            return exact_score

        # Try fuzzy matching
        fuzzy_score = self.fuzzy_comparator.compare_function_name(
            predicted_name, ground_truth_name, context
        )

        # Try LLM if available and fuzzy score is not high
        if self.llm_comparator and fuzzy_score < 0.8:
            try:
                llm_score = self.llm_comparator.compare_function_name(
                    predicted_name, ground_truth_name, context
                )
                # Take the higher of fuzzy and LLM scores
                fuzzy_score = max(fuzzy_score, llm_score)
            except Exception as e:
                logger.warning(f"LLM function name comparison failed: {e}")

        # Try Code Agent if available and current score is not high
        if self.code_agent_comparator and fuzzy_score < 0.85:
            try:
                code_score = self.code_agent_comparator.compare_function_name(
                    predicted_name, ground_truth_name, context
                )
                # Take the highest score
                fuzzy_score = max(fuzzy_score, code_score)
            except Exception as e:
                logger.warning(f"Code agent function name comparison failed: {e}")

        return fuzzy_score

    async def compare_parameter_async(
        self,
        param_name: str,
        predicted_value: Any,
        ground_truth_value: Any,
        context: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
        custom_schema: Optional[Dict[str, Any]] = None,
    ) -> ParameterComparisonResult:
        """Async hybrid parameter comparison with all enhanced features."""

        results = []
        strategies_used = []

        # 1. Try exact match first
        try:
            exact_result = self.exact_comparator.compare_parameter(
                param_name,
                predicted_value,
                ground_truth_value,
                context,
                custom_instructions,
            )
            results.append(exact_result)
            strategies_used.append(ComparisonStrategy.EXACT_MATCH)

            # If exact match is perfect, return it
            if exact_result.score >= 0.95:
                exact_result.comparison_strategy = ComparisonStrategy.HYBRID
                return exact_result

        except Exception as e:
            logger.warning(f"Exact match comparison failed: {e}")

        # 2. Try fuzzy string matching
        try:
            fuzzy_result = self.fuzzy_comparator.compare_parameter(
                param_name,
                predicted_value,
                ground_truth_value,
                context,
                custom_instructions,
            )
            results.append(fuzzy_result)
            strategies_used.append(ComparisonStrategy.FUZZY_STRING)

        except Exception as e:
            logger.warning(f"Fuzzy string comparison failed: {e}")

        # 3. Try LLM judge async if available and other methods haven't given high confidence
        if self.llm_comparator and (not results or max(r.score for r in results) < 0.8):
            try:
                llm_result = await self.llm_comparator.compare_parameter_async(
                    param_name,
                    predicted_value,
                    ground_truth_value,
                    context,
                    custom_instructions,
                    custom_schema,
                )
                results.append(llm_result)
                strategies_used.append(ComparisonStrategy.LLM_JUDGE)

            except Exception as e:
                logger.warning(f"Async LLM judge comparison failed: {e}")

        # 4. Try Code Agent async if available and other methods haven't given high confidence
        if self.code_agent_comparator and (
            not results or max(r.score for r in results) < 0.85
        ):
            try:
                # Check if code agent has async support
                if hasattr(self.code_agent_comparator, "compare_parameter_async"):
                    code_result = (
                        await self.code_agent_comparator.compare_parameter_async(
                            param_name,
                            predicted_value,
                            ground_truth_value,
                            context,
                            custom_instructions,
                        )
                    )
                else:
                    # Fallback to sync version
                    code_result = self.code_agent_comparator.compare_parameter(
                        param_name,
                        predicted_value,
                        ground_truth_value,
                        context,
                        custom_instructions,
                    )
                results.append(code_result)
                strategies_used.append(ComparisonStrategy.CODE_AGENT)

            except Exception as e:
                logger.warning(f"Async code agent comparison failed: {e}")

        # Select the best result
        if not results:
            # Fallback to basic exact match
            return ParameterComparisonResult(
                parameter_name=param_name,
                predicted_value=predicted_value,
                ground_truth_value=ground_truth_value,
                predicted_resolved_value=predicted_value,
                ground_truth_resolved_value=ground_truth_value,
                parameter_status=(
                    context.get("parameter_status", ParameterStatus.BOTH_PRESENT)
                    if context
                    else ParameterStatus.BOTH_PRESENT
                ),
                comparison_strategy=ComparisonStrategy.HYBRID,
                score=0.0,
                explanation="All async comparison strategies failed",
                is_match=False,
                confidence=0.1,
                error_type="comparison_failed",
            )

        # Choose best result based on combination of score and confidence
        best_result = self._select_best_result(results, strategies_used)

        # Update the strategy to reflect hybrid approach
        best_result.comparison_strategy = ComparisonStrategy.HYBRID

        # Enhance explanation with strategy information
        strategy_names = [s.value for s in strategies_used]
        best_result.explanation += (
            f" (Async hybrid strategies used: {', '.join(strategy_names)})"
        )

        return best_result

    async def compare_tool_calls_async(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tool_specs: Optional[List[Dict[str, Any]]] = None,
        custom_instructions: Optional[str] = None,
        custom_schema: Optional[str] = None,
    ) -> Any:
        """Async hybrid tool call comparison with enhanced LLM Judge features."""

        # For tool call level comparison, prioritize LLM-based approaches

        # Try enhanced LLM judge with custom schema first if available
        if self.llm_comparator and custom_schema:
            try:
                return await self.llm_comparator.compare_tool_calls_with_custom_schema(
                    predicted_call,
                    ground_truth_call,
                    conversation_history,
                    tool_specs,
                    custom_instructions,
                    custom_schema,
                )
            except Exception as e:
                logger.warning(f"Custom schema LLM comparison failed: {e}")

        # Try standard async LLM judge
        if self.llm_comparator:
            try:
                return await self.llm_comparator.compare_tool_calls_async(
                    predicted_call,
                    ground_truth_call,
                    conversation_history,
                    tool_specs,
                    custom_instructions,
                )
            except Exception as e:
                logger.warning(f"Async LLM tool call comparison failed: {e}")

        # Try code agent async if available
        if self.code_agent_comparator:
            try:
                if hasattr(self.code_agent_comparator, "compare_tool_calls_async"):
                    return await self.code_agent_comparator.compare_tool_calls_async(
                        predicted_call,
                        ground_truth_call,
                        conversation_history,
                        tool_specs,
                        custom_instructions,
                    )
                else:
                    # Fallback to sync version
                    return self.code_agent_comparator.compare_tool_calls(
                        predicted_call,
                        ground_truth_call,
                        conversation_history,
                        tool_specs,
                        custom_instructions,
                    )
            except Exception as e:
                logger.warning(f"Async code agent tool call comparison failed: {e}")

        # Fallback to base class comparison
        return await super().compare_tool_calls_async(
            predicted_call, ground_truth_call, conversation_history, tool_specs
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
        """Sync hybrid tool call comparison with enhanced LLM Judge features."""

        # For tool call level comparison, prioritize LLM-based approaches

        # Try standard LLM judge first
        if self.llm_comparator:
            try:
                return self.llm_comparator.compare_tool_calls(
                    predicted_call,
                    ground_truth_call,
                    conversation_history,
                    tool_specs,
                    custom_instructions,
                    custom_schema,
                )
            except Exception as e:
                logger.warning(f"LLM tool call comparison failed: {e}")

        # Try code agent if available
        if self.code_agent_comparator:
            try:
                return self.code_agent_comparator.compare_tool_calls(
                    predicted_call,
                    ground_truth_call,
                    conversation_history,
                    tool_specs,
                    custom_instructions,
                )
            except Exception as e:
                logger.warning(f"Code agent tool call comparison failed: {e}")

        # Fallback to base class comparison
        return super().compare_tool_calls(
            predicted_call, ground_truth_call, conversation_history, tool_specs
        )
