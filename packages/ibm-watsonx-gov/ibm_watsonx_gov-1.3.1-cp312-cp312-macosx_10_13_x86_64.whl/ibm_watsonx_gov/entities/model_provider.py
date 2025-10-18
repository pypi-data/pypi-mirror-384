# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

from typing import Annotated

from ibm_watsonx_gov.entities.credentials import (AWSBedrockCredentials,
                                                  AzureOpenAICredentials,
                                                  GoogleAIStudioCredentials,
                                                  OpenAICredentials,
                                                  PortKeyCredentials,
                                                  RITSCredentials,
                                                  VertexAICredentials,
                                                  WxAICredentials)
from ibm_watsonx_gov.entities.enums import ModelProviderType
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self


class ModelProvider(BaseModel):
    type: Annotated[
        ModelProviderType, Field(
            description="The type of model provider.")
    ]


class WxAIModelProvider(ModelProvider):
    """
    This class represents a model provider configuration for IBM watsonx.ai. It includes the provider type and
    credentials required to authenticate and interact with the watsonx.ai platform. If credentials are not explicitly
    provided, it attempts to load them from environment variables.

    Examples:
        1. Create provider using credentials object:
            .. code-block:: python

                credentials = WxAICredentials(
                    url="https://us-south.ml.cloud.ibm.com",
                    api_key="your-api-key"
                )
                provider = WxAIModelProvider(credentials=credentials)

        2. Create provider using environment variables:
            .. code-block:: python

                import os

                os.environ['WATSONX_URL'] = "https://us-south.ml.cloud.ibm.com"
                os.environ['WATSONX_APIKEY'] = "your_api_key"

                provider = WxAIModelProvider()
    """

    type: Annotated[
        ModelProviderType,
        Field(
            description="The type of model provider.",
            default=ModelProviderType.IBM_WATSONX_AI,
            frozen=True
        )
    ]
    credentials: Annotated[
        WxAICredentials | None,
        Field(
            default=None,
            description="The credentials used to authenticate with watsonx.ai. If not provided, they will be loaded from environment variables."
        )
    ]

    @model_validator(mode="after")
    def create_credentials_from_env(self) -> Self:
        if self.credentials is None:
            try:
                self.credentials = WxAICredentials.create_from_env()
            except ValueError:
                self.credentials = None
        return self


class OpenAIModelProvider(ModelProvider):
    type: Annotated[ModelProviderType,
                    Field(description="The type of model provider.",
                          default=ModelProviderType.OPENAI, frozen=True)]
    credentials: Annotated[OpenAICredentials | None, Field(
        description="OpenAI credentials. This can also be set by using `OPENAI_API_KEY` environment variable.", default=None)]

    @model_validator(mode="after")
    def create_credentials_from_env(self) -> Self:
        if self.credentials is None:
            self.credentials = OpenAICredentials.create_from_env()
        return self


class PortKeyModelProvider(ModelProvider):
    type: Annotated[ModelProviderType,
                    Field(description="The type of model provider.",
                          default=ModelProviderType.PORTKEY, frozen=True)]
    credentials: Annotated[PortKeyCredentials | None, Field(
        description="PortKey credentials.", default=None)]

    @model_validator(mode="after")
    def create_credentials_from_env(self) -> Self:
        if self.credentials is None:
            self.credentials = PortKeyCredentials.create_from_env()
        return self


class AzureOpenAIModelProvider(ModelProvider):
    type: Annotated[ModelProviderType,
                    Field(description="The type of model provider.",
                          default=ModelProviderType.AZURE_OPENAI, frozen=True)]
    credentials: Annotated[AzureOpenAICredentials | None, Field(
        description="Azure OpenAI credentials.", default=None
    )]

    @model_validator(mode="after")
    def create_credentials_from_env(self) -> Self:
        if self.credentials is None:
            self.credentials = AzureOpenAICredentials.create_from_env()
        return self


class RITSModelProvider(ModelProvider):
    type: Annotated[ModelProviderType,
                    Field(description="The type of model provider.",
                          default=ModelProviderType.RITS, frozen=True)]
    credentials: Annotated[RITSCredentials | None, Field(
        description="RITS credentials.", default=None
    )]

    @model_validator(mode="after")
    def create_credentials_from_env(self) -> Self:
        if self.credentials is None:
            self.credentials = RITSCredentials.create_from_env()
        return self


