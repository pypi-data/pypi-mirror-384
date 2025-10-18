# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------
from typing import Any, Dict, List, Optional, Union

from datasets import Dataset
from ibm_watsonx_gov.entities.llm_judge import LLMJudge
from unitxt.inference import (InferenceEngine, PackageRequirementsMixin,
                              StandardAPIParamsMixin,
                              TextGenerationInferenceOutput,
                              get_model_and_label_id)


class PortKeyInferenceEngine(
    InferenceEngine, StandardAPIParamsMixin, PackageRequirementsMixin
):
    label: str = "portkey"
    _requirements_list = {
        "portkey-ai": "Install portkey-ai package using 'pip install --upgrade portkey-ai"
    }
    model: str = None
    credentials: Dict[str, str] = {}

    def get_engine_id(self):
        return get_model_and_label_id(self.model, self.label)

    def prepare_engine(self):
        from portkey_ai import Portkey

        self.client = Portkey(
            api_key=self.credentials["api_key"],
            base_url=self.credentials.get("base_url", None),
            provider=self.credentials.get("provider"),
            Authorization="Bearer " + self.credentials["provider_api_key"],
        )

    def _infer(
        self,
        dataset: Union[List[Dict[str, Any]], Dataset],
        return_meta_data: bool = False,
    ) -> Union[List[str], List[TextGenerationInferenceOutput]]:
        args = self.to_dict([StandardAPIParamsMixin])
        results = []
        for instance in dataset:
            messages = self.to_messages(instance)
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model
            )
            results.append(response.choices[0].message.content)

        return results
