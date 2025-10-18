# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

from multiprocessing.pool import ThreadPool
from typing import Annotated, Any, Callable, Dict, List, Optional, Union

from datasets import Dataset
from lazy_imports import LazyModule, load
from pydantic import Field
from tqdm import tqdm

unitxt_imports = LazyModule(
    "from unitxt.artifact import Artifact",
    "from unitxt.inference import InferenceEngine, TextGenerationInferenceOutput, get_model_and_label_id",
    name="lazy_unitxt",
)
load(unitxt_imports)

Artifact = unitxt_imports.Artifact
InferenceEngine = unitxt_imports.InferenceEngine
TextGenerationInferenceOutput = unitxt_imports.TextGenerationInferenceOutput
get_model_and_label_id = unitxt_imports.get_model_and_label_id


def run_with_imap(func):
    """
    Decorator to adapt a function for use with multiprocessing's imap.
    Ensures arguments are unpacked properly when parallelizing inference.
    """

    def inner(self, args):
        return func(self, *args)
    return inner


class CustomFnEngineParamsMixin(Artifact):
    """
    Mixin class that provides configurable parameters for the custom engine.
    - batch_size: number of instances per batch (unused, but reserved for extension).
    - timeout: optional timeout in seconds for inference requests.
    - num_parallel_requests: max number of threads used for parallel inference.
    """
    batch_size: Optional[int] = None
    timeout: Optional[float] = None
    num_parallel_requests: Optional[int] = 20


class CustomFunctionInferenceEngine(InferenceEngine, CustomFnEngineParamsMixin):
    """
    A custom inference engine that delegates prediction to a user-provided function (`scoring_fn`).
    Supports parallel execution across multiple threads and integrates seamlessly with Unitxt.
    """

    label: str = "custom_fn"
    model_name: str = "custom_fn"
    num_parallel_requests: int = 20

    scoring_fn: Callable
    context: Optional[Dict[str, Any]] = None

    def get_engine_id(self) -> str:
        """
        Return a unique engine identifier based on model_name and label.
        Used internally by Unitxt to differentiate inference engines.
        """
        return get_model_and_label_id(self.model_name, self.label)

    def prepare_engine(self):
        """
        Hook for initializing resources before inference.
        No-op here since the custom engine delegates everything to scoring_fn.
        """
        pass

    def get_return_object(self, predict_result, response, return_meta_data):
        """
        Return the prediction object in the format expected by Unitxt.
        In this implementation, the prediction is returned as-is.
        """
        return predict_result

    def _parallel_infer(
        self,
        dataset: Union[List[Dict[str, Any]], Dataset],
        infer_func,
        return_meta_data: bool = False,
    ) -> Union[List[str], List["TextGenerationInferenceOutput"]]:
        """
        Run inference on a dataset in parallel using a thread pool.
        Args:
            dataset: list of instances or HuggingFace Dataset.
            infer_func: function applied to each instance.
            return_meta_data: if True, expects TextGenerationInferenceOutput.
        Returns:
            A list of predictions or metadata objects.
        """
        inputs = [(instance, return_meta_data) for instance in dataset]
        outputs: List[Union[str, "TextGenerationInferenceOutput"]] = []
        with ThreadPool(processes=self.num_parallel_requests) as pool:
            for output in tqdm(
                pool.imap(infer_func, inputs),
                total=len(inputs),
                desc=f"Inferring with {self.__class__.__name__}",
            ):
                outputs.append(output)
        return outputs

    def _infer(
        self,
        dataset: Union[List[Dict[str, Any]], Dataset],
        return_meta_data: bool = False,
    ) -> Union[List[str], List["TextGenerationInferenceOutput"]]:
        """
        Core inference method called by Unitxt.
        Delegates to `_parallel_infer` for concurrent execution.
        """
        return self._parallel_infer(
            dataset=dataset,
            return_meta_data=return_meta_data,
            infer_func=self._score_instance,
        )

    @run_with_imap
    def _score_instance(self, instance, return_meta_data):
        """
        Run inference on a single instance using the user-provided scoring_fn.
        Handles type validation and returns a fallback object if scoring fails.
        """
        try:
            pred = self.scoring_fn(
                instance, return_meta_data, context=self.context)

            if return_meta_data and not isinstance(pred, TextGenerationInferenceOutput):
                raise TypeError(
                    "With return_meta_data=True, scoring_fn must return TextGenerationInferenceOutput."
                )
            if not return_meta_data and not isinstance(pred, str):
                raise TypeError(
                    "With return_meta_data=False, scoring_fn must return str."
                )

            return self.get_return_object(pred, response=None, return_meta_data=return_meta_data)
        except Exception:
            if return_meta_data:
                return TextGenerationInferenceOutput(
                    prediction="-", generated_text="-", input_tokens=0, output_tokens=0,
                    model_name=self.model_name, inference_type=self.label,
                )
            return "-"

    def to_dict(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Convert the engine configuration to a dictionary.
        Excludes unserializable fields like `scoring_fn` and `context` to ensure cache safety.
        """
        d = super().to_dict(*args, **kwargs)
        d.pop("scoring_fn", None)
        d.pop("context", None)
        return d