class VertexAIModelProvider(ModelProvider):
    """
    Represents a model provider using Vertex AI.

    Examples:
        1. Create provider using credentials object:
            .. code-block:: python

                provider = VertexAIModelProvider(
                    credentials=VertexAICredentials(
                        credentials_path="path/to/key.json",
                        project_id="your-project",
                        location="us-central1" 
                    )
                )

        2. Create provider using environment variables:
            .. code-block:: python

                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/path/to/service_account.json"
                os.environ['GOOGLE_CLOUD_PROJECT'] = "your-project"
                os.environ['GOOGLE_CLOUD_LOCATION'] = "us-central1" # This is optional field, by default us-central1 location is selected

                provider = VertexAIModelProvider()
    """

    type: Annotated[ModelProviderType, Field(
        description="The type of model provider.",
        default=ModelProviderType.VERTEX_AI,
        frozen=True
    )]
    credentials: Annotated[VertexAICredentials | None, Field(
        description="Vertex AI credentials.", default=None
    )]

    @model_validator(mode="after")
    def create_credentials_from_env(self) -> "VertexAIModelProvider":
        if self.credentials is None:
            self.credentials = VertexAICredentials.create_from_env()
        return self


class GoogleAIStudioModelProvider(ModelProvider):
    """
    Represents a model provider using Google AI Studio.

    Examples:
        1. Create provider using credentials object:
            .. code-block:: python

                provider = GoogleAIStudioModelProvider(
                    credentials=GoogleAIStudioCredentials(api_key="api-key")
                )

        2. Create provider using environment variables:
            .. code-block:: python

                os.environ['GOOGLE_API_KEY'] = "your_api_key"

                provider = GoogleAIStudioModelProvider()
    """

    type: Annotated[ModelProviderType, Field(
        description="The type of model provider.",
        default=ModelProviderType.GOOGLE_AI_STUDIO,
        frozen=True
    )]
    credentials: Annotated[GoogleAIStudioCredentials | None, Field(
        description="Google AI Studio credentials.", default=None
    )]

    @model_validator(mode="after")
    def create_credentials_from_env(self) -> "GoogleAIStudioModelProvider":
        if self.credentials is None:
            self.credentials = GoogleAIStudioCredentials.create_from_env()
        return self


class AWSBedrockModelProvider(ModelProvider):
    """
    Represents a model provider using Amazon Bedrock.

    Examples:
        1. Create provider using credentials object:
            .. code-block:: python

                provider = AWSBedrockModelProvider(
                    credentials=AWSBedrockCredentials(
                        aws_access_key_id="your-access-key-id",
                        aws_secret_access_key="your-secret-access-key",
                        aws_region_name="us-east-1",
                        aws_session_token="optional-session-token"
                    )
                )

        2. Create provider using environment variables:
            .. code-block:: python

                os.environ['AWS_ACCESS_KEY_ID'] = "your-access-key-id"
                os.environ['AWS_SECRET_ACCESS_KEY'] = "your-secret-access-key"
                os.environ['AWS_SESSION_TOKEN'] = "optional-session-token"  # Optional
                os.environ['AWS_DEFAULT_REGION'] = "us-east-1"
                provider = AWSBedrockModelProvider()
    """

    type: Annotated[ModelProviderType, Field(
        description="The type of model provider.",
        default=ModelProviderType.AWS_BEDROCK,
        frozen=True
    )]
    credentials: Annotated[AWSBedrockCredentials | None, Field(
        description="AWS Bedrock credentials.", default=None
    )]

    @model_validator(mode="after")
    def create_credentials_from_env(self) -> "AWSBedrockModelProvider":
        if self.credentials is None:
            self.credentials = AWSBedrockCredentials.create_from_env()
        return self


class CustomModelProvider(ModelProvider):
    """
    Defines the CustomModelProvider class.

    This class represents a custom model provider, typically used when integrating with non-standard or user-defined
    model backends. It sets the provider type to `CUSTOM` by default.

    Examples:
        1. Create a custom model provider:
            .. code-block:: python

                provider = CustomModelProvider()

        2. Use with a custom foundation model:
            .. code-block:: python

                custom_model = CustomFoundationModel(
                    scoring_fn=my_scoring_function,
                    provider=CustomModelProvider()
                )

    Attributes:
        type (ModelProviderType): The type of model provider. Always set to `ModelProviderType.CUSTOM`.
    """
    type: Annotated[ModelProviderType, Field(
        description="The type of model provider.", default=ModelProviderType.CUSTOM)]
