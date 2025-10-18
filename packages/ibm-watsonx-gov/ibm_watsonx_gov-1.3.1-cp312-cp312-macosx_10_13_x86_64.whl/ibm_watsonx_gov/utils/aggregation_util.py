# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

import copy
from collections import defaultdict
from typing import List

import numpy as np
import pandas as pd

from ibm_watsonx_gov.entities.agentic_app import Node
from ibm_watsonx_gov.entities.agentic_evaluation_result import \
    AgenticEvaluationResult
from ibm_watsonx_gov.entities.enums import MetricGroup, MetricValueType
from ibm_watsonx_gov.entities.evaluation_result import (
    AgentMetricResult, AggregateAgentMetricResult, RecordMetricResult)
from ibm_watsonx_gov.entities.metric_threshold import MetricThreshold
from ibm_watsonx_gov.metrics.llm_validation.llm_validation_metric import \
    LLMValidationMetric
from ibm_watsonx_gov.utils.gov_sdk_logger import GovSDKLogger

logger = GovSDKLogger.get_logger(__name__)


def get_aggregated_thresholds(metric_results: List[AgentMetricResult]) -> List[MetricThreshold]:
    """
    Aggregates thresholds from a list of AgentMetricResult objects.

    This function takes a list of AgentMetricResult objects and returns a list of MetricThreshold objects.
    It aggregates thresholds if all AgentMetricResult objects have identical sets of thresholds.
    If the list is empty, it returns an empty list. If there's only one AgentMetricResult, it returns its thresholds.

    Parameters:
    metric_results (List[AgentMetricResult]): A list of AgentMetricResult objects.

    Returns:
    List[MetricThreshold]: A list of MetricThreshold objects, either aggregated or an empty list if thresholds do not match.
    """

    if not metric_results:
        return []

    if len(metric_results) == 1:
        return metric_results[0].thresholds

    first_thresholds = set(metric_results[0].thresholds)
    for metric_result in metric_results[1:]:
        if first_thresholds != set(metric_result.thresholds):
            logger.warning(
                f"Did not get matching thresholds for {metric_results[0].name} metric. Not aggregating.")
            return []

    return metric_results[0].thresholds


def __get_aggregation_result(metric_results: List[AgentMetricResult]) -> AggregateAgentMetricResult | None:
    valid_values = [v.value for v in metric_results if v.value is not None]

    if not valid_values:
        return None

    has_string = any(isinstance(value, str) for value in valid_values)
    first_metric_result = metric_results[0]

    if not has_string:
        # Case where all the metric values are numeric
        mean = sum(valid_values) / len(valid_values)

        # Calculate percentiles if we have enough data points
        percentiles = None

        if len(valid_values) > 1:
            # Calculate all percentiles in a single call
            percentile_values = np.percentile(
                valid_values, [25, 50, 75, 90, 95, 99])
            percentiles = {
                "25": percentile_values[0],
                "50": percentile_values[1],
                "75": percentile_values[2],
                "90": percentile_values[3],
                "95": percentile_values[4],
                "99": percentile_values[5]
            }

        combined_thresholds = get_aggregated_thresholds(
            metric_results=metric_results)

        return AggregateAgentMetricResult(name=first_metric_result.name,
                                          value_type=first_metric_result.value_type,
                                          display_name=first_metric_result.display_name,
                                          thresholds=combined_thresholds,
                                          method=first_metric_result.method,
                                          provider=first_metric_result.provider,
                                          node_name=first_metric_result.node_name,
                                          applies_to=first_metric_result.applies_to,
                                          group=first_metric_result.group,
                                          value=mean,
                                          min=min(valid_values),
                                          max=max(valid_values),
                                          count=len(valid_values),
                                          percentiles=percentiles,
                                          individual_results=metric_results)

    value_counts = pd.Series(valid_values).astype(str).value_counts().to_dict()
    # Case where some of the metric values are string.
    return AggregateAgentMetricResult(name=first_metric_result.name,
                                      value_type=MetricValueType.CATEGORICAL.value,
                                      display_name=first_metric_result.display_name,
                                      method=first_metric_result.method,
                                      provider=first_metric_result.provider,
                                      node_name=first_metric_result.node_name,
                                      applies_to=first_metric_result.applies_to,
                                      group=first_metric_result.group,
                                      thresholds=first_metric_result.thresholds,
                                      value=value_counts,
                                      count=len(metric_results),
                                      unique=len(value_counts),
                                      individual_results=metric_results)


