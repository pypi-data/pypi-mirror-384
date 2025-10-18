# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

from typing import Annotated, Any, Callable, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator
from typing_extensions import Self

from ibm_watsonx_gov.entities.model_provider import (
    AWSBedrockModelProvider, AzureOpenAIModelProvider, CustomModelProvider,
    GoogleAIStudioModelProvider, ModelProvider, OpenAIModelProvider,
    PortKeyModelProvider, RITSModelProvider, VertexAIModelProvider,
    WxAIModelProvider)
from ibm_watsonx_gov.utils.python_utils import get_environment_variable_value


class FoundationModel(BaseModel):
    """
    Defines the base FoundationModel class.
    """
    model_name: Annotated[
        str | None,
        Field(
            description="The name of the foundation model.",
            default=None,
        ),
    ]
    provider: Annotated[
        ModelProvider, Field(
            description="The provider of the foundation model.")
    ]
    model_config = ConfigDict(protected_namespaces=())


class FoundationModelInfo(BaseModel):
    """
    Represents a foundation model used in an experiment.
    """
    model_name: Annotated[Optional[str], Field(
        description="The name of the foundation model.", default=None)]

    model_id: Annotated[Optional[str], Field(
        description="The id of the foundation model.", default=None)]
    provider: Annotated[str, Field(
        description="The provider of the foundation model.")]
    type: Annotated[str, Field(description="The type of foundation model.", example=[
                               "chat", "embedding", "text-generation"])]

    def __eq__(self, other):
        if isinstance(other, FoundationModelInfo):
            return (
                self.model_name == other.model_name and
                self.model_id == other.model_id and
                self.provider == other.provider and
                self.type == other.type
            )
        return False

    def __hash__(self):
        return hash((self.model_name, self.model_id, self.provider, self.type))


class WxAIFoundationModel(FoundationModel):
    """
    The IBM watsonx.ai foundation model details

    To initialize the foundation model, you can either pass in the credentials directly or set the environment.
    You can follow these examples to create the provider.

    Examples:
        1. Create foundation model by specifying the credentials during object creation:
            .. code-block:: python

                # Specify the credentials during object creation
                wx_ai_foundation_model = WxAIFoundationModel(
                    model_id="ibm/granite-3-3-8b-instruct",
                    project_id=<PROJECT_ID>,
                    provider=WxAIModelProvider(
                        credentials=WxAICredentials(
                            url=wx_url, # This is optional field, by default US-Dallas region is selected
                            api_key=wx_apikey,
                        )
                    )
                )

        2. Create foundation model by setting the credentials environment variables:
            * The api key can be set using one of the environment variables ``WXAI_API_KEY``, ``WATSONX_APIKEY``, or ``WXG_API_KEY``. These will be read in the order of precedence.
            * The url is optional and will be set to US-Dallas region by default. It can be set using one of the environment variables ``WXAI_URL``, ``WATSONX_URL``, or ``WXG_URL``. These will be read in the order of precedence.

            .. code-block:: python

                wx_ai_foundation_model = WxAIFoundationModel(
                    model_id="ibm/granite-3-3-8b-instruct",
                    project_id=<PROJECT_ID>,
                )

        3. Create foundation model by specifying watsonx.governance software credentials during object creation:
            .. code-block:: python

                wx_ai_foundation_model = WxAIFoundationModel(
                    model_id="ibm/granite-3-3-8b-instruct",
                    project_id=project_id,
                    provider=WxAIModelProvider(
                        credentials=WxAICredentials(
                            url=wx_url,
                            api_key=wx_apikey,
                            username=wx_username,
                            version=wx_version,
                        )
                    )
                )

        4. Create foundation model by setting watsonx.governance software credentials environment variables:
            * The api key can be set using one of the environment variables ``WXAI_API_KEY``, ``WATSONX_APIKEY``, or ``WXG_API_KEY``. These will be read in the order of precedence.
            * The url can be set using one of these environment variable ``WXAI_URL``, ``WATSONX_URL``, or ``WXG_URL``. These will be read in the order of precedence.
            * The username can be set using one of these environment variable ``WXAI_USERNAME``, ``WATSONX_USERNAME``, or ``WXG_USERNAME``. These will be read in the order of precedence.
            * The version of watsonx.governance software can be set using one of these environment variable ``WXAI_VERSION``, ``WATSONX_VERSION``, or ``WXG_VERSION``. These will be read in the order of precedence.

            .. code-block:: python

                wx_ai_foundation_model = WxAIFoundationModel(
                    model_id="ibm/granite-3-3-8b-instruct",
                    project_id=project_id,
                )

    """
    model_id: Annotated[
        str, Field(description="The unique identifier for the watsonx.ai model.")
    ]
    project_id: Annotated[
        str | None,
        Field(description="The project ID associated with the model.", default=None),
    ]
    space_id: Annotated[
        str | None,
        Field(description="The space ID associated with the model.", default=None),
    ]
    provider: Annotated[
        WxAIModelProvider,
        Field(
            description="The provider of the model.", default_factory=WxAIModelProvider
        ),
    ]

    @model_validator(mode="after")
    def get_params_from_env(self) -> Self:
        if self.space_id is None and self.project_id is None:
            try:
                self.project_id = get_environment_variable_value(
                    ["WX_PROJECT_ID", "WATSONX_PROJECT_ID"])
            except ValueError:
                self.project_id = None
            if self.project_id is None:
                try:
                    self.space_id = get_environment_variable_value(
                        ["WX_SPACE_ID", "WATSONX_SPACE_ID"])
                except ValueError:
                    self.space_id = None

        return self


