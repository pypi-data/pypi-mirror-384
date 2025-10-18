# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

import os
from typing import Annotated, Literal

from ibm_watsonx_gov.entities.enums import Region
from ibm_watsonx_gov.utils.python_utils import get_environment_variable_value
from ibm_watsonx_gov.utils.url_mapping import (WATSONX_REGION_URLS,
                                               WOS_URL_MAPPING)
from pydantic import BaseModel, Field, model_validator


class Credentials(BaseModel):
    api_key: Annotated[str | None, Field(title="Api Key",
                                         description="The user api key. Required for using watsonx as a service and one of api_key or password is required for using watsonx on-prem software.",
                                         strip_whitespace=True,
                                         default=None)]
    region: Annotated[str | None,
                      Field(title="Region",
                            description="The watsonx cloud region. By default us-south region is used.",
                            default=Region.US_SOUTH.value)]
    url: Annotated[str, Field(title="watsonx url",
                              description="The watsonx url. Required for using watsonx on-prem software.",
                              default=None)]
    service_instance_id:  Annotated[str | None, Field(title="Service instance id",
                                                      description="The watsonx.governance service instance id.",
                                                      default=None)]
    username: Annotated[str | None, Field(title="User name",
                                          description="The user name. Required for using watsonx on-prem software.",
                                          default=None)]
    password: Annotated[str | None, Field(title="Password",
                                          description="The user password. One of api_key or password is required for using watsonx on-prem software.",
                                          default=None)]
    token: Annotated[str | None, Field(title="Token",
                                       description="The bearer token.",
                                       default=None)]
    version: Annotated[str | None, Field(title="Version",
                                         description="The watsonx on-prem software version. Required for using watsonx on-prem software.",
                                         default=None,
                                         examples=["5.2"])]
    disable_ssl: Annotated[bool, Field(title="Disable ssl",
                                       description="The flag to disable ssl.",
                                       default=False)]
    scope_id: Annotated[str | None, Field(title="Scope ID",
                                          description="The scope identifier.",
                                          default=None)]
    scope_collection_type: Annotated[Literal["accounts", "subscriptions", "services", "products", "externalservices"] | None, Field(title="Scope Collection Type",
                                                                                                                                    description="Scope collection type of item(s).",
                                                                                                                                    default=None)]

    @model_validator(mode="after")
    def validate_credentials(self):
        if self.version:  # on-prem
            if not self.url:
                raise ValueError("The url value is required.")
            if not self.username and not self.token:
                raise ValueError("The username value is required.")
            if not (self.api_key or self.password) and not self.token:
                raise ValueError(
                    "One of api_key or password value is required.")
        else:
            if not (self.api_key or self.token):
                raise ValueError("One of api_key or token value is required.")
            if self.url:
                url_map = WOS_URL_MAPPING.get(self.url)
                if not url_map:
                    raise ValueError(
                        f"The url {self.url} is invalid. Please provide a valid watsonx.governance service url.")
                self.region = url_map.region
            else:
                url_map = WATSONX_REGION_URLS.get(self.region)
                if not url_map:
                    raise ValueError(
                        f"The region {self.region} is invalid. Please provide a valid watsonx.governance region. Supported regions are {Region.values()}")
                self.url = url_map.wxg_url
            if self.region == Region.AP_SOUTH.value:
                if not self.scope_id:
                    raise ValueError(
                        "The scope_id is required when using ap-south region. Please provide a valid value.")
                if not self.scope_collection_type:
                    raise ValueError(
                        "The scope_collection_type is required when using ap-south region. Please provide a valid value.")

        return self

    @classmethod
    def create_from_env(cls):
        region = get_environment_variable_value(
            ["WATSONX_REGION"])
        # possible API key environment variable names
        api_key = get_environment_variable_value(
            ["WXG_API_KEY", "WATSONX_APIKEY"])
        username = get_environment_variable_value(
            ["WXG_USERNAME", "WATSONX_USERNAME"])
        password = get_environment_variable_value(["WATSONX_PASSWORD"])
        version = get_environment_variable_value(
            ["WXG_VERSION", "WATSONX_VERSION"])
        token = get_environment_variable_value(["WATSONX_TOKEN"])

        if version:  # on-prem
            url = get_environment_variable_value(["WATSONX_URL"])
            if not url:
                raise ValueError(
                    "The watsonx url is required and should be set using WATSONX_URL environment variable.")
            if not (token or (username and (api_key or password))):
                raise ValueError(
                    "One of token or username api key or password combination is required. These can be set using WATSONX_TOKEN, WATSONX_USERNAME, WATSONX_APIKEY, WATSONX_PASSWORD environment variables"
                )
            if not token:
                if not username:
                    raise ValueError(
                        "The username is required and should be set using WATSONX_USERNAME environment variable.")
                if not (api_key or password):
                    raise ValueError(
                        "One of api_key or password is required and should be set using WATSONX_APIKEY or WATSONX_PASSWORD environment variable.")
        else:
            url = os.getenv("WXG_URL")

            if url:
                url_map = WOS_URL_MAPPING.get(url)
                if not url_map:
                    raise ValueError(
                        f"The url {url} is invalid. Please provide a valid watsonx.governance service url.")
                region = url_map.region
            else:
                if not region:
                    region = Region.US_SOUTH.value

                url_map = WATSONX_REGION_URLS.get(region)
                if not url_map:
                    raise ValueError(
                        f"The region {region} is invalid. Supported regions are {Region.values()}. Please provide a valid watsonx.governance region in WATSONX_REGION environment varaible.")

                url = url_map.wxg_url

            if not (api_key or token):
                raise ValueError(
                    "The api_key or token is required and should be set using WATSONX_APIKEY or WATSONX_TOKEN environment variable.")

        disable_ssl = os.getenv("WATSONX_DISABLE_SSL", False)

        return Credentials(
            region=region,
            api_key=api_key,
            url=url,
            service_instance_id=os.getenv("WXG_SERVICE_INSTANCE_ID"),
            username=username,
            password=password,
            token=token,
            version=version,
            disable_ssl=disable_ssl
        )


