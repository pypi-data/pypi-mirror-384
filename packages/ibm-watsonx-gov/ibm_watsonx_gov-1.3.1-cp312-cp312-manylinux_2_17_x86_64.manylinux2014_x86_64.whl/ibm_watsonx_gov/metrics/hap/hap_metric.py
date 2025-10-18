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

HAP = "hap"


class HAPMetric(GenAIMetric):
    """
    Defines the HAP metric class.

    The HAP metric measures if there is any toxic content that contains hate, abuse, or profanity in the input.
    It is computed using the hap model.

    Examples:
        1. Create HAP metric with default parameters and compute using metrics evaluator.
            .. code-block:: python

                metric = HAPMetric()
                result = MetricsEvaluator().evaluate(data={"input_text": "...", metrics=[metric])

        2. Create HAP metric with a custom threshold.
            .. code-block:: python

                threshold  = MetricThreshold(type="lower_limit", value=0.5)
                metric = HAPMetric(threshold=threshold)
    """
    name: Annotated[Literal["hap"],
                    Field(title="Name",
                          description="The hap metric name.",
                          default=HAP, frozen=True)]
    display_name: Annotated[Literal["HAP"],
                            Field(title="Display Name",
                                  description="The hap metric display name.",
                                  default="HAP", frozen=True)]
    tasks: Annotated[list[TaskType],
                     Field(title="Tasks",
                           description="The list of supported tasks.",
                           default=TaskType.values(), frozen=True)]
    thresholds: Annotated[list[MetricThreshold],
                          Field(title="Thresholds",
                                description="The metric thresholds.",
                                default=[MetricThreshold(type="upper_limit", value=0.1)])]
    group: Annotated[MetricGroup,
                     Field(title="Group",
                           description="The metric group.",
                           default=MetricGroup.CONTENT_SAFETY, frozen=True)]

    async def evaluate_async(
            self,
            data: pd.DataFrame,
            configuration: GenAIConfiguration,
            **kwargs
    ) -> list[AggregateMetricResult]:

        validate_input(data.columns.to_list(), configuration)
        provider = DetectorsProvider(configuration=configuration,
                                     metric_name=self.name,
                                     metric_display_name=self.display_name,
                                     metric_method=self.method,
                                     metric_group=self.group,
                                     thresholds=self.thresholds,
                                     **kwargs)
        aggregated_metric_result = await provider.evaluate_async(data=data)
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
