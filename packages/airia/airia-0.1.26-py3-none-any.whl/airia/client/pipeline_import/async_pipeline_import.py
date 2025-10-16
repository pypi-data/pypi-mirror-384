from typing import Any, Dict, Literal, Optional

from ...types._api_version import ApiVersion
from ...types.api.pipeline_import import CreateAgentFromPipelineDefinitionResponse
from .._request_handler import AsyncRequestHandler
from .base_pipeline_import import BasePipelineImport


class AsyncPipelineImport(BasePipelineImport):
    def __init__(self, request_handler: AsyncRequestHandler):
        super().__init__(request_handler)

    async def create_agent_from_pipeline_definition(
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
    ) -> CreateAgentFromPipelineDefinitionResponse:
        """
        Create an agent from a pipeline definition (async).

        This method imports a complete pipeline from a definition dictionary,
        creating all necessary components including data sources, prompts, tools,
        models, and pipeline steps. The definition structure should match the
        format returned by export_pipeline_definition(), but use JSON-compatible
        types (no enums or Pydantic classes).

        Args:
            pipeline_definition (dict): The pipeline definition to import. This should
                be a dictionary with the same structure as the response from
                pipelines_config.export_pipeline_definition(), but using only
                JSON-compatible types (strings, numbers, dicts, lists).
            agent_import_source (str, optional): The source of the agent import.
                Valid values: "PlatformApi", "ChatCommunity", "PlatformCommunity",
                "PlatformJson", "Marketplace". If not provided, the import source
                will not be specified.
            conflict_resolution_strategy (str): Strategy for handling conflicting entities.
                Valid values:
                - "SkipConflictingEntities" (default): Skip entities that already exist
                - "RecreateExistingEntities": Recreate entities that already exist
                - "SeededAgent": Use seeded agent strategy
            credential_mappings (dict, optional): Mapping of exported credential IDs
                to existing credential GUIDs in the database. Key: Exported credential
                ID from agent definition. Value: Existing credential GUID in database
                (must belong to tenant/project).
            default_project_behavior (str, optional): The default project behavior
                if project_id is null. Valid values: "Library", "BrainFreezeThenDefault",
                "DefaultProject".
            project_id (str, optional): The project ID where the pipeline should be
                imported. If null, the provision will happen in a library project
                according to default_project_behavior.
            correlation_id (str, optional): A unique identifier for request tracing
                and logging. If not provided, one will be automatically generated.

        Returns:
            CreateAgentFromPipelineDefinitionResponse: A response object containing the
                import result, including pipeline ID, department ID, pipeline name,
                deployment ID (if deployed), and lists of created, updated, and
                skipped entities. If the import failed, error_message and error_details
                will contain information about what went wrong.

        Raises:
            AiriaAPIError: If the API request fails, including cases where:
                - The pipeline definition is invalid (400)
                - A referenced project_id doesn't exist (404)
                - Credential mappings are invalid (400)
                - Authentication fails (401)
                - Access is forbidden (403)
                - Server errors (5xx)

        Example:
            ```python
            from airia import AiriaAsyncClient
            import asyncio

            async def main():
                client = AiriaAsyncClient(api_key="your_api_key")

                # First, export a pipeline definition
                exported = await client.pipelines_config.export_pipeline_definition(
                    pipeline_id="source_pipeline_id"
                )

                # Convert the exported definition to a JSON-compatible dictionary
                # (Pydantic models have a .model_dump() method for this)
                pipeline_def = exported.model_dump(by_alias=True, exclude_none=True)

                # Import the pipeline into a new project
                result = await client.pipeline_import.create_agent_from_pipeline_definition(
                    pipeline_definition=pipeline_def,
                    project_id="target_project_id",
                    conflict_resolution_strategy="SkipConflictingEntities"
                )

                if result.error_message:
                    print(f"Import failed: {result.error_message}")
                    if result.error_details:
                        for detail in result.error_details:
                            print(f"  - {detail}")
                else:
                    print(f"Pipeline imported successfully!")
                    print(f"Pipeline ID: {result.pipeline_id}")
                    print(f"Pipeline Name: {result.pipeline_name}")
                    print(f"Created {len(result.created_entities or [])} entities")
                    print(f"Updated {len(result.updated_entities or [])} entities")
                    print(f"Skipped {len(result.skipped_entities or [])} entities")

            asyncio.run(main())
            ```

        Note:
            - The pipeline_definition must use JSON-compatible types only
            - Use model_dump(by_alias=True) on Pydantic models to get the correct format
            - Credential mappings must reference existing credentials in the target system
            - The import process will create new GUIDs for most entities
        """
        request_data = self._pre_create_agent_from_pipeline_definition(
            pipeline_definition=pipeline_definition,
            agent_import_source=agent_import_source,
            conflict_resolution_strategy=conflict_resolution_strategy,
            credential_mappings=credential_mappings,
            default_project_behavior=default_project_behavior,
            project_id=project_id,
            correlation_id=correlation_id,
            api_version=ApiVersion.V1.value,
        )
        resp = await self._request_handler.make_request("POST", request_data)

        return CreateAgentFromPipelineDefinitionResponse(**resp)
