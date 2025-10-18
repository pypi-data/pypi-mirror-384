# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

import uuid
from collections import Counter
from datetime import datetime
from typing import Annotated, Any, Self

import pandas as pd
from pydantic import BaseModel, Field, model_validator

from ibm_watsonx_gov.entities.base_classes import BaseMetricResult
from ibm_watsonx_gov.entities.enums import MetricValueType
from ibm_watsonx_gov.entities.metric import Mapping

AGENTIC_RESULT_COMPONENTS = ["conversation", "message", "node"]


class RecordMetricResult(BaseMetricResult):
    record_id: Annotated[str, Field(
        description="The record identifier.", examples=["record1"])]
    record_timestamp: Annotated[str | None, Field(
        description="The record timestamp.", examples=["2025-01-01T00:00:00.000000Z"], default=None)]


class ToolMetricResult(RecordMetricResult):
    tool_name: Annotated[str, Field(
        title="Tool Name", description="Name of the tool for which this result is computed.")]
    execution_count: Annotated[int, Field(
        title="Execution count", description="The execution count for this tool name.", gt=0, default=1)]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ToolMetricResult):
            return False

        return (self.record_id, self.tool_name, self.execution_count, self.name, self.method, self.value, self.record_timestamp) == \
            (other.record_id, other.tool_name, other.execution_count,
             other.name, other.method, other.value, other.record_timestamp)

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, ToolMetricResult):
            raise NotImplementedError

        return (self.record_id, self.tool_name, self.execution_count, self.name, self.method, self.value, self.record_timestamp) < \
            (other.record_id, other.tool_name, other.execution_count,
             other.name, other.method, other.value, other.record_timestamp)

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, ToolMetricResult):
            raise NotImplementedError

        return (self.record_id, self.tool_name, self.execution_count, self.name, self.method, self.value, self.record_timestamp) > \
            (other.record_id, other.tool_name, other.execution_count,
             other.name, other.method, other.value, other.record_timestamp)

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, ToolMetricResult):
            raise NotImplementedError

        return (self.record_id, self.tool_name, self.execution_count, self.name, self.method, self.value, self.record_timestamp) <= \
            (other.record_id, other.tool_name, other.execution_count,
             other.name, other.method, other.value, other.record_timestamp)

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, ToolMetricResult):
            raise NotImplementedError

        return (self.record_id, self.tool_name, self.execution_count, self.name, self.method, self.value, self.record_timestamp) >= \
            (other.record_id, other.tool_name, other.execution_count,
             other.name, other.method, other.value, other.record_timestamp)


class AggregateMetricResult(BaseMetricResult):
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    total_records: int
    labels_count: dict | None = None
    record_level_metrics: list[RecordMetricResult] = []

    @staticmethod
    def create(results: list[RecordMetricResult]) -> Self | None:
        if not results:
            return None

        values, labels = [], []

        for r in results:
            if r.value is not None:
                values.append(r.value)
            if r.label is not None:
                labels.append(r.label)

        value, mean, min_val, max_val, labels_count = None, None, None, None, None
        if values:
            mean = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            value = mean

        if labels:
            labels_count = dict(Counter(labels))

        first = results[0]
        # creating AggregateMetricResult
        aggregated_result = AggregateMetricResult(
            name=first.name,
            display_name=first.display_name,
            method=first.method,
            group=first.group,
            provider=first.provider,
            value=value,
            labels_count=labels_count,
            total_records=len(results),
            record_level_metrics=results,
            min=min_val,
            max=max_val,
            mean=mean,
            thresholds=first.thresholds
        )
        return aggregated_result


class MetricsEvaluationResult(BaseModel):
    metrics_result: list[AggregateMetricResult]

    def to_json(self, indent: int | None = None, **kwargs):
        """
        Transform the metrics evaluation result to a json.
        The kwargs are passed to the model_dump_json method of pydantic model. All the arguments supported by pydantic model_dump_json can be passed.

        Args:
            indent (int, optional): The indentation level for the json. Defaults to None.

        Returns:
            string of the result json.
        """
        if kwargs.get("exclude_unset") is None:
            kwargs["exclude_unset"] = True
        return self.model_dump_json(
            exclude={
                "metrics_result": {
                    "__all__": {
                        "record_level_metrics": {
                            "__all__": {"provider", "name", "method", "group", "display_name"}
                        }
                    }
                }
            },
            indent=indent,
            **kwargs,
        )

    def to_df(self, data: pd.DataFrame | None = None, include_additional_info: bool = False) -> pd.DataFrame:
        """
        Transform the metrics evaluation result to a dataframe.

        Args:
            data (pd.DataFrame): the input dataframe, when passed will be concatenated to the metrics result
            include_additional_info (bool): wether to include additional info in the metrics result
        Returns:
            pd.DataFrame: new dataframe of the input and the evaluated metrics
        """
        values_dict: dict[str, list[float | str | bool]] = {}
        for result in self.metrics_result:
            metric_key = f"{result.name}.{result.method}" if result.method else result.name

            values_dict[metric_key] = [
                record_metric.value for record_metric in result.record_level_metrics]

            if include_additional_info and len(result.record_level_metrics) > 0:
                additional_info = result.record_level_metrics[0].additional_info
                if additional_info:
                    for k in additional_info.keys():
                        values_dict[f"{metric_key}.{k}"] = [
                            record_metric.additional_info[k] for record_metric in result.record_level_metrics
                        ]

        if data is None:
            return pd.DataFrame.from_dict(values_dict)
        else:
            return pd.concat([data, pd.DataFrame.from_dict(values_dict)], axis=1)

    def to_dict(self) -> list[dict]:
        """
        Transform the metrics evaluation result to a list of dict containing the record level metrics.
        """
        result = []
        for aggregate_metric_result in self.metrics_result:
            for record_level_metric_result in aggregate_metric_result.record_level_metrics:
                result.append(record_level_metric_result.model_dump())
        return result


