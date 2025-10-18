from typing import Any, Dict, List, Optional, Union
import asyncio
import logging

from llmevalkit.llm import LLMClient
from llmevalkit.llm.output_parser import ValidatingLLMClient
from .types import (
    ComparisonStrategy,
    ComparisonConfig,
    ToolCallComparisonResult,
)
from .comparators.exact_match import (
    ExactMatchComparator,
)
from .comparators.llm_judge import (
    LLMJudgeComparator,
)
from .comparators.fuzzy_string import (
    FuzzyStringComparator,
)
from .comparators.hybrid import (
    HybridComparator,
)

logger = logging.getLogger(__name__)


class ComparisonPipeline:
    """
    Enhanced pipeline for comparing predicted tool calls against ground truth.

    Features:
    - Proper handling of missing parameters with defaults
    - Integration with ValidatingLLMClient for structured outputs
    - Support for tool specifications to resolve parameter defaults
    - Multiple comparison strategies with intelligent fallbacks
    """

    def __init__(
        self,
        strategy: ComparisonStrategy = ComparisonStrategy.EXACT_MATCH,
        llm_client: Optional[Union[LLMClient, ValidatingLLMClient]] = None,
        config: Optional[ComparisonConfig] = None,
    ):
        # Use strategy from config if provided, otherwise use parameter
        if config:
            self.strategy = config.strategy
            self.config = config
        else:
            self.strategy = strategy
            self.config = ComparisonConfig(strategy=strategy)

        # Ensure we have ValidatingLLMClient for LLM-based strategies
        if self.strategy in [
            ComparisonStrategy.LLM_JUDGE,
            ComparisonStrategy.CODE_AGENT,
        ]:
            if not llm_client:
                raise ValueError(
                    f"LLM client required for {self.strategy.value} strategy"
                )

            # Wrap regular LLM client with mock wrapper for testing
            if not isinstance(llm_client, ValidatingLLMClient):
                # For testing purposes, create a simple mock wrapper
                class MockValidatingClient:
                    def __init__(self, base_client):
                        self._base_client = base_client

                    def generate(self, prompt, schema=None, **kwargs):
                        return self._base_client.generate(prompt, schema, **kwargs)

                    async def generate_async(self, prompt, schema=None, **kwargs):
                        if hasattr(self._base_client, "generate_async"):
                            return await self._base_client.generate_async(
                                prompt, schema, **kwargs
                            )
                        else:
                            return self.generate(prompt, schema, **kwargs)

                self.llm_client = MockValidatingClient(llm_client)
            else:
                self.llm_client = llm_client
        else:
            self.llm_client = llm_client  # Optional for non-LLM strategies

        # Initialize the appropriate comparator
        self.comparator = self._create_comparator()

    def _create_comparator(self):
        """Factory method to create the appropriate comparator."""
        if self.strategy == ComparisonStrategy.EXACT_MATCH:
            return ExactMatchComparator(self.config)
        elif self.strategy == ComparisonStrategy.NORMALIZED_MATCH:
            # Enhanced exact match with type normalization
            config = self.config.model_copy()
            config.normalize_types = True
            return ExactMatchComparator(config)
        elif self.strategy == ComparisonStrategy.FUZZY_STRING:
            return FuzzyStringComparator(self.config)
        elif self.strategy == ComparisonStrategy.LLM_JUDGE:
            return LLMJudgeComparator(self.config, self.llm_client)
        elif self.strategy == ComparisonStrategy.HYBRID:
            return HybridComparator(self.config, self.llm_client)
        # TODO: Implement remaining strategies
        # elif self.strategy == ComparisonStrategy.SEMANTIC_SIMILARITY:
        #     return SemanticSimilarityComparator(self.config)
        # elif self.strategy == ComparisonStrategy.CODE_AGENT:
        #     return CodeAgentComparator(self.config, self.llm_client)
        else:
            raise ValueError(f"Strategy {self.strategy} not implemented yet")

    def compare(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tool_specs: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> ToolCallComparisonResult:
        """
        Compare a predicted tool call against ground truth.

        Args:
            predicted_call: The tool call made by the agent
            ground_truth_call: The expected/correct tool call
            conversation_history: Context from the conversation
            tool_specs: Available tool specifications (OpenAI format)
            **kwargs: Additional comparison parameters

        Returns:
            ToolCallComparisonResult with detailed comparison analysis
        """
        try:
            result = self.comparator.compare_tool_calls(
                predicted_call=predicted_call,
                ground_truth_call=ground_truth_call,
                conversation_history=conversation_history,
                tool_specs=tool_specs,
            )

            # Add pipeline metadata
            result.metadata.update(
                {
                    "pipeline_strategy": self.strategy.value,
                    "config_used": self.config.dict(),
                    "llm_client_type": (
                        type(self.llm_client).__name__ if self.llm_client else None
                    ),
                }
            )

            return result

        except Exception as e:
            logger.error(f"Comparison failed: {e}")

            # Create fallback result
            return self._create_error_result(predicted_call, ground_truth_call, str(e))

    def _create_error_result(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        error_message: str,
    ) -> ToolCallComparisonResult:
        """Create a result object for error cases."""
        return ToolCallComparisonResult(
            predicted_call=predicted_call,
            ground_truth_call=ground_truth_call,
            function_name_match=False,
            function_name_score=0.0,
            parameter_results=[],
            overall_score=0.0,
            overall_explanation=f"Comparison failed: {error_message}",
            strategy_used=self.strategy,
            metadata={"error": error_message},
        )

    def batch_compare(
        self, comparisons: List[Dict[str, Any]], **kwargs
    ) -> List[ToolCallComparisonResult]:
        """
        Perform batch comparison of multiple tool call pairs.

        Args:
            comparisons: List of dicts with 'predicted', 'ground_truth', and optional context

        Returns:
            List of comparison results
        """
        results = []
        for i, comp_data in enumerate(comparisons):
            try:
                result = self.compare(
                    predicted_call=comp_data["predicted"],
                    ground_truth_call=comp_data["ground_truth"],
                    conversation_history=comp_data.get("conversation_history"),
                    tool_specs=comp_data.get("tool_specs"),
                    **kwargs,
                )
                result.metadata["batch_index"] = i
                results.append(result)

            except Exception as e:
                logger.error(f"Batch comparison failed for item {i}: {e}")
                error_result = self._create_error_result(
                    comp_data.get("predicted", {}),
                    comp_data.get("ground_truth", {}),
                    str(e),
                )
                error_result.metadata["batch_index"] = i
                results.append(error_result)

        return results

    async def compare_async(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tool_specs: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> ToolCallComparisonResult:
        """Async version of comparison (for LLM-based strategies)."""

        # Ensure custom_instructions is provided for compatibility
        if "custom_instructions" not in kwargs:
            kwargs["custom_instructions"] = " "

        # Check if comparator supports async
        if hasattr(self.comparator, "compare_tool_calls_async"):
            try:
                result = await self.comparator.compare_tool_calls_async(
                    predicted_call=predicted_call,
                    ground_truth_call=ground_truth_call,
                    conversation_history=conversation_history,
                    tool_specs=tool_specs,
                    **kwargs,
                )

                # Add pipeline metadata
                result.metadata.update(
                    {
                        "pipeline_strategy": self.strategy.value,
                        "config_used": self.config.dict(),
                        "execution_mode": "async",
                    }
                )

                return result

            except Exception as e:
                logger.error(f"Async comparison failed: {e}")
                return self._create_error_result(
                    predicted_call, ground_truth_call, str(e)
                )
        else:
            # Fallback to sync version in thread
            return await asyncio.to_thread(
                self.compare,
                predicted_call,
                ground_truth_call,
                conversation_history,
                tool_specs,
                **kwargs,
            )

    async def batch_compare_async(
        self,
        comparisons: List[Dict[str, Any]],
        max_concurrent: int = 10,
        progress_callback: Optional[callable] = None,
        **kwargs,
    ) -> List[ToolCallComparisonResult]:
        """
        Efficient async batch processing with concurrency control.

        Args:
            comparisons: List of comparison tasks
            max_concurrent: Maximum concurrent comparisons
            progress_callback: Optional callback for progress updates

        Returns:
            List of comparison results in original order
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def compare_with_semaphore(comp_data, index):
            async with semaphore:
                try:
                    result = await self.compare_async(
                        predicted_call=comp_data["predicted"],
                        ground_truth_call=comp_data["ground_truth"],
                        conversation_history=comp_data.get("conversation_history"),
                        tool_specs=comp_data.get("tool_specs"),
                        **kwargs,
                    )
                    result.metadata["batch_index"] = index

                    if progress_callback:
                        progress_callback(index + 1, len(comparisons))

                    return result

                except Exception as e:
                    logger.error(f"Async batch comparison failed for item {index}: {e}")
                    error_result = self._create_error_result(
                        comp_data.get("predicted", {}),
                        comp_data.get("ground_truth", {}),
                        str(e),
                    )
                    error_result.metadata["batch_index"] = index
                    return error_result

        # Create tasks for all comparisons
        tasks = [
            compare_with_semaphore(comp_data, i)
            for i, comp_data in enumerate(comparisons)
        ]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions that weren't caught
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = self._create_error_result(
                    comparisons[i].get("predicted", {}),
                    comparisons[i].get("ground_truth", {}),
                    str(result),
                )
                error_result.metadata["batch_index"] = i
                final_results.append(error_result)
            else:
                final_results.append(result)

        return final_results

    def get_comparison_summary(
        self, results: List[ToolCallComparisonResult]
    ) -> Dict[str, Any]:
        """Generate summary statistics for a batch of comparison results."""
        if not results:
            return {"error": "No results provided"}

        total = len(results)
        exact_matches = sum(1 for r in results if r.overall_score >= 0.95)
        semantic_matches = sum(1 for r in results if 0.8 <= r.overall_score < 0.95)
        partial_matches = sum(1 for r in results if 0.3 <= r.overall_score < 0.8)
        no_matches = sum(1 for r in results if r.overall_score < 0.3)

        avg_score = sum(r.overall_score for r in results) / total
        avg_confidence = (
            sum(
                sum(p.confidence for p in r.parameter_results)
                / len(r.parameter_results)
                for r in results
                if r.parameter_results
            )
            / sum(1 for r in results if r.parameter_results)
            if any(r.parameter_results for r in results)
            else 0.0
        )

        function_name_accuracy = (
            sum(1 for r in results if r.function_name_match) / total
        )

        return {
            "total_comparisons": total,
            "exact_matches": exact_matches,
            "semantic_matches": semantic_matches,
            "partial_matches": partial_matches,
            "no_matches": no_matches,
            "accuracy_breakdown": {
                "exact": exact_matches / total,
                "semantic": semantic_matches / total,
                "partial": partial_matches / total,
                "none": no_matches / total,
            },
            "average_overall_score": avg_score,
            "average_confidence": avg_confidence,
            "function_name_accuracy": function_name_accuracy,
            "strategy_used": self.strategy.value,
        }
