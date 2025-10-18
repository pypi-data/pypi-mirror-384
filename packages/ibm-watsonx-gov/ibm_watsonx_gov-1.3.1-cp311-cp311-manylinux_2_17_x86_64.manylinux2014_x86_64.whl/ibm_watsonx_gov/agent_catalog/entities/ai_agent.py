# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------
import warnings

from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any, Annotated, Union, List, Type
from pydantic_core import PydanticCustomError
from ..utils.constants import ServiceProviderType
from ibm_watsonx_gov.tools.utils.constants import CustomToolType, PatchOperationTypes, Framework, Categories
from ibm_watsonx_gov.tools.utils.python_utils import get_base64_encoding
from ...utils.python_utils import get



class AIAgentParentApplication(BaseModel):
    inventory_id: Annotated[
        str,
        Field(
            ...,
            description="Inventory ID of the parent application."
        )
    ]
    agent_id: Annotated[
        str,
        Field(
            ...,
            description="Agent ID of the parent application"
        )
    ]

    @model_validator(mode="before")
    @classmethod
    def populate_agent_id_from_asset_id(cls,data):
        if "asset_id" in data and "agent_id" not in data:
            data["agent_id"] = data["asset_id"]
        return data


class AIAgentUsedInApplication(BaseModel):
    inventory_id: Annotated[
        str,
        Field(
            ...,
            description="Inventory ID of the application where the agent is used."
        )
    ]
    agent_id: Annotated[
        str,
        Field(
            ...,
            description="Agent ID of the application where the agent is used."
        )
    ]

    @model_validator(mode="before")
    @classmethod
    def populate_agent_id_from_asset_id(cls,data):
        if "asset_id" in data and "agent_id" not in data:
            data["agent_id"] = data["asset_id"]
        return data


class AIAgentRuntimeDetails(BaseModel):
    engine: Annotated[
        str,
        Field(
            ...,
            description="Python version required by the agent."
        )
    ]
    cpu_capacity: Annotated[
        Optional[str],
        Field(
            default=None,
            description="CPU capacity required by the agent."
        )
    ]
    memory: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Memory required by the agent."
        )
    ]


class AIAgentCodePayload(BaseModel):
    source: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Source location of the agent's code."
        )
    ]
    commit: Annotated[
        Optional[str],
        Field(
            default=None
        )
    ]
    language: Annotated[
        Optional[str],
        Field(
            default="python",
            description="Language used in the code"
        )
    ]
    source_code: Annotated[
        Optional[str],
        Field(
            ...,
            description="Source code encoded in Base64 format.",
            alias="source_code_base64"
        )
    ]
    run_time_details: Annotated[
        AIAgentRuntimeDetails,
        Field(
            ...,
            description="Runtime details required for executing the source code."
        )
    ]

    @model_validator(mode='before')
    @classmethod
    def accept_multiple_field_names(cls, data):
        if "source_code" in data and "source_code_base64" not in data:
            data["source_code_base64"] = data["source_code"]
        return data


class AIAgentEndpointPayload(BaseModel):
    url: Annotated[
        str,
        Field(
            ...,
            description="URL to access the endpoint."
        )
    ]
    headers: Annotated[
        Dict[str, str],
        Field(
            ...,
            description="Headers required to call the endpoint."
        )
    ]
    method: Annotated[
        str,
        Field(
            ...,
            description="Method to call the endpoint."
        )
    ]


class AIAgentTool(BaseModel):
    inventory_id: Annotated[
        str,
        Field(
            ...,
            description="Inventory ID of the tool where the application is used."
        )
    ]
    tool_id: Annotated[
        str,
        Field(
            ...,
            description="Tool ID of the tool where the application is used."
        )
    ]

    @model_validator(mode="before")
    @classmethod
    def populate_tool_id_from_asset_id(cls,data):
        if "asset_id" in data and "tool_id" not in data:
            data["tool_id"] = data["asset_id"]
        return data

class AIAgentDependencies(BaseModel):
    remote_services: Annotated[
        list[str],
        Field(
            ...,
        )
    ]
    run_time_packages: Annotated[
        list[str],
        Field(
            ...,
        )
    ]


class AIAgentSchema(BaseModel):
    title: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Title for schema."
        )]
    type: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Type of schema."
        )]
    properties: Annotated[
        dict,
        Field(
            ...,
            description="Properties for schema."
        )]
    required: Annotated[
        Optional[list],
        Field(
            default=None,
            description="Required for schema."
        )]