def __compute_aggregated_metrics_results(metrics_result: List[AgentMetricResult],
                                         nodes: List[Node],
                                         include_individual_results: bool = True) -> List[AggregateAgentMetricResult]:

    nodes_result_group, message_result_group, conversation_result_map = __get_grouped_metrics_result(
        metrics_result)

    aggregated_results = []
    aggregated_results.extend(__get_aggregated_node_metrics(
        include_individual_results, nodes, nodes_result_group))
    aggregated_results.extend(
        __get_aggregated_metrics(message_result_group))
    aggregated_results.extend(
        __get_aggregated_metrics(conversation_result_map))

    return aggregated_results


def __get_aggregated_metrics(message_results):
    aggregated_results = []
    # Aggregate message or conversation level metrics
    for values in list(message_results.values()):
        aggregated_result = __get_aggregation_result(
            values)
        if aggregated_result:
            aggregated_results.append(aggregated_result)
    return aggregated_results


def __get_grouped_metrics_result(metrics_result):
    """
    Group the metrics results based on node and message.
    """
    nodes_result_map, message_result_map = {}, {}
    conversation_result_map = defaultdict(list)
    conversation_metrics = defaultdict(lambda: defaultdict(float))
    for mr in metrics_result:
        key = mr.name+"_"+mr.method if mr.method else mr.name
        if mr.applies_to == "node":
            if mr.node_name in nodes_result_map:
                if key in nodes_result_map[mr.node_name]:
                    nodes_result_map[mr.node_name][key].append(mr)
                else:
                    nodes_result_map[mr.node_name][key] = [mr]
            else:
                nodes_result_map[mr.node_name] = {
                    key: [mr]
                }
        elif mr.applies_to == "message":
            if key in message_result_map:
                message_result_map[key].append(mr)
            else:
                message_result_map[key] = [mr]
            if key in ("duration", "cost", "input_token_count", "output_token_count"):
                conversation_metrics[mr.conversation_id][key] += mr.value
    for conversation_id, metric_value in conversation_metrics.items():
        for metric, value in metric_value.items():
            conversation_result_map[metric].append(AgentMetricResult(name=metric,
                                                                     value=value,
                                                                     display_name=metric,
                                                                     group=MetricGroup.PERFORMANCE.value if metric == "duration" else MetricGroup.USAGE.value,
                                                                     message_id=None,
                                                                     applies_to="conversation",
                                                                     conversation_id=conversation_id))

    return nodes_result_map, message_result_map, dict(conversation_result_map)


def __get_aggregated_node_metrics(include_individual_results, nodes, nodes_results):
    aggregated_results = []

    # Create node metrics dict for easy access to metrics
    node_to_metrics = {}
    for n in nodes:
        mts = {}
        for mc in n.metrics_configurations:
            for m in mc.metrics:
                mts[m.id] = m
        node_to_metrics[n.name] = mts

    # Aggregate node level metrics
    for node, node_metrics in nodes_results.items():
        for metric_key, values in node_metrics.items():
            aggregated_result = None
            metric_obj = node_to_metrics.get(node, {}).get(metric_key)

            if isinstance(metric_obj, LLMValidationMetric):
                # convert metrics result from AgentMetricResult to RecordMetricResult used by the metric
                aggregated_result = __get_llm_validation_metric_aggregation_result(
                    include_individual_results, values, metric_obj)
            else:
                aggregated_result = __get_aggregation_result(
                    values)
            if aggregated_result:
                aggregated_results.append(aggregated_result)
    return aggregated_results


