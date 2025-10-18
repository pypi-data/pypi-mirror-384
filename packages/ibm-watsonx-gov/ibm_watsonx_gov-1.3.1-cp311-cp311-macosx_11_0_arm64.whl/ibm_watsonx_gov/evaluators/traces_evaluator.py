# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

from typing import Annotated

from pydantic import Field, PrivateAttr

from ibm_watsonx_gov.entities.agentic_app import AgenticApp, Node
from ibm_watsonx_gov.entities.agentic_evaluation_result import AgenticEvaluationResult
from ibm_watsonx_gov.evaluators.base_evaluator import BaseEvaluator
from ibm_watsonx_gov.traces.trace_utils import TraceUtils
from ibm_watsonx_gov.traces.span_util import flatten_attributes
from ibm_watsonx_gov.utils.async_util import (gather_with_concurrency,
                                              run_in_event_loop)
from ibm_watsonx_gov.utils.python_utils import add_if_unique
from ibm_watsonx_gov.utils.aggregation_util import get_agentic_evaluation_result


class TracesEvaluator(BaseEvaluator):
    """
    The class to evaluate agentic applications based on the traces generated.
    """
    agentic_app: Annotated[AgenticApp,
                           Field(title="Agentic application configuration details",
                                 description="The agentic application configuration details.")]
    __nodes: Annotated[list[Node], PrivateAttr(default=[])]

    def evaluate(self, spans: list[dict], **kwargs) -> AgenticEvaluationResult:
        """
        Computes the agentic metrics based on the spans/traces provided as a list.

        Args:
            spans (list[AgentMetricResult]): The spans on which the metrics need to be computed.

        Returns:
            list[AgentMetricResult]: The computed metric results
        """
        metrics_result = []
        node_data = []
        messages_data = []
        mapping_data = []
        coros = []
        max_concurrency = kwargs.get("max_concurrency", 10)
        span_trees = TraceUtils.build_span_trees(
            spans=spans, agentic_app=self.agentic_app)
        for span_tree in span_trees:
            # Process only the spans that are associated with the agent application
            attrs = flatten_attributes(span_tree.span.attributes)
            if not attrs.get("traceloop.span.kind") == "workflow":
                continue

            # Append coroutine for data
            coros.append(
                TraceUtils.compute_metrics_from_trace_async_v2(
                    span_tree=span_tree, metrics_configuration=self.agentic_app.metrics_configuration, api_client=self.api_client, **kwargs
                )
            )
        # Run all coroutines in parallel with concurrency control
        results = run_in_event_loop(
            gather_with_concurrency,
            coros=coros,
            max_concurrency=max_concurrency)

      # Process results
        for mr, md, nd, mpd, ns in results:
            metrics_result.extend(mr)
            messages_data.append(md)
            node_data.extend(nd)
            mapping_data.append(mpd)

            for n in ns:
                add_if_unique(n, self.__nodes, ["name", "func_name"], [
                              "foundation_models"])

        result = get_agentic_evaluation_result(
            metrics_result=metrics_result, nodes=self.__nodes)

        result.messages_data = messages_data
        result.nodes_data = node_data
        result.metrics_mapping_data = mapping_data
        return result
