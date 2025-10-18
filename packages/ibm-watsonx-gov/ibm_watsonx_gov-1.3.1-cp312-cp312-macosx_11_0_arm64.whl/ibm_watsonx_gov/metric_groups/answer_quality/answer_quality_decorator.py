# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

from functools import partial
from typing import Callable, Optional

from wrapt import decorator

from ibm_watsonx_gov.config import AgenticAIConfiguration
from ibm_watsonx_gov.entities.enums import EvaluatorFields, MetricGroup
from ibm_watsonx_gov.entities.metric import GenAIMetric
from ibm_watsonx_gov.metrics import (AnswerRelevanceMetric,
                                     AnswerSimilarityMetric,
                                     FaithfulnessMetric,
                                     UnsuccessfulRequestsMetric)
from ibm_watsonx_gov.metrics.base_metric_decorator import BaseMetricDecorator


class AnswerQualityDecorator(BaseMetricDecorator):
    def evaluate_answer_quality(self,
                                func: Optional[Callable] = None,
                                *,
                                configuration: Optional[AgenticAIConfiguration] = None,
                                metrics: list[GenAIMetric] = []
                                ) -> dict:
        """
        An evaluation decorator for computing answer quality metrics on an agentic node.
        """
        if func is None:
            return partial(self.evaluate_answer_quality, configuration=configuration, metrics=metrics)

        if not metrics:
            metrics = MetricGroup.ANSWER_QUALITY.get_metrics()

        @decorator
        def wrapper(func, instance, args, kwargs):

            try:
                self.validate(func=func, metrics=metrics,
                              valid_metric_types=(AnswerRelevanceMetric, FaithfulnessMetric, UnsuccessfulRequestsMetric, AnswerSimilarityMetric))

                metric_inputs = [EvaluatorFields.INPUT_FIELDS,
                                 EvaluatorFields.CONTEXT_FIELDS]
                metric_outputs = [EvaluatorFields.OUTPUT_FIELDS]
                metric_references = [EvaluatorFields.REFERENCE_FIELDS]

                original_result = self.compute_helper(func=func, args=args, kwargs=kwargs,
                                                      configuration=configuration,
                                                      metrics=metrics,
                                                      metric_inputs=metric_inputs,
                                                      metric_outputs=metric_outputs,
                                                      metric_references=metric_references,
                                                      metric_groups=[MetricGroup.ANSWER_QUALITY])

                return original_result
            except Exception as ex:
                raise Exception(
                    f"There was an error while evaluating answer quality metrics on {func.__name__},") from ex

        return wrapper(func)
