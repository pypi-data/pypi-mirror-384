# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

import asyncio
import functools
from abc import abstractmethod
from typing import TYPE_CHECKING, Annotated, List, Literal, Optional, Self

import pandas as pd
from pydantic import (BaseModel, Field, computed_field, field_serializer,
                      model_validator)

from ibm_watsonx_gov.entities.base_classes import BaseMetric
from ibm_watsonx_gov.entities.enums import MetricGroup, TaskType
from ibm_watsonx_gov.entities.metric_threshold import MetricThreshold

if TYPE_CHECKING:
    from ibm_watsonx_gov.config import (AgenticAIConfiguration,
                                        GenAIConfiguration)
    from ibm_watsonx_gov.entities.evaluation_result import (
        AggregateMetricResult, RecordMetricResult)


class MappingItem(BaseModel):
    """
    The mapping details to be used for reading the values from the data.
    """
    name: Annotated[str,
                    Field(title="Name",
                          description="The name of the item.",
                          examples=["input_text", "generated_text", "context", "ground_truth"])]
    type_: Annotated[Literal["input", "output", "reference", "context", "tool_call"],
                     Field(title="Type",
                           description="The type of the item.",
                           examples=["input"],
                           alias="type",
                           serialization_alias="type")]
    column_name: Annotated[Optional[str],
                           Field(title="Column Name",
                                 description="The column name in the tabular data to be used for reading the field value. Applicable for tabular source.", default=None)]
    span_name: Annotated[Optional[str],
                         Field(title="Span Name",
                               description="The span name in the trace data to be used for reading the field value. Applicable for trace source.", default=None)]
    attribute_name: Annotated[Optional[str],
                              Field(title="Attribute Name",
                                    description="The attribute name in the trace to be used for reading the field value. Applicable for trace source.", default=None)]
    json_path: Annotated[Optional[str],
                         Field(title="Json Path",
                               description="The json path to be used for reading the field value from the attribute value. Applicable for trace source. If not provided, the span attribute value is read as the field value.", default=None)]
    lookup_child_spans: Annotated[Optional[bool],
                                  Field(title="Look up child spans",
                                        description="The flag to indicate if all the child spans should be searched for the attribute value. Applicable for trace source.",
                                        default=False)]


class Mapping(BaseModel):
    """
    Defines the field mapping details to be used for computing a metric.
    """
    source: Annotated[Literal["trace", "tabular"],
                      Field(title="Source",
                            description="The source type of the data. Use trace if the data should be read from span in trace. Use tabular if the data is passed as a dataframe.",
                            default="trace",
                            examples=["trace", "tabular"])]
    items: Annotated[list[MappingItem],
                     Field(title="Mapping Items",
                           description="The list of mapping items for the field. They are used to read the data from trace or tabular data for computing the metric.")]


class GenAIMetric(BaseMetric):
    """Defines the Generative AI metric interface"""
    thresholds: Annotated[list[MetricThreshold],
                          Field(description="The list of thresholds", default=[])]
    tasks: Annotated[list[TaskType], Field(
        description="The task types this metric is associated with.", frozen=True, default=[])]
    group: Annotated[MetricGroup | None, Field(
        description="The metric group this metric belongs to.", frozen=True, default=None)]
    is_reference_free: Annotated[bool, Field(
        description="Decides whether this metric needs a reference for computation", frozen=True, default=True)]
    method: Annotated[
        str | None,
        Field(description="The method used to compute the metric.",
              default=None)]
    metric_dependencies: Annotated[list["GenAIMetric"], Field(
        description="Metrics that needs to be evaluated first", default=[])]
    applies_to: Annotated[Optional[str],
                          Field(title="Applies to",
                                description="The tag to indicate for which the metric is applied to. Used for agentic application metric computation.",
                                examples=["message",
                                          "conversation", "sub_agent"],
                                default="message")]
    mapping: Annotated[Optional[Mapping],
                       Field(title="Mapping",
                             description="The data mapping details for the metric which are used to read the values needed to compute the metric.",
                             default=None,
                             examples=Mapping(items=[MappingItem(name="input_text",
                                                                 type="input",
                                                                 span_name="LangGraph.workflow",
                                                                 attribute_name="traceloop.entity.input",
                                                                 json_path="$.inputs.input_text"),
                                                     MappingItem(name="generated_text",
                                                                 type="output",
                                                                 span_name="LangGraph.workflow",
                                                                 attribute_name="traceloop.entity.output",
                                                                 json_path="$.outputs.generated_text")])
                             )]

    @field_serializer("metric_dependencies", when_used="json")
    def metric_dependencies_serializer(self, metric_dependencies: list["GenAIMetric"]):
        return [metric.model_dump(mode="json") for metric in metric_dependencies]

    @computed_field(return_type=str)
    @property
    def id(self):
        if self._id is None:
            self._id = self.name + (f"_{self.method}" if self.method else "")
        return self._id

    @model_validator(mode="after")
    def validate(self) -> Self:
        if not self.display_name:
            words = self.name.split('_')
            self.display_name = ' '.join(word.capitalize() for word in words)

        return self

    @abstractmethod
    def evaluate(self, data: pd.DataFrame | dict,
                 configuration: "GenAIConfiguration | AgenticAIConfiguration",
                 **kwargs) -> "AggregateMetricResult":
        raise NotImplementedError

    async def evaluate_async(
        self,
        data: pd.DataFrame | dict,
        configuration: "GenAIConfiguration | AgenticAIConfiguration",
        **kwargs,
    ) -> "AggregateMetricResult":
        loop = asyncio.get_event_loop()
        # If called as async, run it in a separate thread
        return await loop.run_in_executor(
            None,
            functools.partial(
                self.evaluate,
                data=data,
                configuration=configuration,
                **kwargs,
            )
        )

    def info(self):
        pass

    def get_aggregated_results_from_individual_results(self, record_results: List["RecordMetricResult"]):
        from ibm_watsonx_gov.entities.evaluation_result import \
            AggregateMetricResult

        values = [record.value for record in record_results]
        record_result = record_results[0]
        mean = sum(values) / len(values)
        return AggregateMetricResult(
            name=record_result.name,
            method=record_result.method,
            provider=record_result.provider,
            group=record_result.group,
            value=mean,
            total_records=len(record_results),
            record_level_metrics=record_results,
            min=min(values),
            max=max(values),
            mean=mean,
        )


class PredictiveAIMetric(BaseMetric):
    pass
