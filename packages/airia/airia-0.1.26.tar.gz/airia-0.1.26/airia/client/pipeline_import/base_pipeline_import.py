from typing import Any, Dict, Literal, Optional, Union
from urllib.parse import urljoin

from ...types._api_version import ApiVersion
from .._request_handler import AsyncRequestHandler, RequestHandler


class BasePipelineImport:
    def __init__(self, request_handler: Union[RequestHandler, AsyncRequestHandler]):
        self._request_handler = request_handler

    def _pre_create_agent_from_pipeline_definition(
        self,
        pipeline_definition: Dict[str, Any],
        agent_import_source: Optional[
            Literal[
                "PlatformApi",
                "ChatCommunity",
                "PlatformCommunity",
                "PlatformJson",
                "Marketplace",
            ]
        ] = None,
        conflict_resolution_strategy: Literal[
            "SkipConflictingEntities",
            "RecreateExistingEntities",
            "SeededAgent",
        ] = "SkipConflictingEntities",
        credential_mappings: Optional[Dict[str, str]] = None,
        default_project_behavior: Optional[
            Literal["Library", "BrainFreezeThenDefault", "DefaultProject"]
        ] = None,
        project_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        api_version: str = ApiVersion.V1.value,
    ):
        """
        Prepare request data for creating an agent from a pipeline definition.

        This internal method constructs the URL and payload for importing
        a pipeline from a definition.

        Args:
            pipeline_definition: The pipeline definition to import (dictionary structure
                matching ExportPipelineDefinitionResponse format, but using JSON-compatible types)
            agent_import_source: The source of the agent import (PlatformApi, ChatCommunity,
                PlatformCommunity, PlatformJson, or Marketplace)
            conflict_resolution_strategy: Strategy for handling conflicting entities
                (SkipConflictingEntities, RecreateExistingEntities, or SeededAgent)
            credential_mappings: Optional mapping of exported credential IDs to existing
                credential GUIDs in the database
            default_project_behavior: The default project behavior if project_id is null
                (Library, BrainFreezeThenDefault, or DefaultProject)
            project_id: Optional project ID. If null, provision happens in a library project
            correlation_id: Optional correlation ID for tracing
            api_version: API version to use for the request

        Returns:
            RequestData: Prepared request data for the pipeline import endpoint

        Raises:
            ValueError: If an invalid API version is provided
        """
        if api_version not in ApiVersion.as_list():
            raise ValueError(
                f"Invalid API version: {api_version}. Valid versions are: {', '.join(ApiVersion.as_list())}"
            )
        url = urljoin(
            self._request_handler.base_url,
            f"{api_version}/PipelineImport/definition",
        )

        payload = {
            "pipelineDefinition": pipeline_definition,
            "conflictResolutionStrategy": conflict_resolution_strategy,
        }

        # Add optional fields only if they are not None
        if agent_import_source is not None:
            payload["agentImportSource"] = agent_import_source

        if credential_mappings is not None:
            payload["credentialMappings"] = credential_mappings

        if default_project_behavior is not None:
            payload["defaultProjectBehavior"] = default_project_behavior

        if project_id is not None:
            payload["projectId"] = project_id

        request_data = self._request_handler.prepare_request(
            url=url, payload=payload, correlation_id=correlation_id
        )

        return request_data
