from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

from ...types._api_version import ApiVersion
from .._request_handler import AsyncRequestHandler, RequestHandler


class BasePipelineExecution:
    def __init__(self, request_handler: Union[RequestHandler, AsyncRequestHandler]):
        self._request_handler = request_handler

    def _is_local_path(self, path: str) -> bool:
        """
        Check if a given path is a local file path or a URL.

        Args:
            path: The path to check

        Returns:
            True if it's a local file path, False if it's a URL
        """
        parsed = urlparse(path)
        # If it has a scheme (http, https, ftp, etc.) and a netloc, it's a URL
        return not (parsed.scheme and parsed.netloc)

    def _pre_execute_pipeline(
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
        api_version: str = ApiVersion.V2.value,
    ):
        """
        Prepare request data for pipeline execution endpoint.

        This internal method constructs the URL and payload for pipeline execution
        requests, validating the API version and preparing all request components.

        Args:
            pipeline_id: ID of the pipeline to execute
            user_input: Input text to process
            debug: Whether to enable debug mode
            user_id: Optional user identifier
            conversation_id: Optional conversation identifier
            async_output: Whether to enable streaming output
            include_tools_response: Whether to include tool responses
            images: Optional list of image URLs
            files: Optional list of file URLs
            data_source_folders: Optional data source folder configuration
            data_source_files: Optional data source files configuration
            in_memory_messages: Optional list of in-memory messages
            current_date_time: Optional current date/time in ISO format
            save_history: Whether to save to conversation history
            additional_info: Optional additional information
            prompt_variables: Optional prompt variables
            voice_enabled: Whether the request came through the airia-voice-proxy
            correlation_id: Optional correlation ID for tracing
            api_version: API version to use for the request

        Returns:
            RequestData: Prepared request data for the pipeline execution endpoint

        Raises:
            ValueError: If an invalid API version is provided
        """
        if api_version not in ApiVersion.as_list():
            raise ValueError(
                f"Invalid API version: {api_version}. Valid versions are: {', '.join(ApiVersion.as_list())}"
            )

        url = urljoin(
            self._request_handler.base_url,
            f"{api_version}/PipelineExecution/{pipeline_id}",
        )

        payload = {
            "userInput": user_input,
            "debug": debug,
            "userId": user_id,
            "conversationId": conversation_id,
            "asyncOutput": async_output,
            "includeToolsResponse": include_tools_response,
            "images": images,
            "files": files,
            "dataSourceFolders": data_source_folders,
            "dataSourceFiles": data_source_files,
            "inMemoryMessages": in_memory_messages,
            "currentDateTime": current_date_time,
            "saveHistory": save_history,
            "additionalInfo": additional_info,
            "promptVariables": prompt_variables,
            "voiceEnabled": voice_enabled,
        }

        request_data = self._request_handler.prepare_request(
            url=url, payload=payload, correlation_id=correlation_id
        )

        return request_data

    def _pre_execute_temporary_assistant(
        self,
        model_parameters: Dict[str, Any],
        user_input: str,
        assistant_name: str = "",
        prompt_parameters: Dict[str, Any] = {},
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
    ):
        """
        Prepare request data for temporary assistant execution endpoint.

        This internal method constructs the URL and payload for temporary assistant execution
        requests, validating parameters and preparing all request components.

        Args:
            model_parameters: model parameters
            user_input: Optional user input text
            assistant_name: Name of the temporary assistant
            prompt_parameters: Parameters for prompt configuration (required)
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
            correlation_id: Optional correlation ID for request tracing

        Returns:
            RequestData: Prepared request data for the temporary assistant execution endpoint

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Prepare the request URL
        url = urljoin(
            self._request_handler.base_url,
            f"{ApiVersion.V2.value}/PipelineExecution/TemporaryAssistant",
        )

        # Create the request payload
        payload = {
            "additionalInfo": additional_info,
            "assistantName": assistant_name,
            "asyncOutput": async_output,
            "conversationId": conversation_id,
            "currentDateTime": current_date_time,
            "dataSourceFiles": data_source_files,
            "dataSourceFolders": data_source_folders,
            "dataStoreParameters": data_store_parameters,
            "debug": debug,
            "externalUserId": external_user_id,
            "files": files,
            "images": images,
            "includeToolsResponse": include_tools_response,
            "inMemoryMessages": in_memory_messages,
            "modelParameters": model_parameters,
            "outputConfiguration": output_configuration,
            "promptParameters": prompt_parameters,
            "promptVariables": prompt_variables,
            "saveHistory": save_history,
            "userId": user_id,
            "userInput": user_input,
            "userInputId": user_input_id,
            "variables": variables,
            "voiceEnabled": voice_enabled,
        }

        request_data = self._request_handler.prepare_request(
            url=url,
            payload=payload,
            correlation_id=correlation_id,
        )

        return request_data