class AgentRegistrationPayload(BaseModel):
    display_name: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Unique name for displaying the agent."
        )
    ]
    agent_name: Annotated[
        str,
        Field(
            ...,
            description="Unique name for the agent"
        )
    ]
    description: Annotated[
        str,
        Field(
            ...,
            description="Short description about the agent."
        )
    ]
    inventory_id: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Inventory ID in which the asset needs to be created."
        )
    ]
    summary: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Summary of the agent."
        )
    ]
    service_provider_type: Annotated[
        Optional[ServiceProviderType],
        Field(
            default=ServiceProviderType.CUSTOM,
            description=f"Service provider type. Allowed values are: {ServiceProviderType.values()}."
        )
    ]
    framework: Annotated[
        Optional[list[Framework]],
        Field(
            default_factory=lambda: [Framework.LANGGRAPH],
            description="Specify the framework used by the agent."
        )
    ]
    category: Annotated[
        Optional[list[Categories]],
        Field(
            default_factory=lambda: [Categories.OTHER],
            description=f"Specify the category under which the agent will be classified. Allowed values are {Categories.values()}."
        )
    ]
    agent_type: Annotated[
        Optional[CustomToolType],
        Field(
            default=CustomToolType.ENDPOINT,
            description=f"Type of the agent. Allowed agent types are: {CustomToolType.values()}."
        )
    ]
    development_implementation_url: Annotated[
        Optional[str],
        Field(
            default=None,
        )
    ]
    validation_implementation_url: Annotated[
        Optional[str],
        Field(
            default=None,
        )
    ]
    implementation_url: Annotated[
        Optional[str],
        Field(
            default=None,
        )
    ]
    reusable: Annotated[
        bool,
        Field(
            default=False,
            description="Specify the agent will be reusable."
        )
    ]
    version: Annotated[
        Optional[str],
        Field(
            default=None,
        )
    ]
    parent_applications: Annotated[
        Optional[list[AIAgentParentApplication]],
        Field(
            default=None,
            description="List of parent applications"
        )
    ]
    tools: Annotated[
        Optional[list[AIAgentTool]],
        Field(
            default=None,
            description="List of tools used in this applications"
        )
    ]
    used_in_applications: Annotated[
        Optional[list[AIAgentUsedInApplication]],
        Field(
            default=None,
            description="List of applications where this application is used."
        )
    ]
    code: Annotated[
        Optional[AIAgentCodePayload],
        Field(
            default=None,
            description="Code-related information for the agent."
        )
    ]
    endpoint: Annotated[
        Optional[AIAgentEndpointPayload],
        Field(
            default=None,
            description="Endpoint-related information for the agent."
        )
    ]
    dependencies: Annotated[
        Optional[AIAgentDependencies],
        Field(
            default=None,
            description="Dependencies required by this agent."
        )
    ]
    metrics: Annotated[
        Optional[dict],
        Field(
            default=None,
            description="Metrics and their respective values."
        )
    ]
    benchmark_test: Annotated[
        Optional[dict],
        Field(
            default=None,
            description="Benchmark test details."
        )
    ]
    pricing: Annotated[
        Optional[dict],
        Field(
            default=None,
            description="Type of currency and its corresponding price."
        )
    ]
    schema_: Annotated[
        Optional[AIAgentSchema],
        Field(
            default=None,
            description="Schema information for this agent.",
            alias="schema"
        )
    ]

    environment_variables: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Environment variables required by this agent."
        )
    ]

    @model_validator(mode="before")
    @classmethod
    def check_required_fields(cls, values):
        if 'agent_name' not in values or not values['agent_name']:
            raise ValueError("Missing required field: 'agent_name'. Please provide a unique name for the agent.")
        if "agent_type" not in values:
            values["agent_type"] = CustomToolType.ENDPOINT.value
        if values["agent_type"] == CustomToolType.ENDPOINT.value and "code" in values:
            values["code"] = None
        if values["agent_type"] == CustomToolType.CODE.value and "endpoint" in values:
            values["endpoint"] = None

        # Converting list[tools] to AIAgentTool pydantic model
        if "tools" in values:
            tools = values.get("tools")
            if isinstance(tools, list) and all(isinstance(tool, str) for tool in tools):
                values["tools"] = generate_agent_assets(asset_names=tools, asset_type=AIAgentTool)

        # Converting list[agent] to AIAgentParentApplication pydantic model
        if "parent_applications" in values:
            parent_applications = values.get("parent_applications")
            if isinstance(parent_applications, list) and all(isinstance(agent, str) for agent in parent_applications):
                values["parent_applications"] = generate_agent_assets(asset_names=parent_applications,
                                                                      asset_type=AIAgentParentApplication)

        # Converting list[agent] to AIAgentUsedInApplication pydantic model
        if "used_in_applications" in values:
            used_in_applications = values.get("used_in_applications")
            if isinstance(used_in_applications, list) and all(isinstance(agent, str) for agent in used_in_applications):
                values["used_in_applications"] = generate_agent_assets(asset_names=used_in_applications,
                                                                       asset_type=AIAgentUsedInApplication)

        return values

    @model_validator(mode="after")
    def validate_post_payload(self):
        if self.agent_type == CustomToolType.CODE and not self.code:
            raise PydanticCustomError(
                "missing code_payload", 'agent_type is "code", but code field missing in payload.'
            )

        if self.agent_type == CustomToolType.ENDPOINT and not self.endpoint:
            raise PydanticCustomError(
                "missing_endpoint_payload", 'agent_type is "endpoint", but endpoint field missing payload'
            )

        if self.code and self.code.source_code:
            self.code.source_code = get_base64_encoding(tool_code=self.code.source_code)

        if not self.display_name:
            self.display_name = self.agent_name

        return self