class WxAICredentials(BaseModel):
    """
    Defines the WxAICredentials class to specify the watsonx.ai server details.

    Examples:
        1. Create WxAICredentials with default parameters. By default Dallas region is used.
            .. code-block:: python

                wxai_credentials = WxAICredentials(api_key="...")

        2. Create WxAICredentials by specifying region url.
            .. code-block:: python

                wxai_credentials = WxAICredentials(api_key="...",
                                                   url="https://au-syd.ml.cloud.ibm.com")

        3. Create WxAICredentials by reading from environment variables.
            .. code-block:: python

                os.environ["WATSONX_APIKEY"] = "..."
                # [Optional] Specify watsonx region specific url. Default is https://us-south.ml.cloud.ibm.com .
                os.environ["WATSONX_URL"] = "https://eu-gb.ml.cloud.ibm.com"
                wxai_credentials = WxAICredentials.create_from_env()

        4. Create WxAICredentials for on-prem.
            .. code-block:: python

                wxai_credentials = WxAICredentials(url="https://<hostname>",
                                                   username="..."
                                                   api_key="...",
                                                   version="5.2")

        5. Create WxAICredentials by reading from environment variables for on-prem.
            .. code-block:: python

                os.environ["WATSONX_URL"] = "https://<hostname>"
                os.environ["WATSONX_VERSION"] = "5.2"
                os.environ["WATSONX_USERNAME"] = "..."
                os.environ["WATSONX_APIKEY"] = "..."
                # Only one of api_key or password is needed
                #os.environ["WATSONX_PASSWORD"] = "..."
                wxai_credentials = WxAICredentials.create_from_env()
    """
    url: Annotated[str, Field(
        title="watsonx.ai url",
        description="The url for watsonx ai service",
        default="https://us-south.ml.cloud.ibm.com",
        examples=[
            "https://us-south.ml.cloud.ibm.com",
            "https://eu-de.ml.cloud.ibm.com",
            "https://eu-gb.ml.cloud.ibm.com",
            "https://jp-tok.ml.cloud.ibm.com",
            "https://au-syd.ml.cloud.ibm.com",
        ]
    )]
    api_key: Annotated[str | None, Field(title="Api Key",
                                         description="The user api key. Required for using watsonx as a service and one of api_key or password is required for using watsonx on-prem software.",
                                         strip_whitespace=True,
                                         default=None)]
    version: Annotated[str | None, Field(title="Version",
                                         description="The watsonx on-prem software version. Required for using watsonx on-prem software.",
                                         default=None)]
    username: Annotated[str | None, Field(title="User name",
                                          description="The user name. Required for using watsonx on-prem software.",
                                          default=None)]
    password: Annotated[str | None, Field(title="Password",
                                          description="The user password. One of api_key or password is required for using watsonx on-prem software.",
                                          default=None)]
    instance_id: Annotated[str | None, Field(title="Instance id",
                                             description="The watsonx.ai instance id. Default value is openshift.",
                                             default="openshift")]

    @classmethod
    def create_from_env(cls):
        # possible API key environment variable names
        api_key = get_environment_variable_value(
            ["WXAI_API_KEY", "WATSONX_APIKEY", "WXG_API_KEY"])

        username = get_environment_variable_value(
            ["WXAI_USERNAME", "WATSONX_USERNAME", "WXG_USERNAME"])

        version = get_environment_variable_value(
            ["WXAI_VERSION", "WATSONX_VERSION", "WXG_VERSION"])

        url = get_environment_variable_value(
            ["WXAI_URL", "WATSONX_URL"])

        password = get_environment_variable_value(["WATSONX_PASSWORD"])

        instance_id = get_environment_variable_value(
            ["WATSONX_INSTANCE_ID"], "openshift")

        if version:  # on-prem
            url = get_environment_variable_value(["WATSONX_URL"])
            if not url:
                raise ValueError(
                    "The watsonx url is required and should be set using WATSONX_URL environment variable.")
            if not username:
                raise ValueError(
                    "The username is required and should be set using WATSONX_USERNAME environment variable.")
            if not (api_key or password):
                raise ValueError(
                    "One of api_key or password is required and should be set using WATSONX_APIKEY or WATSONX_PASSWORD environment variable.")
        else:
            # Check the url & update it
            if url in WOS_URL_MAPPING.keys():
                url = WOS_URL_MAPPING.get(url).wml_url

            # If the url environment variable is not found, use the default
            if not url:
                url = "https://us-south.ml.cloud.ibm.com"

            if not api_key:
                raise ValueError(
                    "The api_key is required and should be set using WATSONX_APIKEY environment variable.")

        credentials = {
            "url": url,
            "api_key": api_key,
            "version": version,
            "username": username,
            "password": password,
            "instance_id": instance_id
        }

        return WxAICredentials(
            **credentials
        )


