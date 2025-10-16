from typing import Any, Dict, List, Literal, Optional, Union, overload

from ...types._api_version import ApiVersion
from ...types.api.pipeline_execution import (
    PipelineExecutionResponse,
    PipelineExecutionStreamedResponse,
    TemporaryAssistantResponse,
    TemporaryAssistantStreamedResponse,
)
from .._request_handler import RequestHandler
from .base_pipeline_execution import BasePipelineExecution


class PipelineExecution(BasePipelineExecution):
    def __init__(self, request_handler: RequestHandler):
        super().__init__(request_handler)

    def _upload_files(
        self, files: List[str], images: List[str]
    ) -> tuple[List[str], List[str]]:
        """
        Upload files and images synchronously and return their URLs.
        URLs are passed through directly, local paths are uploaded first.

        Args:
            files: List of file paths or URLs
            images: List of image file paths or URLs

        Returns:
            Tuple of (file_urls, image_urls)
        """
        from ..attachments.sync_attachments import Attachments

        attachments_client = Attachments(self._request_handler)
        file_urls = None
        image_urls = None

        if files:
            file_urls = []
            for file_path in files:
                if self._is_local_path(file_path):
                    # Local file - upload it
                    response = attachments_client.upload_file(file_path)
                    file_urls.append(response.image_url)
                else:
                    # URL - use directly
                    file_urls.append(file_path)

        if images:
            image_urls = []
            for image_path in images:
                if self._is_local_path(image_path):
                    # Local file - upload it
                    response = attachments_client.upload_file(image_path)
                    if response.image_url:
                        image_urls.append(response.image_url)
                else:
                    # URL - use directly
                    image_urls.append(image_path)

        return file_urls, image_urls

    @overload
    def execute_pipeline(
        self,
        pipeline_id: str,
        user_input: str,
        debug: bool = False,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        async_output: Literal[False] = False,
        include_tools_response: bool = False,
        images: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        data_source_folders: Optional[Dict[str, Any]] = None,
        data_source_files: Optional[Dict[str, Any]] = None,
        in_memory_messages: Optional[List[Dict[str, Any]]] = None,
        current_date_time: Optional[str] = None,
        save_history: bool = True,
        additional_info: Optional[List[Any]] = None,
        prompt_variables: Optional[Dict[str, Any]] = None,
        voice_enabled: bool = False,
        correlation_id: Optional[str] = None,
    ) -> PipelineExecutionResponse: ...

    @overload
    def execute_pipeline(
        self,
        pipeline_id: str,
        user_input: str,
        debug: bool = False,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        async_output: Literal[True] = True,
        include_tools_response: bool = False,
        images: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        data_source_folders: Optional[Dict[str, Any]] = None,
        data_source_files: Optional[Dict[str, Any]] = None,
        in_memory_messages: Optional[List[Dict[str, Any]]] = None,
        current_date_time: Optional[str] = None,
        save_history: bool = True,
        additional_info: Optional[List[Any]] = None,
        prompt_variables: Optional[Dict[str, Any]] = None,
        voice_enabled: bool = False,
        correlation_id: Optional[str] = None,
    ) -> PipelineExecutionStreamedResponse: ...

    def execute_pipeline(
        self,
        pipeline_id: str,
        user_input: str,
        debug: bool = False,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        async_output: bool = False,
        include_tools_response: bool = False,
        images: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        data_source_folders: Optional[Dict[str, Any]] = None,
        data_source_files: Optional[Dict[str, Any]] = None,
        in_memory_messages: Optional[List[Dict[str, Any]]] = None,
        current_date_time: Optional[str] = None,
        save_history: bool = True,
        additional_info: Optional[List[Any]] = None,
        prompt_variables: Optional[Dict[str, Any]] = None,
        voice_enabled: bool = False,
        correlation_id: Optional[str] = None,
    ) -> Union[PipelineExecutionResponse, PipelineExecutionStreamedResponse]:
        """
        Execute a pipeline with the provided input.

        Args:
            pipeline_id: The ID of the pipeline to execute.
            user_input: input text to process.
            debug: Whether debug mode execution is enabled. Default is False.
            user_id: Optional ID of the user making the request (guid).
            conversation_id: Optional conversation ID (guid).
            async_output: Whether to stream the response. Default is False.
            include_tools_response: Whether to return the initial LLM tool result. Default is False.
            images: Optional list of image file paths or URLs.
            files: Optional list of file paths or URLs.
            data_source_folders: Optional data source folders information.
            data_source_files: Optional data source files information.
            in_memory_messages: Optional list of in-memory messages, each with a role and message.
            current_date_time: Optional current date and time in ISO format.
            save_history: Whether to save the userInput and output to conversation history. Default is True.
            additional_info: Optional additional information.
            prompt_variables: Optional variables to be used in the prompt.
            voice_enabled: Whether the request came through the airia-voice-proxy. Default is False.
            correlation_id: Optional correlation ID for request tracing. If not provided,
                        one will be generated automatically.

        Returns:
            Response containing the result of the execution.

        Raises:
            AiriaAPIError: If the API request fails with details about the error.
            requests.RequestException: For other request-related errors.

        Example:
            ```python
            client = AiriaClient(api_key="your_api_key")
            response = client.pipeline_execution.execute_pipeline(
                pipeline_id="pipeline_123",
                user_input="Tell me about quantum computing"
            )
            print(response.result)
            ```
        """
        # Validate user_input parameter
        if not user_input:
            raise ValueError("user_input cannot be empty")

        # Handle file and image uploads (local files are uploaded, URLs are passed through)
        image_urls = None
        file_urls = None

        if images or files:
            file_urls, image_urls = self._upload_files(files or [], images or [])

        request_data = self._pre_execute_pipeline(
            pipeline_id=pipeline_id,
            user_input=user_input,
            debug=debug,
            user_id=user_id,
            conversation_id=conversation_id,
            async_output=async_output,
            include_tools_response=include_tools_response,
            images=image_urls,
            files=file_urls,
            data_source_folders=data_source_folders,
            data_source_files=data_source_files,
            in_memory_messages=in_memory_messages,
            current_date_time=current_date_time,
            save_history=save_history,
            additional_info=additional_info,
            prompt_variables=prompt_variables,
            voice_enabled=voice_enabled,
            correlation_id=correlation_id,
            api_version=ApiVersion.V2.value,
        )
        resp = (
            self._request_handler.make_request_stream("POST", request_data)
            if async_output
            else self._request_handler.make_request("POST", request_data)
        )

        if not async_output:
            return PipelineExecutionResponse(**resp)

        return PipelineExecutionStreamedResponse(stream=resp)

    @overload
    def execute_temporary_assistant(
        self,
        model_parameters: Dict[str, Any],
        user_input: str,
        assistant_name: str = "",
        prompt_parameters: Dict[str, Any] = {"prompt": ""},
        async_output: Literal[False] = False,
        include_tools_response: bool = False,
        save_history: bool = True,
        voice_enabled: bool = False,
        debug: bool = False,
        additional_info: Optional[List[Any]] = None,
        conversation_id: Optional[str] = None,
        current_date_time: Optional[str] = None,
        data_source_files: Optional[Dict[str, List[str]]] = None,
        data_source_folders: Optional[Dict[str, List[str]]] = None,
        data_store_parameters: Optional[Dict[str, Any]] = None,
        external_user_id: Optional[str] = None,
        files: Optional[List[str]] = None,
        images: Optional[List[str]] = None,
        in_memory_messages: Optional[List[Dict[str, Any]]] = None,
        output_configuration: Optional[Dict[str, Any]] = None,
        prompt_variables: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        user_input_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> TemporaryAssistantResponse: ...

    @overload
    def execute_temporary_assistant(
        self,
        model_parameters: Dict[str, Any],
        user_input: str,
        assistant_name: str = "",
        prompt_parameters: Dict[str, Any] = {"prompt": ""},
        async_output: Literal[True] = True,
        include_tools_response: bool = False,
        save_history: bool = True,
        voice_enabled: bool = False,
        debug: bool = False,
        additional_info: Optional[List[Any]] = None,
        conversation_id: Optional[str] = None,
        current_date_time: Optional[str] = None,
        data_source_files: Optional[Dict[str, List[str]]] = None,
        data_source_folders: Optional[Dict[str, List[str]]] = None,
        data_store_parameters: Optional[Dict[str, Any]] = None,
        external_user_id: Optional[str] = None,
        files: Optional[List[str]] = None,
        images: Optional[List[str]] = None,
        in_memory_messages: Optional[List[Dict[str, Any]]] = None,
        output_configuration: Optional[Dict[str, Any]] = None,
        prompt_variables: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        user_input_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> TemporaryAssistantStreamedResponse: ...

    def execute_temporary_assistant(
        self,
        model_parameters: Dict[str, Any],
        user_input: str,
        assistant_name: str = "",
        prompt_parameters: Dict[str, Any] = {"prompt": ""},
        async_output: bool = False,
        include_tools_response: bool = False,
        save_history: bool = True,
        voice_enabled: bool = False,
        debug: bool = False,
        additional_info: Optional[List[Any]] = None,
        conversation_id: Optional[str] = None,
        current_date_time: Optional[str] = None,
        data_source_files: Optional[Dict[str, List[str]]] = None,
        data_source_folders: Optional[Dict[str, List[str]]] = None,
        data_store_parameters: Optional[Dict[str, Any]] = None,
        external_user_id: Optional[str] = None,
        files: Optional[List[str]] = None,
        images: Optional[List[str]] = None,
        in_memory_messages: Optional[List[Dict[str, Any]]] = None,
        output_configuration: Optional[Dict[str, Any]] = None,
        prompt_variables: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        user_input_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Union[
        TemporaryAssistantResponse,
        TemporaryAssistantStreamedResponse,
    ]:
        """
        Execute a temporary assistant with the provided parameters.

        This method creates and executes a temporary AI assistant with custom configuration,
        allowing for flexible assistant behavior without creating a persistent pipeline.

        Args:
            model_parameters: Model parameters (required). Must include libraryModelId,
                            projectModelId, modelIdentifierType, and modelIsAvailableinProject
            user_input: User input text (required)
            assistant_name: Name of the temporary assistant. Default is ""
            prompt_parameters: Parameters for prompt configuration. Default is {"prompt": ""}
            async_output: Whether to stream the response. Default is False
            include_tools_response: Whether to return initial LLM tool result. Default is False
            save_history: Whether to save input and output to conversation history. Default is True
            voice_enabled: Whether voice output is enabled. Default is False
            debug: Whether debug mode execution is enabled. Default is False
            additional_info: Optional additional information array
            conversation_id: Optional conversation identifier (GUID string or UUID)
            current_date_time: Optional current date and time in ISO format
            data_source_files: Optional dictionary mapping data source GUIDs to file GUID arrays
            data_source_folders: Optional dictionary mapping data source GUIDs to folder GUID arrays
            data_store_parameters: Optional DataStore parameters
            external_user_id: Optional external user identifier
            files: Optional list of file identifiers
            images: Optional list of image identifiers
            in_memory_messages: Optional list of in-memory messages
            output_configuration: Optional output configuration
            prompt_variables: Optional prompt variables dictionary
            user_id: Optional user identifier (GUID string or UUID)
            user_input_id: Optional unique identifier for user input (GUID string or UUID)
            variables: Optional variables dictionary
            correlation_id: Optional correlation ID for request tracing. If not provided,
                          one will be generated automatically.

        Returns:
            Response containing the result of the temporary assistant execution.

        Raises:
            AiriaAPIError: If the API request fails with details about the error.
            requests.RequestException: For other request-related errors.
            ValueError: If required parameters are missing or invalid.

        Example:
            ```python
            client = AiriaClient(api_key="your_api_key")
            response = client.pipeline_execution.execute_temporary_assistant(
                model_parameters={
                    "libraryModelId": "library-model-id",
                    "projectModelId": None,
                    "modelIdentifierType": "Library",
                    "modelIsAvailableinProject": True,
                },
                user_input="say double bubble bath ten times fast",
            )
            print(response.result)
            ```
        """
        # Validate required parameters
        if not user_input:
            raise ValueError("user_input cannot be empty")

        if not model_parameters:
            raise ValueError("model_parameters cannot be empty")

        # Handle file and image uploads (local files are uploaded, URLs are passed through)
        image_urls = None
        file_urls = None

        if images or files:
            file_urls, image_urls = self._upload_files(files or [], images or [])

        # Convert UUID objects to strings for API compatibility
        conversation_id_str = str(conversation_id) if conversation_id else conversation_id
        user_id_str = str(user_id) if user_id else user_id
        user_input_id_str = str(user_input_id) if user_input_id else user_input_id

        request_data = self._pre_execute_temporary_assistant(
            model_parameters=model_parameters,
            user_input=user_input,
            assistant_name=assistant_name,
            prompt_parameters=prompt_parameters,
            async_output=async_output,
            include_tools_response=include_tools_response,
            save_history=save_history,
            voice_enabled=voice_enabled,
            debug=debug,
            additional_info=additional_info,
            conversation_id=conversation_id_str,
            current_date_time=current_date_time,
            data_source_files=data_source_files,
            data_source_folders=data_source_folders,
            data_store_parameters=data_store_parameters,
            external_user_id=external_user_id,
            files=file_urls,
            images=image_urls,
            in_memory_messages=in_memory_messages,
            output_configuration=output_configuration,
            prompt_variables=prompt_variables,
            user_id=user_id_str,
            user_input_id=user_input_id_str,
            variables=variables,
            correlation_id=correlation_id,
        )

        resp = (
            self._request_handler.make_request_stream("POST", request_data)
            if async_output
            else self._request_handler.make_request("POST", request_data)
        )

        if async_output:
            return TemporaryAssistantStreamedResponse(stream=resp)

        return TemporaryAssistantResponse(**resp)
