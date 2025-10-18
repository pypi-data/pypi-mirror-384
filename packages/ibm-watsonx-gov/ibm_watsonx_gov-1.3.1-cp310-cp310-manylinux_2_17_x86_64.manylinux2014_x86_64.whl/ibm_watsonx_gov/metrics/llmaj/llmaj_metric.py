# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

import re
from typing import Annotated, Literal, Optional, Self

import pandas as pd
from pydantic import Field, field_validator, model_validator

from ibm_watsonx_gov.config import AgenticAIConfiguration, GenAIConfiguration
from ibm_watsonx_gov.entities.criteria import Option
from ibm_watsonx_gov.entities.enums import (MetricGroup, MetricType,
                                            MetricValueType, TaskType)
from ibm_watsonx_gov.entities.evaluation_result import AggregateMetricResult
from ibm_watsonx_gov.entities.llm_judge import LLMJudge
from ibm_watsonx_gov.entities.metric import GenAIMetric
from ibm_watsonx_gov.entities.metric_threshold import MetricThreshold

try:
    from ibm_watsonx_gov.providers.eval_assist_provider import (
        VARIABLES_PATTERN, EvalAssistProvider)
except:
    pass

from ibm_watsonx_gov.utils.async_util import run_in_event_loop
from ibm_watsonx_gov.utils.constants import CUSTOM_TYPE


