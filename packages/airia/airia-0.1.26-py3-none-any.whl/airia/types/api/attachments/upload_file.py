from typing import Optional

from pydantic import BaseModel, Field


class AttachmentResponse(BaseModel):
    """Response model for uploading an attachment file.

    This class conveys the unique identifier and URL of the uploaded attachment.

    Attributes:
        id: The unique identifier of the attachment
        image_url: The URL of the attachment
    """

    id: Optional[str] = None
    image_url: Optional[str] = Field(None, alias="imageUrl")