class OpenAIFoundationModel(FoundationModel):
    """
    The OpenAI foundation model details

    Examples:
        1. Create OpenAI foundation model by passing the credentials during object creation. Note that the url is optional and will be set to the default value for OpenAI. To change the default value, the url should be passed to ``OpenAICredentials`` object.
            .. code-block:: python

                openai_foundation_model = OpenAIFoundationModel(
                    model_id="gpt-4o-mini",
                    provider=OpenAIModelProvider(
                        credentials=OpenAICredentials(
                            api_key=api_key,
                            url=openai_url,
                        )
                    )
                )

        2. Create OpenAI foundation model by setting the credentials in environment variables:
            * ``OPENAI_API_KEY`` is used to set the api key for OpenAI.
            * ``OPENAI_URL`` is used to set the url for OpenAI

            .. code-block:: python

                openai_foundation_model = OpenAIFoundationModel(
                    model_id="gpt-4o-mini",
                )
    """
    model_id: Annotated[str, Field(description="Model name from OpenAI")]
    provider: Annotated[OpenAIModelProvider, Field(
        description="OpenAI provider", default_factory=OpenAIModelProvider)]


class PortKeyGateway(FoundationModel):
    """
    The PortKey gateway details

    Examples:
        1. Create PortKeyGateway by passing the credentials during object creation. Note that the url is optional and will be set to the default value for PortKey. To change the default value, the url should be passed to ``PortKeyCredentials`` object.
            .. code-block:: python

                port_key_gateway = PortKeyGateway(
                    model_id="gpt-4o-mini",
                    provider=PortKeyModelProvider(
                        credentials=PortKeyCredentials(
                            api_key=api_key,
                            url=openai_url,
                            provider_api_key=provider_api_key,
                            provider_name=provider_name
                        )
                    )
                )

        2. Create PortKeyGateway by setting the credentials in environment variables:
            * ``PORTKEY_API_KEY`` is used to set the api key for PortKey.
            * ``PORTKEY_URL`` is used to set the url for PortKey.
            * ``PORTKEY_PROVIDER_API_KEY`` is used to set the provider api key for PortKey.
            * ``PORTKEY_PROVIDER_NAME`` is used to set the provider name for PortKey

            .. code-block:: python

                port_key_gateway = PortKeyGateway(
                    model_id="gpt-4o-mini",
                )
    """
    model_id: Annotated[str, Field(description="Model name from the Provider")]
    provider: Annotated[PortKeyModelProvider, Field(
        description="PortKey Provider", default_factory=PortKeyModelProvider)]


