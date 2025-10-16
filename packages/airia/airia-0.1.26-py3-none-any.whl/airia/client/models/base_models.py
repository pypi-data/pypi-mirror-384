from typing import Optional, Union
from urllib.parse import urljoin, urlencode

from ...types._api_version import ApiVersion
from .._request_handler import AsyncRequestHandler, RequestHandler


class BaseModels:
    def __init__(self, request_handler: Union[RequestHandler, AsyncRequestHandler]):
        self._request_handler = request_handler

    def _pre_list_models(
        self,
        project_id: Optional[str] = None,
        include_global: bool = True,
        page_number: int = 1,
        page_size: int = 50,
        sort_by: str = "updatedAt",
        sort_direction: str = "DESC",
        correlation_id: Optional[str] = None,
        api_version: str = ApiVersion.V1.value,
    ):
        """
        Prepare request data for listing models endpoint.

        Args:
            project_id: Optional project ID to filter models
            include_global: Whether to include global models (default: True)
            page_number: Page number for pagination (default: 1)
            page_size: Number of items per page (default: 50)
            sort_by: Field to sort by (default: "updatedAt")
            sort_direction: Sort direction "ASC" or "DESC" (default: "DESC")
            correlation_id: Optional correlation ID for tracing
            api_version: API version to use for the request

        Returns:
            RequestData: Prepared request data for the models endpoint

        Raises:
            ValueError: If an invalid API version is provided
        """
        if api_version not in ApiVersion.as_list():
            raise ValueError(
                f"Invalid API version: {api_version}. Valid versions are: {', '.join(ApiVersion.as_list())}"
            )

        # Build query parameters
        query_params = {
            "pageNumber": page_number,
            "pageSize": page_size,
            "sortBy": sort_by,
            "sortDirection": sort_direction,
            "includeGlobal": str(include_global).lower(),
        }

        if project_id:
            query_params["projectId"] = project_id

        query_string = urlencode(query_params)
        url = urljoin(
            self._request_handler.base_url, f"{api_version}/Models?{query_string}"
        )

        request_data = self._request_handler.prepare_request(
            url, correlation_id=correlation_id
        )

        return request_data