class AgentMetricResult(BaseMetricResult):
    """
    This is the data model for metric results in the agentic app.
    It stores evaluation results for conversations, messages and nodes.
    """
    id: Annotated[str, Field(
        description="The unique identifier for the metric result record. UUID.",
        default_factory=lambda: str(uuid.uuid4()))]

    ts: Annotated[datetime, Field(
        description="The timestamp when the metric was recorded.",
        default_factory=datetime.now)]

    applies_to: Annotated[str, Field(
        description="The type of component the metric result applies to.",
        examples=AGENTIC_RESULT_COMPONENTS
    )]

    message_id: Annotated[str | None, Field(
        description="The ID of the message being evaluated.")]

    message_ts: Annotated[datetime | None, Field(
        description="The timestamp of the message being evaluated.", default=None)]

    conversation_id: Annotated[str | None, Field(
        description="The ID of the conversation containing the message.", default=None)]

    node_name: Annotated[str | None, Field(
        description="The name of the node being evaluated.", default=None)]

    execution_count: Annotated[int | None, Field(
        title="Execution count", description="The execution count of the node in a message.", default=None)]

    execution_order: Annotated[int | None, Field(
        title="Execution order", description="The execution order number in the sequence of nodes executed in a message.", default=None)]

    is_violated: Annotated[int | None, Field(
        title="Is Violated", description="Indicates whether the metric threshold is violated or not. For numeric metric, "
        "its set to 1 if the metric value violates the defined threshold lower or upper limit and 0 otherwise. "
        "For categorical metric, its set to 1 if the metric value belongs to unfavourable category and 0 otherwise.", default=None)]

    @model_validator(mode="after")
    def validate_is_violated(self) -> Any:

        if self.value is not None:
            self.is_violated = self.check_violated_record()
        return self

    def check_violated_record(self) -> Any:
        """
        Helper to check if a metric value violates any of the defined thresholds.

        Returns:
            int|None: Returns 1 if the value violates any threshold, 0 if it does not violate any,
                    and None if the value_type is unsupported or thresholds are not defined.

        """

        if self.value_type == MetricValueType.NUMERIC.value and self.thresholds:
            for threshold in self.thresholds:
                if threshold.type == "lower_limit" and self.value < threshold.value:
                    return 1
                elif threshold.type == "upper_limit" and self.value > threshold.value:
                    return 1
            return 0

        elif self.value_type == MetricValueType.CATEGORICAL.value:
            pass
        else:
            return None


class AggregateAgentMetricResult(BaseMetricResult):
    min: Annotated[float | None, Field(
        description="The minimum value of the metric. Applicable for numeric metric types.", default=None)]
    max: Annotated[float | None, Field(
        description="The maximum value of the metric. Applicable for numeric metric types.", default=None)]
    mean: Annotated[float | None, Field(
        description="The mean value of the metric. Applicable for numeric metric types.", default=None)]
    percentiles: Annotated[dict[str, float] | None, Field(
        description="Dictionary of percentile values (25th, 50th, 75th, 90th, 95th, 99th) of the metric. Applicable for numeric metric types.", default=None)]
    unique: Annotated[int | None, Field(
        description="The distinct count of the string values found. Applicable for categorical metric types.", default=None)]
    value: Annotated[float | dict[str, int] | None, Field(
        description="The value of the metric. Defaults to mean for numeric metric types. For categorical metric types, this has the frequency distribution of non-null categories.", default=None)]
    count: Annotated[int | None, Field(
        description="The count for metric results used for aggregation.", default=None)]
    node_name: Annotated[str | None, Field(
        description="The name of the node being evaluated.", default=None)]
    applies_to: Annotated[str, Field(
        description="The type of component the metric result applies to.",
        examples=AGENTIC_RESULT_COMPONENTS
    )]
    individual_results: Annotated[list[AgentMetricResult], Field(
        description="The list individual metric results.", default=[]
    )]

    violations_count: Annotated[int | None, Field(
        description="The count of records that violated the defined thresholds.", default=None
    )]

    @model_validator(mode="after")
    def validate_violations_count(self) -> Any:
        if self.individual_results and any(r.is_violated is not None for r in self.individual_results):
            self.violations_count = sum(
                1 for r in self.individual_results if r.is_violated == 1)
        return self


