"""
Pydantic models for models management API responses.

This module defines the data structures returned by models-related endpoints,
including model listings and associated configuration information.
"""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ModelProject(BaseModel):
    """
    Basic project information associated with a model.

    Represents a simplified view of project data within model contexts,
    containing only essential identification information.
    """

    id: str
    name: str


class ModelSystemPrompt(BaseModel):
    """
    System prompt information associated with a model.

    Contains details about the system prompt template used by the model,
    including version tracking and project associations.
    """

    id: str
    name: str
    active_version_id: Optional[str] = Field(None, alias="activeVersionId")
    active_version: Optional[Any] = Field(None, alias="activeVersion")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    project_id: Optional[str] = Field(None, alias="projectId")
    project_name: Optional[str] = Field(None, alias="projectName")
    project: Optional[Any] = None
    latest_version_number: Optional[int] = Field(None, alias="latestVersionNumber")
    is_agent_specific: bool = Field(alias="isAgentSpecific")


class ModelUserProvidedDetails(BaseModel):
    """
    User-provided configuration details for a model.

    Contains authentication, pricing, and deployment information
    for models configured by users.
    """

    url: str
    credentials_id: Optional[str] = Field(None, alias="credentialsId")
    deployment_type: str = Field(alias="deploymentType")
    connection_string: Optional[str] = Field(None, alias="connectionString")
    container_name: Optional[str] = Field(None, alias="containerName")
    deployed_key: Optional[str] = Field(None, alias="deployedKey")
    deployed_url: Optional[str] = Field(None, alias="deployedUrl")
    state: Optional[Any] = None
    uploaded_container_id: Optional[str] = Field(None, alias="uploadedContainerId")
    input_token_price: float = Field(alias="inputTokenPrice")
    output_token_price: float = Field(alias="outputTokenPrice")
    token_units: int = Field(alias="tokenUnits")


class ModelItem(BaseModel):
    """
    Comprehensive model information and metadata.

    This model represents a complete model entity with all associated configuration,
    pricing information, capabilities, and organizational details. Models can be
    either library-provided or user-configured.

    Attributes:
        category: Model category (e.g., "Multimodal", "NLP", "ImageGeneration")
        id: Unique model identifier
        display_name: Human-readable model name
        model_name: Technical model identifier/name
        prompt_id: Optional system prompt identifier
        system_prompt: Optional system prompt configuration
        source_type: Model source ("Library" or "UserProvided")
        type: Model type (e.g., "Text", "Image")
        provider: AI provider (e.g., "OpenAI", "Anthropic", "Google")
        tenant_id: Tenant/organization identifier
        project_id: Optional project identifier
        project_name: Optional project name
        project: Optional project details
        created_at: Model creation timestamp
        updated_at: Last modification timestamp
        user_id: User who created/configured the model
        has_tool_support: Whether model supports tool calling
        has_stream_support: Whether model supports streaming responses
        library_model_id: Optional library model identifier
        user_provided_details: Configuration details for user-provided models
        allow_airia_credentials: Whether Airia-managed credentials are allowed
        allow_byok_credentials: Whether bring-your-own-key credentials are allowed
        price_type: Pricing model type
        model_parameters: Additional model parameters
        route_through_acc: Whether to route through Airia Credentials Controller
    """

    category: Optional[str] = None
    id: str
    display_name: str = Field(alias="displayName")
    model_name: str = Field(alias="modelName")
    prompt_id: Optional[str] = Field(None, alias="promptId")
    system_prompt: Optional[ModelSystemPrompt] = Field(None, alias="systemPrompt")
    source_type: str = Field(alias="sourceType")
    type: str
    provider: str
    tenant_id: str = Field(alias="tenantId")
    project_id: Optional[str] = Field(None, alias="projectId")
    project_name: Optional[str] = Field(None, alias="projectName")
    project: Optional[ModelProject] = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    user_id: str = Field(alias="userId")
    has_tool_support: bool = Field(alias="hasToolSupport")
    has_stream_support: bool = Field(alias="hasStreamSupport")
    library_model_id: Optional[str] = Field(None, alias="libraryModelId")
    user_provided_details: ModelUserProvidedDetails = Field(alias="userProvidedDetails")
    allow_airia_credentials: bool = Field(alias="allowAiriaCredentials")
    allow_byok_credentials: bool = Field(alias="allowBYOKCredentials")
    price_type: str = Field(alias="priceType")
    model_parameters: List[Any] = Field(alias="modelParameters")
    route_through_acc: bool = Field(alias="routeThroughACC")
