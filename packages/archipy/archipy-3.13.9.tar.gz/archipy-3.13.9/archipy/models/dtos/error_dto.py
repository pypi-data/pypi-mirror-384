from typing import TYPE_CHECKING, Self

from archipy.models.dtos.base_dtos import BaseDTO

try:
    from http import HTTPStatus

    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    if not TYPE_CHECKING:
        # Only create at runtime, not during type checking
        HTTPStatus = None

try:
    from grpc import StatusCode

    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    if not TYPE_CHECKING:
        # Only create at runtime, not during type checking
        StatusCode = None


class ErrorDetailDTO(BaseDTO):
    """Standardized error detail model."""

    code: str
    message_en: str
    message_fa: str
    http_status: int | None = None
    grpc_status: int | None = None

    @classmethod
    def create_error_detail(
        cls,
        code: str,
        message_en: str,
        message_fa: str,
        http_status: HTTPStatus | int | None = None,
        grpc_status: StatusCode | int | None = None,
    ) -> Self:
        """Creates an `ErrorDetailDTO` with appropriate status codes.

        Args:
            code (str): A unique error code.
            message_en (str): The error message in English.
            message_fa (str): The error message in Persian.
            http_status (HTTPStatus | int | None): The HTTP status code associated with the error.
            grpc_status (StatusCode | int  | None): The gRPC status code associated with the error.

        Returns:
            ErrorDetailDTO: The created exception detail object.
        """
        status_kwargs = {}

        if HTTP_AVAILABLE and http_status is not None:
            status_kwargs["http_status"] = http_status.value if isinstance(http_status, HTTPStatus) else http_status

        if GRPC_AVAILABLE and grpc_status is not None:
            # StatusCode.value can be a tuple, but we need only the first element (integer value)
            if isinstance(grpc_status, StatusCode):
                status_kwargs["grpc_status"] = (
                    grpc_status.value[0] if isinstance(grpc_status.value, tuple) else grpc_status.value
                )
            else:
                status_kwargs["grpc_status"] = grpc_status

        # We need to use cls() for proper typing with Self return type
        return cls(code=code, message_en=message_en, message_fa=message_fa, **status_kwargs)