class MessageData(BaseModel):
    """
    The model class to capture the message input output data for an agent.
    """
    message_id: Annotated[str | None,
                          Field(title="Message ID",
                                description="The ID of the message.")]
    message_ts: Annotated[datetime | None,
                          Field(title="Message timestamp",
                                description="The timestamp of the message in ISO format. The end timestamp of the message processing is considered as the message timestamp.")]
    conversation_id: Annotated[str | None,
                               Field(title="Conversation ID",
                                     description="The ID of the conversation containing the message.")]
    start_time: Annotated[str | None,
                          Field(title="Start time",
                                description="The message execution start time in ISO format.")]
    end_time: Annotated[str | None,
                        Field(title="End time",
                              description="The message excution end time in ISO format.")]
    input: Annotated[dict | str | None,
                     Field(title="Input",
                           description="The message input data.")]
    output: Annotated[dict | str | None,
                      Field(title="Input",
                            description="The message output data.")]
    num_loops: Annotated[int,
                         Field(title="Number of Loops",
                               description="The number of loops occurred in the agent while generating the output.",
                               default=0)]


class NodeData(BaseModel):
    """
    The model class to capture the node input output data of a langgraph agent.
    """
    message_id: Annotated[str | None,
                          Field(title="Message ID",
                                description="The ID of the message.")]
    message_ts: Annotated[datetime | None,
                          Field(title="Message timestamp",
                                description="The timestamp of the message in ISO format. The end timestamp of the message processing is considered as the message timestamp.")]
    conversation_id: Annotated[str | None,
                               Field(title="Conversation ID",
                                     description="The ID of the conversation containing the message.")]
    node_name: Annotated[str | None,
                         Field(title="Node name",
                                     description="The name of the node.")]
    start_time: Annotated[str | None,
                          Field(title="Start time",
                                description="The node execution start time in ISO format.")]
    end_time: Annotated[str | None,
                        Field(title="End time",
                              description="The node execution end time in ISO format.")]
    input: Annotated[dict | str | None,
                     Field(title="Input",
                           description="The node input data.")]
    output: Annotated[dict | str | None,
                      Field(title="Input",
                            description="The node output data.")]
    execution_order: Annotated[int,
                               Field(title="Execution Order",
                                     description="The execution order of the node in the langgraph.",
                                     default=0)]
    execution_count: Annotated[int,
                               Field(title="Execution Count",
                                     description="The execution count of the node in the langgraph.",
                                     default=0)]
    node_txn_id: Annotated[str,
                           Field(title="Node transaction id",
                                 description="Unique identifier of the object.",
                                 default=str(uuid.uuid4()))
                           ]
    node_txn_timestamp: Annotated[str,
                                  Field(title="Node transaction timestamp",
                                        description="The node transaction timestamp. The end timestamp of the node execution is considered as the node transaction timestamp.")]


class MetricMapping(BaseModel):
    """
    The metric mapping data
    """
    name: Annotated[str,
                    Field(title="Name",
                          description="The name of the metric.")]
    method: Annotated[str | None,
                      Field(title="Method",
                            description="The method used to compute the metric.",
                            default=None)]
    applies_to: Annotated[str,
                          Field(Field(title="Applies to",
                                description="The tag to indicate for which the metric is applied to. Used for agentic application metric computation.",
                                examples=["message",
                                          "conversation", "sub_agent"],
                                default="message"))]
    mapping: Annotated[Mapping | None,
                       Field(title="Mapping",
                             description="The data mapping details for the metric which are used to read the values needed to compute the metric.",
                             default=None)]


class MetricsMappingData(BaseModel):
    """
    The model class to capture the metrics mappings and the span data.
    """
    message_id: Annotated[str,
                          Field(title="Message ID",
                                description="The ID of the message.")]
    metric_mappings: Annotated[list[MetricMapping],
                               Field(title="Metric Mapping",
                                     description="The list of metric mappings.")]
    data: Annotated[dict,
                    Field(title="Data",
                          description="The span data used for metrics computation.",
                          examples=[{"LangGraph.workflow": {"traceloop.entity.output": {"$.outputs.generated_text": "The response"}}}])]
