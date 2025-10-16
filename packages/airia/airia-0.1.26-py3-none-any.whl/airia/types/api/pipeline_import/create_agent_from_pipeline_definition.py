"""Types for the create_agent_from_pipeline_definition API response.

This module defines data structures for pipeline import results,
including information about created, updated, and skipped entities
during the pipeline import process.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class PipelineImportedEntity(BaseModel):
    """Pipeline imported entity result.

    Represents an entity that was processed during pipeline import,
    including its type, name, ID, and the action taken (created, updated, or skipped).

    Attributes:
        entity_type: The type of entity (e.g., Pipeline, DataSource, Tool)
        entity_name: The name of the entity
        entity_id: The unique identifier of the entity
        reason: Optional explanation for why the entity was created/updated/skipped
        action: The action taken on the entity (Created, Updated, or Skipped)
        prompt_id: Optional prompt ID associated with this entity (used for step-level prompts)
    """

    entity_type: str = Field(
        ..., description="Gets the entity type.", alias="entityType"
    )
    entity_name: Optional[str] = Field(
        None, description="Gets the entity name.", alias="entityName"
    )
    entity_id: str = Field(..., description="Gets the entity id.", alias="entityId")
    reason: Optional[str] = Field(
        None,
        description="Gets or sets an optional value indication why the entity was skipped/updated/created.",
    )
    action: Literal["Created", "Updated", "Skipped"] = Field(
        ..., description="Gets or sets the action taken on the entity."
    )
    prompt_id: Optional[str] = Field(
        None,
        description="Gets or sets the prompt ID associated with this entity (used to set the prompt at the step level on import).",
        alias="promptId",
    )


class CreateAgentFromPipelineDefinitionResponse(BaseModel):
    """Pipeline import result.

    Contains the complete result of a pipeline import operation,
    including the created pipeline information, any errors encountered,
    and detailed lists of all entities that were created, updated, or skipped.

    Attributes:
        pipeline_id: The ID of the imported pipeline
        department_id: The department ID if the pipeline was imported into a specific department
        pipeline_name: The name of the imported pipeline
        deployment_id: The deployment ID if the pipeline was deployed during import
        error_message: An error message if the import failed
        error_details: Detailed error messages if the import failed
        created_entities: List of entities that were created during import
        skipped_entities: List of entities that were skipped during import
        updated_entities: List of entities that were updated during import
    """

    pipeline_id: Optional[str] = Field(
        None, description="Gets the pipeline id.", alias="pipelineId"
    )
    department_id: Optional[str] = Field(
        None,
        description="Gets the department id if the pipeline was imported into a specific department.",
        alias="departmentId",
    )
    pipeline_name: Optional[str] = Field(
        None, description="Gets the pipeline name.", alias="pipelineName"
    )
    deployment_id: Optional[str] = Field(
        None,
        description="Gets the deployment id if the pipeline was deployed during the import.",
        alias="deploymentId",
    )
    error_message: Optional[str] = Field(
        None,
        description="Gets an error message if the import failed.",
        alias="errorMessage",
    )
    error_details: Optional[List[str]] = Field(
        None,
        description="Gets the error details if the import failed.",
        alias="errorDetails",
    )
    created_entities: Optional[List[PipelineImportedEntity]] = Field(
        None,
        description="Gets the list of created entities during the import process.",
        alias="createdEntities",
    )
    skipped_entities: Optional[List[PipelineImportedEntity]] = Field(
        None,
        description="Gets the list of skipped entities during the import process.",
        alias="skippedEntities",
    )
    updated_entities: Optional[List[PipelineImportedEntity]] = Field(
        None,
        description="Gets the list of skipped entities during the import process.",
        alias="updatedEntities",
    )
