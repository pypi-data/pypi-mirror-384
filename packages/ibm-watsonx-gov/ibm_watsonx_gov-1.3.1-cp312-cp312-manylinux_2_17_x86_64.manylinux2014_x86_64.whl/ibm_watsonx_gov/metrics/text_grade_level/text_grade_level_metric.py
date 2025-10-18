# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

from typing import Annotated, Literal

import pandas as pd
import textstat
from pydantic import Field

from ibm_watsonx_gov.config import AgenticAIConfiguration, GenAIConfiguration
from ibm_watsonx_gov.entities.enums import MetricGroup, TaskType
from ibm_watsonx_gov.entities.evaluation_result import (AggregateMetricResult,
                                                        RecordMetricResult)
from ibm_watsonx_gov.entities.metric import GenAIMetric
from ibm_watsonx_gov.entities.metric_threshold import MetricThreshold
from ibm_watsonx_gov.utils.python_utils import replace_none_with_empty_string
from ibm_watsonx_gov.utils.validation_util import validate_output

TEXT_GRADE_LEVEL = "text_grade_level"
TEXT_GRADE_LEVEL_DISPLAY_NAME = "Text Grade Level"
FLESCH_KINCAID_GRADE = "flesch_kincaid_grade"
TEXTSTAT = "textstat"


class TextGradeLevelResult(RecordMetricResult):
    name: str = TEXT_GRADE_LEVEL
    display_name: str = TEXT_GRADE_LEVEL_DISPLAY_NAME
    group: MetricGroup = MetricGroup.READABILITY
    provider: str = TEXTSTAT
    method: str = FLESCH_KINCAID_GRADE


class TextGradeLevelMetric(GenAIMetric):
    """
    Defines the Text Grade Level metric class.

    The Text Grade Level metric measures the approximate reading US grade level of a text.
    It is computed using the flesch_kincaid_grade method.
    Its possible values typically range from 0 to 12+

    - Negative scores are rare and only occur with artificially simple texts.
    - No strict upper limit—some highly complex texts can score 30+, but these are extremely hard to read.

    Examples:
        1. Create Text Grade Level metric with default parameters and compute using metrics evaluator.
            .. code-block:: python

                metric = TextGradeLevelMetric()
                result = MetricsEvaluator().evaluate(data={"generated_text": "..."}, 
                                                    metrics=[metric])

        2. Create Text Grade Level metric with a custom threshold.
            .. code-block:: python

                threshold  = MetricThreshold(type="lower_limit", value=6)
                metric = TextGradeLevelMetric(thresholds=[threshold])
    """
    name: Annotated[Literal["text_grade_level"],
                    Field(title="name",
                          description="The text grade level metric name.",
                          default=TEXT_GRADE_LEVEL, frozen=True)]
    display_name: Annotated[Literal["Text Grade Level"],
                            Field(title="Display Name",
                                  description="The text grade level metric display name.",
                                  default=TEXT_GRADE_LEVEL_DISPLAY_NAME, frozen=True)]
    method: Annotated[Literal["flesch_kincaid_grade"],
                      Field(title="Method",
                            description="The method used to compute text grade level metric.",
                            default=FLESCH_KINCAID_GRADE)]
    tasks: Annotated[list[TaskType],
                     Field(title="Tasks",
                           description="The list of supported tasks.",
                           default=TaskType.values(), frozen=True)]
    group: Annotated[MetricGroup,
                     Field(title="Group",
                           description="The metric group.",
                           default=MetricGroup.READABILITY, frozen=True)]
    thresholds: Annotated[list[MetricThreshold],
                          Field(title="Thresholds",
                                description="The metric thresholds.",
                                default=[MetricThreshold(type="lower_limit", value=6)])]

    def evaluate(
            self,
            data: pd.DataFrame,
            configuration: GenAIConfiguration | AgenticAIConfiguration,
            **kwargs,
    ) -> list[AggregateMetricResult]:
        from ibm_watsonx_gov.utils.aggregation_util import get_summaries

        validate_output(data.columns.to_list(), configuration)
        record_level_metrics = []
        predictions = data[configuration.output_fields[0]].to_list()
        record_ids = data[configuration.record_id_field].to_list()
        replace_none_with_empty_string(predictions)

        all_scores = self._compute(predictions=predictions)
        record_level_metrics = [
            TextGradeLevelResult(record_id=record_id,
                                 value=score, thresholds=self.thresholds,)
            for score, record_id in zip(all_scores, record_ids)
        ]
        summary = get_summaries(all_scores)
        aggregate_metric_scores = AggregateMetricResult(
            name=self.name,
            display_name=self.display_name,
            provider=TEXTSTAT,
            method=self.method,
            group=self.group,
            min=summary.get("min"),
            max=summary.get("max"),
            mean=summary.get("mean"),
            value=summary.get("mean"),
            total_records=len(record_level_metrics),
            record_level_metrics=record_level_metrics,
            thresholds=self.thresholds,
        )

        return aggregate_metric_scores

    def _compute(self, predictions: list) -> list:
        return [textstat.flesch_kincaid_grade(pred) for pred in predictions]