class PatchPayload(BaseModel):
    op: Annotated[
        PatchOperationTypes,
        Field(
            ...,
            description="Type of operation to be performed."
        )
    ]
    path: Annotated[
        str,
        Field(
            ...,
            description="Path of the field on which the operation needs to be performed."
        )
    ]
    value: Annotated[
        Any,
        Field(
            ...,
            description="The value to be applied during the specified operation on the given field path."
        )
    ]

    @model_validator(mode="after")
    def validate_patch_payload(self):
        if "source_code_base64" in self.path:
            self.value = get_base64_encoding(tool_code=self.value)

        elif "tools" in self.path:
            # Converting list[tools] to AIAgentTool pydantic model
            tools = self.value
            if isinstance(tools, list) and all(isinstance(tool, str) for tool in tools):
                self.value = generate_agent_assets(asset_names=tools, asset_type=AIAgentTool)

        elif "parent_applications" in self.path:
            # Converting list[agent] to AIAgentParentApplication pydantic model
            parent_applications = self.value
            if isinstance(parent_applications, list) and all(isinstance(agent, str) for agent in parent_applications):
                self.value = generate_agent_assets(asset_names=parent_applications, asset_type=AIAgentParentApplication)

        elif "used_in_applications" in self.path:
            # Converting list[agent] to AIAgentUsedInApplication pydantic model
            used_in_applications = self.value
            if isinstance(used_in_applications, list) and all(isinstance(agent, str) for agent in used_in_applications):
                self.value = generate_agent_assets(asset_names=used_in_applications, asset_type=AIAgentUsedInApplication)

        return self

class AgentUpdatePayload(BaseModel):
    payload: Annotated[
        list[PatchPayload],
        Field(
            ...,
            description="List of patch payloads used to perform the patch operation."
        )
    ]

    @model_validator(mode='before')
    @classmethod
    def validate_ai_agent_patch_payload(cls, values):
        if "payload" not in values or not isinstance(values.get("payload"), list):
            raise PydanticCustomError(
                "Invalid_payload",
                "The payload is either missing or not in a valid list format."
            )
        return values


def generate_agent_assets(
    asset_names: List[str],
    asset_type: Type[Union[AIAgentTool, AIAgentParentApplication, AIAgentUsedInApplication]]
) -> List[Any]:
    """
    Retrieves agent/tool asset objects (AIAgentTool, AIAgentParentApplication, or AIAgentUsedInApplication)
    for the given asset names.

    This function performs a bulk fetch of assets (either tools or agents) and
    converts each matching result into the specified Pydantic model type.

    Behavior:
        - If `asset_type` is AIAgentTool:
            - Calls `list_tools()` once with all provided names.
            - Extracts `tool_id` (from `metadata.id`) and `inventory_id` (from `entity.inventory_id`)
              for each found tool.
        - If `asset_type` is AIAgentParentApplication or AIAgentUsedInApplication:
            - Calls `list_agents()` once with all provided names.
            - Extracts `agent_id` and `inventory_id` for each found agent.
        - Missing asset names:
            - If no assets are found at all, raises an Exception.
            - If some assets are missing, raises a Warning after processing the found ones.

    Args:
        asset_names (List[str]):
            A list of tool or agent names to retrieve.
        asset_type (Type[Union[AIAgentTool, AIAgentParentApplication, AIAgentUsedInApplication]]):
            The Pydantic model class representing the desired asset type.

    Returns:
        List[Any]:
            A list of instances of the specified asset type, one for each found asset.

    Raises:
        Exception:
            If none of the provided asset names are found in the corresponding list API.
        Warning:
            If one or more asset names cannot be found, but at least one valid asset is returned.
    """
    from ..clients.ai_agent_client import list_agents
    from ibm_watsonx_gov.tools.clients.ai_tool_client import list_tools

    response = []
    missing_names = set(asset_names)

    if asset_type is AIAgentTool:
        current_assets_type = "tools"
        result = list_tools(tool_name=asset_names)
    else:
        current_assets_type = "agents"
        result = list_agents(agent_name=asset_names)

    if not result or not result.get(current_assets_type):
        raise Exception(
            f"An error occurred while converting list[{current_assets_type}] to dict objects: "
            f"None of the {current_assets_type} '{asset_names}' were found."
        )

    for asset in result.get(current_assets_type, []):
        response.append(asset_type(
            asset_id=get(asset, "metadata.id"),
            inventory_id=get(asset, "entity.inventory_id")
        ))
        missing_names.discard(get(asset, "entity.asset_name"))  # Remove if found

    if missing_names:
        warnings.warn(
            f"An error occurred while converting list[{current_assets_type}] to dict objects: "
            f"{current_assets_type} {missing_names} were not found.",
            UserWarning
        )

    return response


