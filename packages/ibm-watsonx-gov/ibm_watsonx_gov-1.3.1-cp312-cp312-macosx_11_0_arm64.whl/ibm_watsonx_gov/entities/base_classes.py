# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field

from ibm_watsonx_gov.entities.enums import (MetricGroup, MetricType,
                                            MetricValueType)
from ibm_watsonx_gov.entities.metric_threshold import MetricThreshold


class BaseConfiguration(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True)

    record_id_field: Annotated[str, Field(title="Record id field",
                                          description="The record identifier field name.",
                                          examples=["record_id"],
                                          default="record_id")]
    record_timestamp_field: Annotated[str, Field(title="Record timestamp field",
                                                 description="The record timestamp field name.",
                                                 examples=["record_timestamp"],
                                                 default="record_timestamp")]


class BaseMetric(BaseModel):
    name: Annotated[str, Field(title="Metric Name",
                               description="The name of the metric.",
                               frozen=True,
                               examples=["answer_relevance",
                                         "context_relevance"],)]
    display_name: Annotated[str | None, Field(title="Metric display name",
                                              description="The display name of the metric.",
                                              examples=["Answer Relevance",
                                                        "Context Relevance"],
                                              default=None)]
    type_: Annotated[str, Field(title="Metric type",
                                description="The type of the metric. Indicates whether the metric is ootb or custom.",
                                serialization_alias="type",
                                default=MetricType.OOTB.value,
                                frozen=True,
                                examples=MetricType.values())]
    value_type: Annotated[str, Field(title="Metric value type",
                                     description="The type of the metric value. Indicates whether the metric value is numeric or categorical.",
                                     serialization_alias="type", default=MetricValueType.NUMERIC.value,
                                     examples=MetricValueType.values())]
    _id: Annotated[str, PrivateAttr(default=None)]

    @computed_field(return_type=str)
    @property
    def id(self):
        if self._id is None:
            self._id = self.name
        return self._id


class BaseMetricGroup(BaseModel):
    name: Annotated[str, Field(description="The name of the metric group")]
    _metrics: Annotated[list[BaseMetric], Field(
        description="Metrics to be computed when selecting this metric group", default=[])]

    @property
    def metrics(self) -> list[BaseMetric]:
        return self._metrics


class Error(BaseModel):
    code: Annotated[str, Field(description="The error code")]
    message_en: Annotated[str, Field(
        description="The error message in English.")]
    parameters: Annotated[list[Any], Field(
        description="The list of parameters to construct the message in a different locale.", default=[])]


class BaseMetricResult(BaseModel):
    name: Annotated[str, Field(title="Metric Name",
                               description="The name of the metric.",
                               frozen=True,
                               examples=["answer_relevance",
                                         "context_relevance"],)]
    display_name: Annotated[str, Field(title="Metric display name",
                                       description="The display name of the metric.",
                                       frozen=True,
                                       examples=["Answer Relevance",
                                                 "Context Relevance"],)]
    value_type: Annotated[str, Field(title="Metric value type",
                                     description="The type of the metric value. Indicates whether the metric value is numeric or categorical.",
                                     serialization_alias="type", default=MetricValueType.NUMERIC.value,
                                     examples=MetricValueType.values())]
    method: Annotated[str | None, Field(title="Method",
                                        description="The method used to compute this metric result.",
                                        examples=["token_recall"],
                                        default=None)]
    provider: Annotated[str | None, Field(title="Provider",
                                          description="The provider used to compute this metric result.",
                                          default=None)]
    value: Annotated[float | str | bool | dict[str, int] | None, Field(title="Value",
                                                                       description="The metric value.")]
    label: Annotated[str | None, Field(title="Label",
                                       description="The string equivalent of the metric value. This is used for metrics with categorical value type.",
                                       default=None)]
    errors: Annotated[list[Error] | None, Field(title="Errors",
                                                description="The list of error messages",
                                                default=None)]
    additional_info: Annotated[dict | None, Field(title="Additional Info",
                                                  description="The additional information about the metric result.",
                                                  default=None)]
    explanation: Annotated[str | None, Field(title="Explanation",
                                             description="The explanation about the metric result.",
                                             default=None)]
    group: Annotated[MetricGroup | None, Field(title="Group",
                                               description="The metric group",
                                               default=None)]
    thresholds: Annotated[list[MetricThreshold], Field(title="Thresholds",
                                                       description="The metric thresholds",
                                                       default=[])]

    model_config = ConfigDict(
        arbitrary_types_allowed=True, use_enum_values=True)
