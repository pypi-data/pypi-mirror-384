
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
import re

import pandas as pd
from lazy_imports import LazyModule, load

from ibm_watsonx_gov.clients.usage_client import validate_usage_client
from ibm_watsonx_gov.entities.credentials import WxAICredentials
from ibm_watsonx_gov.entities.criteria import Option
from ibm_watsonx_gov.entities.enums import EvaluationProvider, MetricGroup
from ibm_watsonx_gov.entities.evaluation_result import (AggregateMetricResult,
                                                        RecordMetricResult)
from ibm_watsonx_gov.entities.foundation_model import (
    AzureOpenAIFoundationModel, OpenAIFoundationModel, PortKeyGateway,
    WxAIFoundationModel)
from ibm_watsonx_gov.entities.llm_judge import LLMJudge
from ibm_watsonx_gov.entities.metric_threshold import MetricThreshold
from ibm_watsonx_gov.providers.inference_engines.portkey_inference_engine import \
    PortKeyInferenceEngine
from ibm_watsonx_gov.utils.async_util import start_event_loop_run_func

ea_imports = LazyModule(
    "from evalassist.judges import Criteria as EACriteria",
    "from evalassist.judges import CriteriaOption as EACriteriaOption",
    "from evalassist.judges import DirectInstance, DirectJudge",
    "from unitxt.inference import CrossProviderInferenceEngine",
    name="lazy_ea"
)
load(ea_imports)

EACriteria = ea_imports.EACriteria
EACriteriaOption = ea_imports.EACriteriaOption
DirectInstance = ea_imports.DirectInstance
DirectJudge = ea_imports.DirectJudge
CrossProviderInferenceEngine = ea_imports.CrossProviderInferenceEngine

VARIABLES_PATTERN = r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}"


