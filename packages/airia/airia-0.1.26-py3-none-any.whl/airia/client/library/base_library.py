from typing import Optional, Union
from urllib.parse import urljoin

from ...types._api_version import ApiVersion
from .._request_handler import AsyncRequestHandler, RequestHandler


class BaseLibrary:
    """Base library client with common functionality for sync and async implementations."""

    def __init__(self, request_handler: Union[RequestHandler, AsyncRequestHandler]):
        self._request_handler = request_handler

    def _prepare_get_models_request(
        self,
        page_number: Optional[int] = None,
        page_size: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_direction: Optional[str] = None,
        search: Optional[str] = None,
        providers: Optional[str] = None,
        categories: Optional[str] = None,
        licenses: Optional[str] = None,
        industries: Optional[str] = None,
        authors: Optional[str] = None,
        is_open_source: Optional[bool] = None,
        chat_specialized: Optional[bool] = None,
        industry: Optional[str] = None,
        commercial_use: Optional[bool] = None,
        certifications: Optional[str] = None,
        has_tool_support: Optional[bool] = None,
        has_stream_support: Optional[bool] = None,
        correlation_id: Optional[str] = None,
    ):
        """
        Prepare request data for the get_models endpoint.

        This internal method constructs the URL and parameters for library models
        requests, validating parameters and preparing all request components.

        Args:
            page_number: The page number to be fetched
            page_size: The number of items per page
            sort_by: Property to sort by
            sort_direction: Direction of the sort, either "ASC" for ascending or "DESC" for descending
            search: An optional search string
            providers: Library service provider type filter
            categories: Library service model category filter
            licenses: Library service model license filter
            industries: Optional list of industries to filter by
            authors: Optional list of authors to filter by
            is_open_source: Optional flag to filter by open source status
            chat_specialized: Optional flag to filter by chat specialized status
            industry: Optional flag to filter by Industry
            commercial_use: Optional flag to filter by Commercial Use
            certifications: Optional list of certifications to filter by
            has_tool_support: Optional flag to filter by the models support for tools
            has_stream_support: Optional flag to filter by the models support for response streaming
            correlation_id: Optional correlation ID for request tracing

        Returns:
            RequestData: Prepared request data for the library models endpoint
        """
        url = urljoin(
            self._request_handler.base_url,
            f"api/marketplace/{ApiVersion.V1.value}/Library/models",
        )

        # Build query parameters, excluding None values
        params = {}
        if page_number is not None:
            params["PageNumber"] = page_number
        if page_size is not None:
            params["PageSize"] = page_size
        if sort_by is not None:
            params["SortBy"] = sort_by
        if sort_direction is not None:
            params["SortDirection"] = sort_direction
        if search is not None:
            params["search"] = search
        if providers is not None:
            params["Providers"] = providers
        if categories is not None:
            params["Categories"] = categories
        if licenses is not None:
            params["Licenses"] = licenses
        if industries is not None:
            params["Industries"] = industries
        if authors is not None:
            params["Authors"] = authors
        if is_open_source is not None:
            params["IsOpenSource"] = is_open_source
        if chat_specialized is not None:
            params["ChatSpecialized"] = chat_specialized
        if industry is not None:
            params["Industry"] = industry
        if commercial_use is not None:
            params["CommercialUse"] = commercial_use
        if certifications is not None:
            params["Certifications"] = certifications
        if has_tool_support is not None:
            params["HasToolSupport"] = has_tool_support
        if has_stream_support is not None:
            params["HasStreamSupport"] = has_stream_support

        request_data = self._request_handler.prepare_request(
            url=url, params=params, correlation_id=correlation_id
        )

        return request_data