class LLMAsJudgeMetric(GenAIMetric):
    """
    Defines the LLMAsJudge metric class.

    The LLMAsJudge metric evaluates the model input, output text based on the provided criteria or the grader prompt using a judge llm.

    Examples:
        1. Create LLMAsJudge metric with user defined grader prompt.
            .. code-block:: python

                # Define LLM Judge using watsonx.ai
                # To use other frameworks and models as llm_judge, see :module:`ibm_watsonx_gov.entities.foundation_model`
                llm_judge = LLMJudge(model=WxAIFoundationModel(
                                            model_id="llama-3-3-70b-instruct",
                                            project_id="<PROJECT_ID>"))
                prompt_template="You are presented with a response generated subject to a context.\\nContext: \\n {context} \\n Response: {response} \\n. Is the response faithful according to context?\\nChoose an option:\\n- 'Yes' if The response is faithful according to context.\\n- 'No' if The response is not faithful according to context."
                options=["Yes", "No"])
                # Optionally the numeric mapping for the string option can be specified as below
                # options={"Yes": 1, "No": 0}
                metric = LLMAsJudgeMetric(llm_judge=llm_judge,
                                          prompt_template=prompt_template,
                                          options=options)
                evaluator = MetricsEvaluator()
                evaluation_result = evaluator.evaluate(data=data,
                                                       metrics=metrics)

        2. Create LLMAsJudge metric with user defined criteria and with default options. It is recommended to provide the options along with the description as shown in the next example for better accuracy.
            .. code-block:: python

                # Define LLM Judge using watsonx.ai
                # To use other frameworks and models as llm_judge, see :module:`ibm_watsonx_gov.entities.foundation_model`
                llm_judge = LLMJudge(model=WxAIFoundationModel(
                                            model_id="llama-3-3-70b-instruct",
                                            project_id="<PROJECT_ID>"))
                criteria_description="Is the {generated_text} faithful according to {context}?"
                # When using the criteria description, its required to specify the output field if its other than generated_text.
                metric = LLMAsJudgeMetric(name="factuality",
                                          llm_judge=llm_judge,
                                          criteria_description=criteria_description,
                                          # output_field="generated_text"
                                          )
                evaluator = MetricsEvaluator()
                evaluation_result = evaluator.evaluate(data=data,
                                                       metrics=metrics)

        3. Create LLMAsJudge metric with user defined criteria and options.
            .. code-block:: python

                # Define LLM Judge using watsonx.ai
                # To use other frameworks and models as llm_judge, see :module:`ibm_watsonx_gov.entities.foundation_model`
                llm_judge = LLMJudge(model=WxAIFoundationModel(
                                            model_id="llama-3-3-70b-instruct",
                                            project_id="<PROJECT_ID>"))
                criteria_description="Is the {response} faithful according to {context}?"
                options=[Option(name="Yes",
                                description="The {response} is faithful according to {context}.",
                                value=1.0),
                        Option(name="No",
                                description="The {response} is not faithful according to {context}.",
                                value=0.0)])
                # When using the criteria description, its required to specify the output field if its other than generated_text.
                metric = LLMAsJudgeMetric(name="factuality",
                                          llm_judge=llm_judge,
                                          criteria_description=criteria_description,
                                          options=options,
                                          output_field="response")
                evaluator = MetricsEvaluator()
                evaluation_result = evaluator.evaluate(data=data,
                                                       metrics=metrics)
    """
    name: Annotated[str,
                    Field(title="Name",
                          description="The llm as judge metric name. The name should be in lower snake case format.")]
    display_name: Annotated[Optional[str],
                            Field(title="Display Name",
                                  description="The llm as judge metric display name. If not specified, its derived from the name.",
                                  default=None)]
    type_: Annotated[CUSTOM_TYPE, Field(title="Metric type",
                                        description="The type of the metric.",
                                        serialization_alias="type",
                                        default=MetricType.CUSTOM.value,
                                        frozen=True,
                                        examples=[MetricType.CUSTOM.value])]
    value_type: Annotated[str, Field(title="Metric value type",
                                     description="The type of the metric value. Indicates whether the metric value is numeric or categorical. The default value is categorical.",
                                     serialization_alias="type", default=MetricValueType.CATEGORICAL.value,
                                     examples=MetricValueType.values())]
    llm_judge: Annotated[LLMJudge,
                         Field(title="LLM Judge",
                               description="The LLM judge to be used for evaluation.")]
    criteria_description: Annotated[Optional[str],
                                    Field(title="Criteria Description",
                                          description="The description of the evaluation criteria used to compute the metric.",
                                          examples=[
                                              "Is the {response} concise and to the point?"],
                                          default=None)]
    prompt_template: Annotated[Optional[str],
                               Field(title="Prompt Template",
                                     description="The grader prompt template used to compute the metric.",
                                     default=None,
                                     examples=["You are an expert grader. Your job is to evaluate how factually grounded an AI-generated answer is based on a given context. \n ## Grading Scale: \n Rate the answer either Yes or No:"])]
    options: Annotated[list[Option] | list[dict] | list[str] | dict,
                       Field(title="Options",
                             description="The list of options of the judge response.",
                             default=[Option(name="Yes",
                                             value=1.0),
                                      Option(name="No",
                                             value=0.0)],
                             examples=[["Yes", "No"], [{"name": "Yes", "value": 1}, {"name": "No", "value": 0}], [{"name": "Yes", "value": 1, "description": ""}, {"name": "No", "value": 0, "description": ""}]]),
                       ]
    output_field: Annotated[Optional[str], Field(title="Output Field",
                                                 description="The model generated output field in the data. This is required when providing the criteria description. Default value is 'generated_text'.",
                                                 default="generated_text",
                                                 examples=["output"])]
    group: Annotated[str,
                     Field(title="Group",
                           description="The metric group. The default group name is custom.",
                           default=MetricGroup.CUSTOM.value)]
    thresholds: Annotated[list[MetricThreshold],
                          Field(title="Thresholds",
                                description="The metric thresholds.",
                                default=[MetricThreshold(type="lower_limit", value=0.7)])]
    tasks: Annotated[list[TaskType],
                     Field(title="Tasks",
                           description="The list of supported tasks.",
                           default=[])]
    method: Annotated[Literal["llm_as_judge"],
                      Field(title="Method",
                            description="The method used to compute the metric.",
                            default="llm_as_judge", frozen=True)]

    @field_validator("options", mode="before")
    def parse_options(cls, value):
        if isinstance(value, list):
            if isinstance(value[0], str):
                return [Option(name=v) for v in value]
        elif isinstance(value, dict):
            return [Option(name=k, value=v) for k, v in value.items()]

        return value

    @model_validator(mode="after")
    def validate(self) -> Self:
        if not self.criteria_description and not self.prompt_template:
            raise ValueError(
                "One of criteria_description or prompt_template is required.")

        if self.criteria_description and not self.output_field:
            raise ValueError(
                "The `output_field` value is invalid. Please provide valid value for `output_field` attribute.")

        if self.value_type == MetricValueType.NUMERIC.value:
            for o in self.options:
                if o.value is None:
                    raise ValueError(
                        f"The option is invalid. The metric value type is numeric, but the criteria option '{o.name}' does not have a valid value. Please provide a valid option.")

        if not bool(re.fullmatch(r'[a-z][a-z0-9]*(?:_[a-z0-9]+)*', self.name)):
            raise ValueError(
                "The metric name should be in lower snake case format.")

        if not self.display_name:
            words = self.name.split('_')
            self.display_name = ' '.join(word.capitalize() for word in words)

        return self

    def evaluate(self,
                 data: pd.DataFrame,
                 configuration: GenAIConfiguration | AgenticAIConfiguration,
                 **kwargs) -> AggregateMetricResult:
        # If ran in sync mode, block until it is done
        return run_in_event_loop(
            self.evaluate_async,
            data=data,
            configuration=configuration,
            **kwargs,
        )

    async def evaluate_async(self, data: pd.DataFrame,
                             configuration: GenAIConfiguration | AgenticAIConfiguration,
                             **kwargs) -> AggregateMetricResult:

        data_cols = data.columns.to_list()
        self.__validate_fields(data_cols)

        context_fields = []
        if self.criteria_description:
            if self.output_field not in data_cols:
                raise ValueError(
                    f"The output field {self.output_field} is not present in the data.")

            ctx_fields = list(self.__criteria_fields)
            ctx_fields.remove(self.output_field)
            context_fields = ctx_fields
        provider = EvalAssistProvider(metric_name=self.name,
                                      display_name=self.display_name,
                                      value_type=self.value_type,
                                      criteria_description=self.criteria_description,
                                      llm_judge=self.llm_judge,
                                      metric_group=self.group,
                                      metric_method=self.method,
                                      thresholds=self.thresholds,
                                      prompt_template=self.prompt_template,
                                      options=self.options,
                                      prediction_field=self.output_field,
                                      context_fields=context_fields,
                                      **kwargs)

        return await provider.evaluate_async(data)

    def __validate_fields(self, data_cols):
        if self.criteria_description:
            fields_from_criteria = set()
            fields_from_options = set()
            fields_from_criteria.update(re.findall(
                VARIABLES_PATTERN, self.criteria_description))
            for option in self.options:
                fields_from_options.update(re.findall(
                    VARIABLES_PATTERN, option.description))

            if (not all(field in data_cols for field in fields_from_criteria)):
                raise ValueError(
                    f"The fields provided in the criteria description {fields_from_criteria} are not present in the data.")
            if (not all(field in data_cols for field in fields_from_options)):
                raise ValueError(
                    f"The fields provided in the options description {fields_from_options} are not present in the data.")
            self.__criteria_fields = fields_from_criteria | fields_from_options
        elif self.prompt_template:
            fields_from_prompt = set()
            fields_from_prompt.update(re.findall(
                VARIABLES_PATTERN, self.prompt_template))

            if (not all(field in data_cols for field in fields_from_prompt)):
                raise ValueError(
                    f"The fields provided in the prompt template {fields_from_prompt} are not present in the data.")