class EvalAssistProvider():
    """
    The class to invoke eval assist library for computing the LLMAJ metrics.
    """

    def __init__(self, metric_name: str,
                 display_name: str,
                 value_type: str,
                 llm_judge: LLMJudge,
                 options: list[Option],
                 criteria_description: str | None = None,
                 prompt_template: str | None = None,
                 context_fields: list[str] = [],
                 prediction_field: str | None = None,
                 metric_group: MetricGroup = None,
                 metric_method: str | None = None,
                 thresholds: list[MetricThreshold] = [],
                 ** kwargs):
        self.metric_name = metric_name
        self.display_name = display_name
        self.value_type = value_type
        self.llm_judge = llm_judge
        self.criteria_description = criteria_description
        self.prompt_template = prompt_template
        self.options = options
        self.context_fields = context_fields
        self.prediction_field = prediction_field
        self.metric_group = metric_group
        self.metric_method = metric_method
        self.thresholds = thresholds
        validate_usage_client(kwargs.get("usage_client"))

    async def evaluate_async(self, data: pd.DataFrame) -> AggregateMetricResult:
        loop = asyncio.get_event_loop()
        # If called as async, run it in a separate thread
        return await loop.run_in_executor(
            None,
            functools.partial(
                start_event_loop_run_func,
                func=self.evaluate,
                data=data
            )
        )

    def evaluate(self, data: pd.DataFrame) -> AggregateMetricResult:
        try:
            judge = self.__get_judge()
            if self.criteria_description:
                criteria = self.__get_criteria(
                    self.prediction_field, self.context_fields)

                instances = self.__get_instances(data=data,
                                                 prediction_field=self.prediction_field,
                                                 context_fields=self.context_fields)

                results = judge(instances=instances, criteria=criteria)
            elif self.prompt_template:
                # Get judge prompts with filled in values
                judge_prompts = data.apply(
                    lambda row: self.prompt_template.format(**row), axis=1).to_list()

                # Get the list of valid outputs from the judge prompt
                valid_outputs = [o.name for o in self.options]

                results = judge.evaluate_with_custom_prompt(
                    judge_prompts=judge_prompts,
                    valid_outputs=valid_outputs)

            aggregated_result = self.__post_process(
                results=results, data=data)
            return aggregated_result
        except Exception as e:
            raise Exception(
                f"Error while computing metrics: {self.metric_name}. Reason: {str(e)}")

    def __get_judge(self):
        if self.llm_judge and isinstance(self.llm_judge.model, PortKeyGateway):
            judge = DirectJudge(
                inference_engine=PortKeyInferenceEngine(
                    **self.__get_inference_engine_params()),
                generate_feedback=True,
            )
        else:
            judge = DirectJudge(
                inference_engine=CrossProviderInferenceEngine(
                    **self.__get_inference_engine_params()),
                generate_feedback=True,
            )

        return judge

    def __get_instances(self, data, prediction_field, context_fields):
        instances = []
        context_data = data[context_fields].to_dict(orient="records")
        predictions = data[prediction_field].tolist()

        if context_data:
            for c, p in zip(context_data, predictions):
                instances.append(DirectInstance(context=c, response=p))
        else:
            for p in predictions:
                instances.append(DirectInstance(context={}, response=p))

        return instances

    def __get_inference_engine_params(self):
        params = {"seed": 36,
                  "data_classification_policy": ["public"]}

        if isinstance(self.llm_judge.model, WxAIFoundationModel):
            wxai_credentials: WxAICredentials = self.llm_judge.model.provider.credentials
            wml_credentials = {}
            wml_credentials["api_base"] = wxai_credentials.url
            if wxai_credentials.api_key:
                wml_credentials["api_key"] = wxai_credentials.api_key
            if wxai_credentials.version:  # using cpd
                wml_credentials["username"] = wxai_credentials.username
                wml_credentials["instance_id"] = wxai_credentials.instance_id
                if wxai_credentials.password:
                    wml_credentials["password"] = wxai_credentials.password

            if self.llm_judge.model.project_id:
                wml_credentials["project_id"] = self.llm_judge.model.project_id
            elif self.llm_judge.model.space_id:
                wml_credentials["space_id"] = self.llm_judge.model.space_id
            else:
                raise Exception("Either project or space id is required")

            params.update({
                "credentials": wml_credentials,
                "provider": "watsonx",
                "model": self.llm_judge.model.model_id,
                "provider_specific_args": {
                    "watsonx": {
                        "max_requests_per_second": 1
                    }
                }
            })

        elif isinstance(self.llm_judge.model, OpenAIFoundationModel):
            params.update({
                "credentials": {
                    "api_key": self.llm_judge.model.provider.credentials.api_key
                },
                "provider": "open-ai",
                "model": self.llm_judge.model.model_id,
                "provider_specific_args": {"temperature": 0}
            })
        elif isinstance(self.llm_judge.model, PortKeyGateway):
            params.update({
                "credentials": self.llm_judge.model.provider.credentials.model_dump(),
                "model": self.llm_judge.model.model_id
            })
        elif isinstance(self.llm_judge.model, AzureOpenAIFoundationModel):
            raise Exception("Azure OpenAI Model provider is not supported.")
        else:
            raise Exception("LLM Model provider is not supported.")

        return params

    def __get_criteria(self, prediction_field, context_fields):
        options = []

        for op in self.options:
            op_desc = op.description.replace(
                "{"+prediction_field+"}", prediction_field)
            op_desc = re.sub(VARIABLES_PATTERN, r"\1", op_desc)
            options.append(EACriteriaOption(
                name=op.name,
                description=op_desc,
                score=op.value
            ))

        desc = self.criteria_description.replace(
            "{"+prediction_field+"}", prediction_field)
        desc = re.sub(VARIABLES_PATTERN, r"\1", desc)

        criteria_with_options = EACriteria(name=self.metric_name,
                                           description=desc,
                                           prediction_field=prediction_field,
                                           context_fields=context_fields,
                                           options=options)

        return criteria_with_options

    def __post_process(self, results, data: pd.DataFrame) -> AggregateMetricResult:
        record_level_metrics: list[RecordMetricResult] = []

        score_map = {o.name: o.value for o in self.options}

        for record_id, result in zip(data["record_id"].tolist(), results):
            record_level_metrics.append(
                RecordMetricResult(
                    name=self.metric_name,
                    display_name=self.display_name,
                    method=self.metric_method,
                    group=self.metric_group,
                    provider=EvaluationProvider.UNITXT.value,
                    value=score_map.get(result.selected_option),
                    label=result.selected_option,
                    record_id=record_id,
                    thresholds=self.thresholds,
                    explanation=result.explanation,
                    additional_info={
                        "feedback": result.feedback} if result.feedback else {}
                )
            )

        aggregated_result = AggregateMetricResult.create(
            record_level_metrics)
        # return the aggregated result
        return aggregated_result