class AzureOpenAIFoundationModel(FoundationModel):
    """
    The Azure OpenAI foundation model details

    Examples:
        1. Create Azure OpenAI foundation model by passing the credentials during object creation.
            .. code-block:: python

                azure_openai_foundation_model = AzureOpenAIFoundationModel(
                    model_id="gpt-4o-mini",
                    provider=AzureOpenAIModelProvider(
                        credentials=AzureOpenAICredentials(
                            api_key=azure_api_key,
                            url=azure_host_url,
                            api_version=azure_api_model_version,
                        )
                    )
                )

    2. Create Azure OpenAI foundation model by setting the credentials in environment variables:
        * ``AZURE_OPENAI_API_KEY`` is used to set the api key for OpenAI.
        * ``AZURE_OPENAI_HOST`` is used to set the url for Azure OpenAI.
        * ``AZURE_OPENAI_API_VERSION`` is uses to set the the api version for Azure OpenAI.

            .. code-block:: python

                openai_foundation_model = AzureOpenAIFoundationModel(
                    model_id="gpt-4o-mini",
                )

    """
    model_id: Annotated[str, Field(
        description="Model deployment name from Azure OpenAI")]
    provider: Annotated[AzureOpenAIModelProvider, Field(
        description="Azure OpenAI provider", default_factory=AzureOpenAIModelProvider)]


class VertexAIFoundationModel(FoundationModel):
    """
    Represents a foundation model served via Vertex AI.

    Examples:
        1. Create Vertex AI foundation model by passing the credentials during object creation.
            .. code-block:: python

                model = VertexAIFoundationModel(
                    model_id="gemini-1.5-pro-002",
                    provider=VertexAIModelProvider(
                        credentials=VertexAICredentials(
                            project_id="your-project",
                            location="us-central1", # This is optional field, by default us-central1 location is selected
                            credentials_path="/path/to/service_account.json"
                        )
                    )
                )
        2. Create Vertex AI foundation model by setting the credentials in environment variables:
            * ``GOOGLE_APPLICATION_CREDENTIALS`` is used to set the Credentials path for Vertex AI.
            * ``GOOGLE_CLOUD_PROJECT`` is used to set the Project id for Vertex AI.
            * ``GOOGLE_CLOUD_LOCATION`` is uses to set the Location for Vertex AI. By default us-central1 location is used when GOOGLE_CLOUD_LOCATION is not provided .

                .. code-block:: python

                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/service_account.json"
                    os.environ["GOOGLE_CLOUD_PROJECT"] = "my-gcp-project"
                    os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

                    model = VertexAIFoundationModel(
                        model_id="gemini/gpt-4o-mini",
                    )
    """

    model_id: Annotated[str, Field(
        title="Model id",
        description="Model name for Vertex AI. Must be a valid Vertex AI model identifier or a fully-qualified publisher path",
        examples=["gemini-1.5-pro-002"],
    )]
    provider: Annotated[VertexAIModelProvider, Field(
        title="Provider",
        description="Vertex AI provider.",
        default_factory=VertexAIModelProvider
    )]