def __get_llm_validation_metric_aggregation_result(include_individual_results, values, metric_obj):
    record_level_metrics = [RecordMetricResult(
        **v.__dict__, record_id=v.message_id) for v in values]
    aggregated_result = metric_obj.get_aggregated_results_from_individual_results(
        record_level_metrics)

    # convert updated record results to AgentMetricResult
    updated_record_level_metrics = aggregated_result.record_level_metrics
    agent_individual_results = []
    for record_result, agent_result in zip(updated_record_level_metrics, values):
        args = {**agent_result.__dict__,
                **record_result.__dict__}
        agent_individual_results.append(
            AgentMetricResult(**args))

    if aggregated_result:
        # convert AggregateMetricResult to AggregateAgentMetricResult
        mv = values[0]

        # Calculate percentiles if we have enough data points
        percentiles = None

        if len(agent_individual_results) > 1:
            # Extract values for percentile calculation
            valid_values = [
                r.value for r in agent_individual_results if r.value is not None]
            if valid_values and all(isinstance(v, (int, float)) for v in valid_values):
                # Calculate all percentiles in a single call
                percentile_values = np.percentile(
                    valid_values, [25, 50, 75, 90, 95, 99])

                percentiles = {
                    "25": percentile_values[0],
                    "50": percentile_values[1],
                    "75": percentile_values[2],
                    "90": percentile_values[3],
                    "95": percentile_values[4],
                    "99": percentile_values[5]
                }

        aggregated_result = AggregateAgentMetricResult(
            name=mv.name,
            method=mv.method,
            provider=mv.provider,
            node_name=mv.node_name,
            applies_to=mv.applies_to,
            group=mv.group,
            value=aggregated_result.mean,
            min=aggregated_result.min,
            max=aggregated_result.max,
            count=aggregated_result.total_records,
            percentiles=percentiles,
            individual_results=copy.deepcopy(
                agent_individual_results) if include_individual_results else [],
            additional_info=copy.deepcopy(
                aggregated_result.additional_info)
        )
    return aggregated_result


def get_agentic_evaluation_result(metrics_result: list[AgentMetricResult], nodes: list[Node] = []) -> AgenticEvaluationResult:
    aggregated_metrics_results = __compute_aggregated_metrics_results(
        metrics_result, nodes)
    metrics_result = []
    for amr in aggregated_metrics_results:
        metrics_result.extend(amr.individual_results)

    return AgenticEvaluationResult(metrics_results=metrics_result,
                                   aggregated_metrics_results=aggregated_metrics_results)


def get_summaries(individual_metric_values: list):
    """
    Calculates statistical summaries for a list of numeric metric values.

    Args:
        individual_metric_values (list): A list of numeric values representing individual
                                       metrics. May contain None values which will be filtered out.

    Returns:
        dict: A dictionary containing the following statistical summaries:
            - "metric_value" (float): Mean of the values (same as "mean")
            - "mean" (float): Arithmetic mean of the values
            - "min" (float): Minimum value in the dataset
            - "max" (float): Maximum value in the dataset
            - "std" (float): Standard deviation of the values
            - "percentiles" (dict): Dictionary containing percentile values with keys:
                - "25": 25th percentile of the values
                - "50": 50th percentile (median) of the values
                - "75": 75th percentile of the values
                - "90": 90th percentile of the values
                - "95": 95th percentile of the values
                - "99": 99th percentile of the values

            If input is empty or contains only None values, returns:
            {"metric_value": 0, "mean": 0, "min": 0, "max": 0, "std": 0,
             "percentiles": {"25": 0, "50": 0, "75": 0, "90": 0, "95": 0, "99": 0}}
    """
    individual_metric_values = [
        ele for ele in individual_metric_values if ele is not None]

    if individual_metric_values is None or len(individual_metric_values) == 0:
        return {
            "metric_value": 0,
            "mean": 0,
            "min": 0,
            "max": 0,
            "std": 0,
            "percentiles": {
                "25": 0,
                "50": 0,
                "75": 0,
                "90": 0,
                "95": 0,
                "99": 0
            }
        }
    else:
        # Calculate all percentiles in a single call
        percentile_values = np.percentile(
            individual_metric_values, [25, 50, 75, 90, 95, 99])

        return {
            "metric_value": np.mean(individual_metric_values).item(),
            "mean": np.mean(individual_metric_values).item(),
            "min": np.min(individual_metric_values).item(),
            "max": np.max(individual_metric_values).item(),
            "std": np.std(individual_metric_values).item(),
            "percentiles": {
                "25": percentile_values[0].item(),
                "50": percentile_values[1].item(),
                "75": percentile_values[2].item(),
                "90": percentile_values[3].item(),
                "95": percentile_values[4].item(),
                "99": percentile_values[5].item()
            }
        }
