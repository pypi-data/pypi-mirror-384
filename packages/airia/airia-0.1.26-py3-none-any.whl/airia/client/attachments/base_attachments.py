import os
from mimetypes import guess_type
from typing import Optional, Union
from urllib.parse import urljoin

from ...types._api_version import ApiVersion
from .._request_handler import AsyncRequestHandler, RequestHandler


class BaseAttachments:
    def __init__(self, request_handler: Union[RequestHandler, AsyncRequestHandler]):
        self._request_handler = request_handler

    def _pre_upload_file(
        self,
        file_path: str,
        correlation_id: Optional[str] = None,
        api_version: str = ApiVersion.V1.value,
    ):
        """
        Prepare request data for file upload endpoint.

        This internal method constructs the URL and files for file upload
        requests, validating the API version and preparing all request components.

        Args:
            file_path: Path to the file on disk
            correlation_id: Optional correlation ID for tracing
            api_version: API version to use for the request

        Returns:
            RequestData: Prepared request data for the file upload endpoint

        Raises:
            ValueError: If an invalid API version is provided
        """
        if api_version not in ApiVersion.as_list():
            raise ValueError(
                f"Invalid API version: {api_version}. Valid versions are: {', '.join(ApiVersion.as_list())}"
            )

        url = urljoin(
            self._request_handler.base_url,
            f"{api_version}/upload",
        )

        filename = os.path.basename(file_path)
        files = {"file": (filename, open(file_path, "rb"), guess_type(file_path)[0])}

        request_data = self._request_handler.prepare_request(
            url=url, payload={}, files=files, correlation_id=correlation_id
        )

        return request_data
