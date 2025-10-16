"""
Pydantic models for pipeline execution API responses.

This module defines the response models returned by pipeline execution endpoints,
including both synchronous and streaming response types.
"""

from datetime import datetime
from typing import Any, AsyncIterator, Dict, Iterator, List, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ...sse import SSEMessage


class TimeTrackingData(BaseModel):
    """
    Time tracking data for pipeline execution.

    Attributes:
        duration: Human-readable duration string (e.g., "2.5s", "1m 30s"). None if execution not completed.
        started_at: Timestamp when the execution started.
        finished_at: Timestamp when the execution finished. None if still running or failed.
    """

    duration: Optional[str] = None
    started_at: datetime = Field(alias="startedAt")
    finished_at: Optional[datetime] = Field(None, alias="finishedAt")


class AgentBaseStepResult(BaseModel):
    """
    Base class for agent step results.

    Attributes:
        step_type: Type of the step (e.g., "LLMStep", "ToolStep", "ConditionalStep").
        step_id: Unique identifier for this step execution.
        type: Discriminator field for polymorphic deserialization ($type field).
    """

    step_type: str = Field(alias="stepType")
    step_id: UUID = Field(alias="stepId")
    type: str = Field(alias="$type")


class PipelineStepResult(BaseModel):
    """
    Result of a pipeline step execution.

    Attributes:
        step_id: Unique identifier for the step.
        step_type: Type of step that was executed (e.g., "LLMStep", "ToolStep").
        step_title: Human-readable title/name of the step.
        result: Output result from the step execution. None if step failed or produced no output.
        input: List of input data that was passed to this step.
        success: Whether the step executed successfully. None if status is indeterminate.
        completion_status: Status of step completion (e.g., "Success", "Failed", "Skipped").
        time_tracking_data: Timing information for this step's execution.
        exception_message: Error message if the step failed. None if successful.
        debug_information: Additional debug data and metadata from step execution.
    """

    step_id: UUID = Field(alias="stepId")
    step_type: Optional[str] = Field(None, alias="stepType")
    step_title: str = Field(alias="stepTitle")
    result: Optional[AgentBaseStepResult] = None
    input: List[AgentBaseStepResult] = []
    success: Optional[bool] = None
    completion_status: str = Field(alias="completionStatus")
    time_tracking_data: Optional[TimeTrackingData] = Field(
        None, alias="timeTrackingData"
    )
    exception_message: Optional[str] = Field(None, alias="exceptionMessage")
    debug_information: Dict[str, Any] = Field(
        default_factory=dict, alias="debugInformation"
    )


class PipelineExecutionResponse(BaseModel):
    """Response model for pipeline execution requests in mode.

    Attributes:
        result: The execution result as a string
        report: Optional Dictionary containing debugging information and execution details
        is_backup_pipeline: Whether a backup pipeline was used for execution
    """

    result: Optional[str]
    report: Optional[Dict[str, PipelineStepResult]] = None
    is_backup_pipeline: bool = Field(alias="isBackupPipeline")


class PipelineExecutionStreamedResponse(BaseModel):
    """Response model for streaming pipeline execution requests (synchronous client).

    This model contains an iterator that yields SSEMessage objects as they
    are received from the streaming response.

    Attributes:
        stream: Iterator that yields SSEMessage objects from the streaming response
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    stream: Iterator[SSEMessage]


class PipelineExecutionAsyncStreamedResponse(BaseModel):
    """Response model for streaming pipeline execution requests (asynchronous client).

    This model contains an async iterator that yields SSEMessage objects as they
    are received from the streaming response.

    Attributes:
        stream: Async iterator that yields SSEMessage objects from the streaming response
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    stream: AsyncIterator[SSEMessage]


class TemporaryAssistantResponse(BaseModel):
    """Response model for TemporaryAssistant pipeline execution.

    This model represents the response from the TemporaryAssistant endpoint,
    which can return either string or array results based on the discriminator.

    Attributes:
        type: Discriminator field indicating the response type
        report: Pipeline execution debug report (optional)
        is_backup_pipeline: Whether a backup pipeline was used
        execution_id: Unique execution identifier
        user_input_id: Identifier for the user input
        files: Files processed during execution
        images: Images processed during execution
    """

    type: Literal["string", "objectArray"] = Field(alias="$type")
    result: Union[List[Any], str] = Field(...)
    report: Optional[Dict[str, PipelineStepResult]] = None
    is_backup_pipeline: bool = Field(alias="isBackupPipeline")
    execution_id: UUID = Field(alias="executionId")
    user_input_id: Optional[UUID] = Field(None, alias="userInputId")
    files: Optional[List[str]] = None
    images: Optional[List[str]] = None


class TemporaryAssistantStreamedResponse(BaseModel):
    """
    Response model for streaming TemporaryAssistant requests (synchronous client).

    Attributes:
        stream: Iterator that yields SSEMessage objects as they arrive from the streaming response.
                Each message contains incremental data from the assistant's response.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    stream: Iterator[SSEMessage]


class TemporaryAssistantAsyncStreamedResponse(BaseModel):
    """
    Response model for streaming TemporaryAssistant requests (asynchronous client).

    Attributes:
        stream: Async iterator that yields SSEMessage objects as they arrive from the streaming response.
                Each message contains incremental data from the assistant's response.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    stream: AsyncIterator[SSEMessage]
