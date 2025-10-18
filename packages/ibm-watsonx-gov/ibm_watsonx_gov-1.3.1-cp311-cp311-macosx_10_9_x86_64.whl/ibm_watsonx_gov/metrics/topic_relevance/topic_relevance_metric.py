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
from pydantic import Field

from ibm_watsonx_gov.config.gen_ai_configuration import GenAIConfiguration
from ibm_watsonx_gov.entities.enums import MetricGroup, TaskType
from ibm_watsonx_gov.entities.evaluation_result import AggregateMetricResult
from ibm_watsonx_gov.entities.metric import GenAIMetric
from ibm_watsonx_gov.entities.metric_threshold import MetricThreshold
from ibm_watsonx_gov.providers.detectors_provider import DetectorsProvider
from ibm_watsonx_gov.utils.async_util import run_in_event_loop
from ibm_watsonx_gov.utils.validation_util import validate_input

TOPIC_RELEVANCE = "topic_relevance"


class TopicRelevanceMetric(GenAIMetric):
    """
    Defines the TopicRelevance metric class.

    The TopicRelevance metric evaluates how closely the input content aligns with the topic specified by the system_prompt.

    Note : system_prompt is mandatory

    Examples:
        1. Create TopicRelevance metric with default parameters and compute using metrics evaluator.
            .. code-block:: python

                metric = TopicRelevanceMetric(system_prompt="...")
                result = MetricsEvaluator().evaluate(data={"input_text": "...", metrics=[metric])

        2. Create TopicRelevance metric with a custom threshold.
            .. code-block:: python

                threshold  = MetricThreshold(type="lower_limit", value=0.5)
                metric = TopicRelevanceMetric(threshold=threshold, system_prompt="...")
    """
    name: Annotated[Literal["topic_relevance"],
                    Field(title="Name",
                          description="The topic relevance metric name.",
                          default=TOPIC_RELEVANCE, frozen=True)]
    display_name: Annotated[Literal["Topic Relevance"],
                            Field(title="Display Name",
                                  description="The topic relevance metric display name.",
                                  default="Topic Relevance", frozen=True)]
    thresholds: Annotated[list[MetricThreshold],
                          Field(title="Thresholds",
                                description="The metric thresholds.",
                                default=[MetricThreshold(type="lower_limit", value=0.7)])]
    tasks: Annotated[list[TaskType],
                     Field(title="Tasks",
                           description="The list of supported tasks.",
                           default=TaskType.values(), frozen=True)]
    # TODO uncomment when the metric is pushed to prod
    # group: Annotated[MetricGroup, Field(title="Group",
    #                                     description="The metric group.",
    #                                     default=MetricGroup.CONTENT_SAFETY, frozen=True)]
    system_prompt: Annotated[str, Field(title="System Prompt",
                                        description=f"The AI model system prompt which contains instructions to define its overall behavior.")]

    async def evaluate_async(
            self,
            data: pd.DataFrame | dict,
            configuration: GenAIConfiguration,
            **kwargs
    ) -> list[AggregateMetricResult]:
        if not self.system_prompt:
            raise AssertionError(
                f"The system_prompt field is required but was missing from the input.")

        validate_input(data.columns.to_list(), configuration)
        # Set system_prompt as part of the detector parameters
        kwargs["detector_params"] = {"system_prompt": self.system_prompt}
        provider = DetectorsProvider(configuration=configuration,
                                     metric_name=self.name,
                                     metric_display_name=self.display_name,
                                     metric_method=self.method,
                                     metric_group=MetricGroup.CONTENT_SAFETY,
                                     thresholds=self.thresholds,
                                     **kwargs)
        aggregated_metric_result = provider.evaluate(data=data)
        return aggregated_metric_result

    def evaluate(
        self,
        data: pd.DataFrame | dict,
        configuration: GenAIConfiguration,
        **kwargs,
    ):
        # If ran in sync mode, block until it is done
        return run_in_event_loop(
            self.evaluate_async,
            data=data,
            configuration=configuration,
            **kwargs,
        )
