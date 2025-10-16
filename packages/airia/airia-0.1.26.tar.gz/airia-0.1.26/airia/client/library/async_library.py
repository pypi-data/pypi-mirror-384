from typing import Optional

from ...types.api.library import GetLibraryModelsResponse
from .._request_handler import AsyncRequestHandler
from .base_library import BaseLibrary


class AsyncLibrary(BaseLibrary):
    """Asynchronous library client for interacting with Airia Library endpoints."""

    def __init__(self, request_handler: AsyncRequestHandler):
        super().__init__(request_handler)

    async def get_models(
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
    ) -> GetLibraryModelsResponse:
        """
        Asynchronously retrieve models from the Airia Library with optional filtering and pagination.

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
            correlation_id: Optional correlation ID for request tracing. If not provided,
                          one will be generated automatically.

        Returns:
            GetLibraryModelsResponse: Response containing the list of models and total count

        Raises:
            AiriaAPIError: If the API request fails with details about the error.
            aiohttp.ClientError: For other request-related errors.

        Example:
            ```python
            client = AiriaAsyncClient(api_key="your_api_key")
            response = await client.library.get_models(
                search="gpt",
                providers="OpenAI",
                page_size=10
            )
            for model in response.models:
                print(f"Model: {model.name} (ID: {model.id})")
            ```
        """
        request_data = self._prepare_get_models_request(
            page_number=page_number,
            page_size=page_size,
            sort_by=sort_by,
            sort_direction=sort_direction,
            search=search,
            providers=providers,
            categories=categories,
            licenses=licenses,
            industries=industries,
            authors=authors,
            is_open_source=is_open_source,
            chat_specialized=chat_specialized,
            industry=industry,
            commercial_use=commercial_use,
            certifications=certifications,
            has_tool_support=has_tool_support,
            has_stream_support=has_stream_support,
            correlation_id=correlation_id,
        )

        resp = await self._request_handler.make_request("GET", request_data)
        return GetLibraryModelsResponse(**resp)