class WxGovConsoleCredentials(BaseModel):
    """
    This class holds the authentication credentials required to connect to the watsonx Governance Console.

    Examples:
        1. Create credentials manually:
            .. code-block:: python

                credentials = WxGovConsoleCredentials(
                    url="https://governance-console.example.com",
                    username="admin",
                    password="securepassword",
                    api_key="optional-api-key"
                )

        2. Create credentials using environment variables:
            .. code-block:: python

                import os

                os.environ['WXGC_URL'] = "https://governance-console.example.com"
                os.environ['WXGC_USERNAME'] = "admin"
                os.environ['WXGC_PASSWORD'] = "securepassword"
                os.environ['WXGC_API_KEY'] = "optional-api-key"  # Optional

                credentials = WxGovConsoleCredentials.create_from_env()
    """
    url: str = Field(
        description="The base URL of the watsonx Governance Console.")
    username: str = Field(description="The username used for authentication.")
    password: str = Field(description="The password used for authentication.")
    api_key: str | None = Field(
        default=None, description="Optional API key for token-based authentication.")

    @classmethod
    def create_from_env(cls):
        return WxGovConsoleCredentials(
            url=os.getenv("WXGC_URL"),
            username=os.getenv("WXGC_USERNAME"),
            password=os.getenv("WXGC_PASSWORD"),
            api_key=os.getenv("WXGC_API_KEY"),
        )


class RITSCredentials(BaseModel):
    hostname: Annotated[
        str | None,
        Field(description="The rits hostname",
              default="https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com"),
    ]
    api_key: str

    @classmethod
    def create_from_env(cls):
        api_key = os.getenv("RITS_API_KEY")
        rits_host = os.getenv(
            "RITS_HOST", "https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com")

        return RITSCredentials(
            hostname=rits_host,
            api_key=api_key,
        )


