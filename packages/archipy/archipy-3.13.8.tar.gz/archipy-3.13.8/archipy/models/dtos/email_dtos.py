import mimetypes
from typing import BinaryIO, Self

from pydantic import Field, field_validator, model_validator

from archipy.models.dtos.base_dtos import BaseDTO
from archipy.models.types.email_types import EmailAttachmentDispositionType, EmailAttachmentType


class EmailAttachmentDTO(BaseDTO):
    """Pydantic model for email attachments."""

    content: str | bytes | BinaryIO
    filename: str
    content_type: str | None = Field(default=None)
    content_disposition: EmailAttachmentDispositionType = Field(default=EmailAttachmentDispositionType.ATTACHMENT)
    content_id: str | None = Field(default=None)
    attachment_type: EmailAttachmentType
    max_size: int

    @field_validator("content_type")  # type: ignore[type-var]
    def set_content_type(self, v: str | None, values: dict) -> str | None:
        """Set content type based on filename extension if not provided.

        Args:
            v: The content type value
            values: Other field values

        Returns:
            The determined content type or the original value
        """
        if v is None and "filename" in values:
            content_type, _ = mimetypes.guess_type(values["filename"])
            return content_type or "application/octet-stream"
        return v

    @model_validator(mode="after")  # type: ignore[arg-type]
    def validate_attachment_size(self, model: Self) -> Self:
        """Validate that the attachment size does not exceed the maximum allowed size.

        Args:
            model: The model instance

        Returns:
            The validated model instance

        Raises:
            ValueError: If attachment size exceeds maximum allowed size
        """
        content = model.content
        if isinstance(content, str | bytes):
            content_size = len(content)
            if content_size > model.max_size:
                error_msg = f"Attachment size exceeds maximum allowed size of {model.max_size} bytes"
                raise ValueError(error_msg)
        return model

    @field_validator("content_id")  # type: ignore[type-var]
    def validate_content_id(self, v: str | None, _: dict) -> str | None:
        """Ensure content_id is properly formatted with angle brackets.

        Args:
            v: The content_id value
            _: Unused field values

        Returns:
            Properly formatted content_id
        """
        if v and not v.startswith("<"):
            return f"<{v}>"
        return v
