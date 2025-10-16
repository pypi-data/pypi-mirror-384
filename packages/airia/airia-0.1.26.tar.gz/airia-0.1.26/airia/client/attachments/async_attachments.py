from typing import Optional

from ...types._api_version import ApiVersion
from ...types.api.attachments import AttachmentResponse
from .._request_handler import AsyncRequestHandler
from .base_attachments import BaseAttachments


class AsyncAttachments(BaseAttachments):
    def __init__(self, request_handler: AsyncRequestHandler):
        super().__init__(request_handler)

    async def upload_file(
        self,
        file_path: str,
        correlation_id: Optional[str] = None,
    ) -> AttachmentResponse:
        """
        Upload a file and get attachment information.

        Args:
            file_path: Path to the file on disk
            correlation_id: Optional correlation ID for request tracing. If not provided,
                        one will be generated automatically.

        Returns:
            AttachmentResponse: Response containing the attachment ID and URL.

        Raises:
            AiriaAPIError: If the API request fails with details about the error.
            aiohttp.ClientError: For other request-related errors.

        Example:
            ```python
            async_client = AiriaAsyncClient(api_key="your_api_key")

            # Upload a file
            response = await async_client.attachments.upload_file(
                file_path="example.jpg"
            )
            print(f"Uploaded attachment ID: {response.id}")
            print(f"Attachment URL: {response.image_url}")
            ```
        """
        request_data = self._pre_upload_file(
            file_path=file_path,
            correlation_id=correlation_id,
            api_version=ApiVersion.V1.value,
        )

        resp = await self._request_handler.make_request_multipart("POST", request_data)
        return AttachmentResponse(**resp)