class OpenAICredentials(BaseModel):
    """
    Defines the OpenAICredentials class to specify the OpenAI server details.

    Examples:
        1. Create OpenAICredentials with default parameters. By default Dallas region is used.
            .. code-block:: python

                openai_credentials = OpenAICredentials(api_key=api_key,
                                                       url=openai_url)

        2. Create OpenAICredentials by reading from environment variables.
            .. code-block:: python

                os.environ["OPENAI_API_KEY"] = "..."
                os.environ["OPENAI_URL"] = "..."
                openai_credentials = OpenAICredentials.create_from_env()
    """
    url: str | None
    api_key: str | None

    @classmethod
    def create_from_env(cls):
        return OpenAICredentials(
            url=os.getenv("OPENAI_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )


class PortKeyCredentials(BaseModel):
    """
    Defines the PortKeyCredentials class to specify the PortKey Gateway details.

    Examples:
        1. Create PortKeyCredentials with default parameters.
            .. code-block:: python

                portkey_credentials = PortKeyCredentials(api_key=api_key,
                                                        url=portkey_url,
                                                        provider_api_key=provider_api_key,
                                                        provider=provider_name)

        2. Create PortKeyCredentials by reading from environment variables.
            .. code-block:: python

                os.environ["PORTKEY_API_KEY"] = "..."
                os.environ["PORTKEY_URL"] = "..."
                os.environ["PORTKEY_PROVIDER_API_KEY"] = "..."
                os.environ["PORTKEY_PROVIDER_NAME"] = "..."
                portkey_credentials = PortKeyCredentials.create_from_env()
    """
    url: Annotated[str | None, Field(
        description="PortKey url. This attribute can be read from `PORTKEY_URL` environment variable.")]
    api_key: Annotated[str | None, Field(
        description="API key for PortKey. This attribute can be read from `PORTKEY_API_KEY` environment variable.")]
    provider_api_key: Annotated[str | None, Field(
        description="API key for the provider. This attribute can be read from `PORTKEY_PROVIDER_API_KEY` environment variable.")]
    provider: Annotated[str | None, Field(
        description="The provider name. This attribute can be read from `PORTKEY_PROVIDER_NAME` environment variable.")]

    @classmethod
    def create_from_env(cls):
        return PortKeyCredentials(
            url=os.getenv("PORTKEY_URL"),
            api_key=os.getenv("PORTKEY_API_KEY"),
            provider_api_key=os.getenv("PORTKEY_PROVIDER_API_KEY"),
            provider=os.getenv("PORTKEY_PROVIDER_NAME")
        )


class AzureOpenAICredentials(BaseModel):
    url: Annotated[str | None, Field(
        description="Azure OpenAI url. This attribute can be read from `AZURE_OPENAI_HOST` environment variable.",
        serialization_alias="azure_openai_host")]
    api_key: Annotated[str | None, Field(
        description="API key for Azure OpenAI. This attribute can be read from `AZURE_OPENAI_API_KEY` environment variable.")]
    api_version: Annotated[str | None, Field(
        description="The model API version from Azure OpenAI. This attribute can be read from `AZURE_OPENAI_API_VERSION` environment variable.")]

    @classmethod
    def create_from_env(cls):
        return AzureOpenAICredentials(
            url=os.getenv("AZURE_OPENAI_HOST"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )


class GoogleAIStudioCredentials(BaseModel):
    """
    Defines the GoogleAIStudioCredentials class for accessing Google AI Studio using an API key.

    Examples:
        1. Create credentials manually:
            .. code-block:: python

                google_credentials = GoogleAIStudioCredentials(api_key="your-api-key")

        2. Create credentials from environment:
            .. code-block:: python

                os.environ["GOOGLE_API_KEY"] = "your-api-key"
                google_credentials = GoogleAIStudioCredentials.create_from_env()
    """
    api_key: Annotated[str, Field(
        title="Api Key",
        description="The Google AI Studio key. This attribute can be read from GOOGLE_API_KEY environment variable when creating GoogleAIStudioCredentials from environment.")]

    @classmethod
    def create_from_env(cls):
        return cls(api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))

    @model_validator(mode="after")
    def validate_credentials(self):
        if not self.api_key or not self.api_key.strip():
            raise ValueError(
                "The api_key is missing or empty. Please provide a valid value")
        return self


class VertexAICredentials(BaseModel):
    """
    Defines the VertexAICredentials class for accessing Vertex AI using service account credentials.

    Examples:
        1. Create credentials manually:
            .. code-block:: python

                vertex_credentials = VertexAICredentials(
                    credentials_path="path/to/service_account.json",
                    project_id="my-gcp-project",
                    location="us-central1"
                )

        2. Create credentials from environment:
            .. code-block:: python

                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/service_account.json"
                os.environ["GOOGLE_CLOUD_PROJECT"] = "my-gcp-project"
                os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

                vertex_ai_credentials = VertexAICredentials.create_from_env()
    """
    credentials_path: Annotated[str, Field(
        title="Credentials Path",
        description="Path to service-account JSON. This attribute can be read from GOOGLE_APPLICATION_CREDENTIALS environment variable when creating VertexAICredentials from environment.")]
    project_id: Annotated[str, Field(
        title="Project ID",
        description="The Google Cloud project id. This attribute can be read from GOOGLE_CLOUD_PROJECT or GCLOUD_PROJECT environment variable when creating VertexAICredentials from environment.")]
    location: Annotated[str, Field(
        title="Location",
        default="us-central1",
        description="Vertex AI region. This attribute can be read from GOOGLE_CLOUD_LOCATION environment variable when creating VertexAICredentials from environment. By default us-central1 location is used.",
        examples=["us-central1", "europe-west4"])]

    @classmethod
    def create_from_env(cls):
        return cls(
            credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv(
                "GCLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )

    @model_validator(mode="after")
    def validate_credentials(self):
        missing_fields = []
        if not self.credentials_path:
            missing_fields.append("credentials_path")
        if not self.project_id:
            missing_fields.append("project_id")

        if missing_fields:
            raise ValueError(
                f"Missing required Vertex AI fields: {', '.join(missing_fields)}, Please provide the missing fields ")
        return self


class AWSBedrockCredentials(BaseModel):
    """
    Defines the AWSBedrockCredentials class for accessing AWS Bedrock using environment variables or manual input.

    Examples:
        1. Create credentials manually:
            .. code-block:: python

                credentials = AWSBedrockCredentials(
                    aws_access_key_id="your-access-key-id",
                    aws_secret_access_key="your-secret-access-key",
                    aws_region_name="us-east-1",
                    aws_session_token="optional-session-token"
                )

        2. Create credentials from environment:
            .. code-block:: python

                os.environ["AWS_ACCESS_KEY_ID"] = "your-access-key-id"
                os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
                os.environ["AWS_SECRET_ACCESS_KEY"] = "your-secret-access-key"

                credentials = AWSBedrockCredentials.create_from_env()
    """

    aws_access_key_id: Annotated[str | None, Field(
        title="AWS Access Key ID",
        description="The AWS access key id. This attribute value will be read from AWS_ACCESS_KEY_ID environment variable when creating AWSBedrockCredentials from environment."
    )]
    aws_secret_access_key: Annotated[str | None, Field(
        title="AWS Secret Access Key",
        description="The AWS secret access key. This attribute value will be read from AWS_SECRET_ACCESS_KEY environment variable when creating AWSBedrockCredentials from environment."
    )]
    aws_region_name: Annotated[str, Field(
        title="AWS Region",
        default="us-east-1",
        description="AWS region. This attribute value will be read from AWS_DEFAULT_REGION environment variable when creating AWSBedrockCredentials from environment.",
        examples=["us-east-1", "eu-west-1"]
    )]
    aws_session_token: Annotated[str | None, Field(
        title="AWS Session Token",
        description="Optional AWS session token for temporary credentials."
    )]

    @classmethod
    def create_from_env(cls):
        return cls(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN")
        )

    @model_validator(mode="after")
    def validate_credentials(self):
        missing_fields = []
        if not self.aws_access_key_id:
            missing_fields.append("aws_access_key_id")
        if not self.aws_secret_access_key:
            missing_fields.append("aws_secret_access_key")

        if missing_fields:
            raise ValueError(
                f"Missing required AWS credentials: {', '.join(missing_fields)}. "
                f"Please provide the missing fields or set them via environment variables."
            )
