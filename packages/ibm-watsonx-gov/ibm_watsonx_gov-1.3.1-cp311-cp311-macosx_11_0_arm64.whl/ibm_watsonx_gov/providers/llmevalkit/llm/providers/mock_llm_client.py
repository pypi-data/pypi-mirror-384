from typing import Any, Dict, List, Optional, Union

from llmevalkit.llm.output_parser import ValidatingLLMClient
from ..base import (
    GenerationMode,
    GenerationArgs,
    register_llm,
)


@register_llm("mock.output_val")
class MockLLMClient(ValidatingLLMClient):
    """
    Mock implementation of LLMClient for testing purposes.
    Assumes that the reflection is done in runtime (i.e., the generate output does not contain actionable recommendations).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = None  # No real client needed for mock

    @classmethod
    def provider_class(cls):
        # Return a dummy class for type checking
        class DummyProvider:
            pass

        return DummyProvider

    def _register_methods(self) -> None:
        # Register mock method configs
        self.set_method_config("text", "mock_text", "prompt")
        self.set_method_config("chat", "mock_chat", "prompt")
        self.set_method_config("text_async", "mock_text_async", "prompt")
        self.set_method_config("chat_async", "mock_chat_async", "prompt")

    def _setup_parameter_mapper(self) -> None:
        # No parameter mapping needed for mock
        pass

    def _parse_llm_response(self, raw: Any) -> str:
        # Return the raw value as the mock response
        return str(raw)

    def generate(
        self,
        prompt: Union[str, List[Dict[str, Any]]],
        mode: Union[str, GenerationMode] = GenerationMode.CHAT,
        generation_args: Optional[GenerationArgs] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # Return a mock response resembling expected model output
        return {
            "evidence": f"Assistant message: 'Logged in as user 55; auth token acquired.'",
            "explanation": "The user_id=55 parameter is properly grounded in the conversation history, as evidenced by the assistant's explicit statement 'Logged in as user 55.'",
            "output": 3,
            "confidence": 0.95,
            "correction": {},
        }

    async def generate_async(
        self,
        prompt: Union[str, List[Dict[str, Any]]],
        mode: Union[str, GenerationMode] = GenerationMode.CHAT_ASYNC,
        generation_args: Optional[GenerationArgs] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # Return a mock async response resembling expected model output
        return {
            "evidence": f"Assistant message: 'Logged in as user 55; auth token acquired.'",
            "explanation": "The user_id=55 parameter is properly grounded in the conversation history, as evidenced by the assistant's explicit statement 'Logged in as user 55.'",
            "output": 3,
            "confidence": 0.95,
            "correction": {},
        }
