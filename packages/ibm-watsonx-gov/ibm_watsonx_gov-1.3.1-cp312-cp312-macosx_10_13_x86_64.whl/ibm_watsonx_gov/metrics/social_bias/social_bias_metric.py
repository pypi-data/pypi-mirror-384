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

SOCIAL_BIAS = "social_bias"


class SocialBiasMetric(GenAIMetric):
    """
    Defines the Social Bias metric class.

    The Social Bias metric measures the risk of systemic prejudice against groups based on shared identity or characteristics, often stemming from stereotypes or cultural influences. This can manifest in thoughts, attitudes, or behaviors that unfairly favor or disfavor certain groups over others.
    It is computed using the granite guardian model.

    Examples:
        1. Create Social Bias metric with default parameters and compute using metrics evaluator.
            .. code-block:: python

                metric = SocialBiasMetric()
                result = MetricsEvaluator().evaluate(data={"input_text": "...", metrics=[metric])

        2. Create Social Bias metric with a custom threshold.
            .. code-block:: python

                threshold  = MetricThreshold(type="lower_limit", value=0.5)
                metric = SocialBiasMetric(threshold=threshold)
    """
    name: Annotated[Literal["social_bias"],
                    Field(title="Name",
                          description="The social bias metric name.",
                          default=SOCIAL_BIAS, frozen=True)]
    display_name: Annotated[Literal["Social Bias"],
                            Field(title="Display Name",
                                  description="The social bias metric display name.",
                                  default="Social Bias", frozen=True)]
    method: Annotated[Literal["granite_guardian"],
                      Field(title="Method",
                            description="The method used to compute harm metric.",
                            default="granite_guardian")]
    tasks: Annotated[list[TaskType],
                     Field(title="Tasks",
                           description="The list of supported tasks.",
                           default=TaskType.values(), frozen=True)]
    thresholds: Annotated[list[MetricThreshold],
                          Field(title="Thresholds",
                                description="The metric thresholds.",
                                default=[MetricThreshold(type="upper_limit", value=0.5)])]
    group: Annotated[MetricGroup,
                     Field(title="Group",
                           description="The metric group.",
                           default=MetricGroup.CONTENT_SAFETY, frozen=True)]

    async def evaluate_async(
        self,
        data: pd.DataFrame | dict,
        configuration: GenAIConfiguration,
        **kwargs
    ) -> list[AggregateMetricResult]:

        validate_input(data.columns.to_list(), configuration)
        kwargs["detector_params"] = {"risk_name": SOCIAL_BIAS}
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