class GoogleAIStudioFoundationModel(FoundationModel):
    """
    Represents a foundation model served via Google AI Studio.

    Examples:
        1. Create Google AI Studio foundation model by passing the credentials during object creation.
            .. code-block:: python

                model = GoogleAIStudioFoundationModel(
                    model_id="gemini-1.5-pro-002",
                    provider=GoogleAIStudioModelProvider(
                        credentials=GoogleAIStudioCredentials(api_key="your_api_key")
                    )
                )
        2. Create Google AI Studio foundation model by setting the credentials in environment variables:
            * ``GOOGLE_API_KEY`` OR ``GEMINI_API_KEY`` is used to set the Credentials path for Vertex AI.
                .. code-block:: python

                    model = GoogleAIStudioFoundationModel(
                        model_id="gemini/gpt-4o-mini",
                    )
    """

    model_id: Annotated[str, Field(
        title="Model id",
        description="Model name for Google AI Studio. Must be a valid Google AI model identifier or a fully-qualified publisher path",
        examples=["gemini-1.5-pro-002"],
    )]
    provider: Annotated[GoogleAIStudioModelProvider, Field(
        title="Provider",
        description="Google AI Studio provider.",
        default_factory=GoogleAIStudioModelProvider
    )]


class AWSBedrockFoundationModel(BaseModel):
    """
    The Amazon Bedrock foundation model details.

    Examples:
        1. Create AWS Bedrock foundation model by passing credentials manually:
            .. code-block:: python

                bedrock_model = AWSBedrockFoundationModel(
                    model_id="anthropic.claude-v2",
                    provider=AWSBedrockModelProvider(
                        credentials=AWSBedrockCredentials(
                            aws_access_key_id="your-access-key-id",
                            aws_secret_access_key="your-secret-access-key",
                            aws_region_name="us-east-1",
                            aws_session_token="optional-session-token"
                        )
                    ),
                    parameters={
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 200,
                        "stop_sequences": ["\n"],
                        "system": "You are a concise assistant.",
                        "reasoning_effort": "high",
                        "tool_choice": "auto"
                    }
                )

        2. Create AWS Bedrock foundation model using environment variables:
            os.environ["AWS_ACCESS_KEY_ID"] = "your-access-key-id"
            os.environ["AWS_SECRET_ACCESS_KEY"] = "your-secret-access-key"
            os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

            .. code-block:: python

                bedrock_model = AWSBedrockFoundationModel(
                    model_id="anthropic.claude-v2"
                )
    """
    model_id: Annotated[str, Field(
        title="Model ID", description="The AWS Bedrock model name. It must be a valid AWS Bedrock model identifier.", examples=["anthropic.claude-v2"])

    ]

    provider: Annotated[AWSBedrockModelProvider, Field(
        title="Provider",
        description="The AWS Bedrock provider details.",
        default_factory=AWSBedrockModelProvider
    )]

    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        title="Parameters",
        description="The model parameters to be used when invoking the model. The parameters may include temperature, top_p, max_tokens, etc.."
    )


class RITSFoundationModel(FoundationModel):
    provider: Annotated[
        RITSModelProvider,
        Field(description="The provider of the model.",
              default_factory=RITSModelProvider),
    ]


class CustomFoundationModel(FoundationModel):
    """
    Defines the CustomFoundationModel class.

    This class extends the base `FoundationModel` to support custom inference logic through a user-defined scoring function.
    It is intended for use cases where the model is externally hosted and not in the list of supported frameworks.
    Examples:
        1. Define a custom scoring function and create a model:
            .. code-block:: python

                import pandas as pd

                def scoring_fn(data: pd.DataFrame):
                    predictions_list = []
                    # Custom logic to call an external LLM
                    return pd.DataFrame({"generated_text": predictions_list})                    

                model = CustomFoundationModel(
                    scoring_fn=scoring_fn
                )
    """

    _scoring_fn: Annotated[Optional[Callable], PrivateAttr(default=None)]
    provider: Annotated[
        ModelProvider,
        Field(
            description="The provider of the model.",
            default_factory=CustomModelProvider,
        ),
    ]

    def __init__(self, **data):
        scoring_fn = data.pop("scoring_fn", None)
        super().__init__(**data)
        self._scoring_fn = scoring_fn

    def model_post_init(self, context):
        if self._scoring_fn is None:
            raise ValueError("The scoring function is required.")
