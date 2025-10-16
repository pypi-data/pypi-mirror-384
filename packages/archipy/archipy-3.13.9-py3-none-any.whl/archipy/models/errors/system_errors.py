from typing import Any, ClassVar

from archipy.models.dtos.error_dto import ErrorDetailDTO
from archipy.models.errors.base_error import BaseError
from archipy.models.types.error_message_types import ErrorMessageType
from archipy.models.types.language_type import LanguageType


class InternalError(BaseError):
    """Represents an internal server error.

    This error is typically used when an unexpected condition is encountered
    that prevents the server from fulfilling the request.
    """

    def __init__(
        self,
        error_code: str | None = None,
        lang: LanguageType | None = None,
        error: ErrorDetailDTO = ErrorMessageType.INTERNAL_ERROR.value,
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        data = {}
        if error_code:
            data["error_code"] = error_code
        if additional_data:
            data.update(additional_data)
        super().__init__(error, lang, data if data else None)


class ConfigurationError(BaseError):
    """Represents a configuration error.

    This error is used when there is a problem with the application's
    configuration that prevents it from operating correctly.
    """

    def __init__(
        self,
        operation: str | None = None,
        reason: str | None = None,
        lang: LanguageType | None = None,
        error: ErrorDetailDTO = ErrorMessageType.CONFIGURATION_ERROR.value,
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        data = {}
        if operation:
            data["operation"] = operation
        if reason:
            data["reason"] = reason
        if additional_data:
            data.update(additional_data)
        super().__init__(error, lang, data if data else None)


class UnavailableError(BaseError):
    """Represents a resource unavailability error.

    This error is used when a required resource is temporarily unavailable
    but may become available again in the future.
    """

    def __init__(
        self,
        resource_type: str | None = None,
        lang: LanguageType | None = None,
        error: ErrorDetailDTO = ErrorMessageType.UNAVAILABLE.value,
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        data = {}
        if resource_type:
            data["resource_type"] = resource_type
        if additional_data:
            data.update(additional_data)
        super().__init__(error, lang, data if data else None)


class UnknownError(BaseError):
    """Represents an unknown error.

    This is a catch-all error type for unexpected conditions that
    don't fit into other error categories.
    """

    def __init__(
        self,
        config_key: str | None = None,
        lang: LanguageType | None = None,
        error: ErrorDetailDTO = ErrorMessageType.UNKNOWN_ERROR.value,
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        data = {}
        if config_key:
            data["config_key"] = config_key
        if additional_data:
            data.update(additional_data)
        super().__init__(error, lang, data if data else None)


class AbortedError(BaseError):
    """Represents an aborted operation error.

    This error is used when an operation is aborted, typically due to
    a concurrency issue or user cancellation.
    """

    def __init__(
        self,
        service: str | None = None,
        reason: str | None = None,
        lang: LanguageType | None = None,
        error: ErrorDetailDTO = ErrorMessageType.UNAVAILABLE.value,
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        data = {}
        if service:
            data["service"] = service
        if reason:
            data["reason"] = reason
        if additional_data:
            data.update(additional_data)
        super().__init__(error, lang, data if data else None)


class DeadlockDetectedError(BaseError):
    """Represents a deadlock detection error.

    This error is used when a deadlock is detected in a system operation,
    typically in database transactions or resource locking scenarios.
    """

    def __init__(
        self,
        service: str | None = None,
        reason: str | None = None,
        lang: LanguageType | None = None,
        error: ErrorDetailDTO = ErrorMessageType.UNAVAILABLE.value,
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        data = {}
        if service:
            data["service"] = service
        if reason:
            data["reason"] = reason
        if additional_data:
            data.update(additional_data)
        super().__init__(error, lang, data if data else None)


class DeadlineExceededError(BaseError):
    """Raised when an operation exceeds its deadline/timeout.

    This error is typically used in decorators or functions that have
    time limits or deadlines for completion.
    """

    http_status_code: ClassVar[int] = 408  # Request Timeout
    grpc_status_code: ClassVar[int] = 4  # DEADLINE_EXCEEDED

    def __init__(
        self,
        timeout: int | None = None,
        operation: str | None = None,
        lang: LanguageType | None = None,
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize DeadlineExceededError.

        Args:
            timeout: The timeout value that was exceeded (in seconds).
            operation: The operation that exceeded the deadline.
            lang: The language for error messages.
            additional_data: Additional context data.
        """
        error = ErrorDetailDTO(
            code="DEADLINE_EXCEEDED",
            message_en="Operation exceeded its deadline",
            message_fa="عملیات از مهلت زمانی مجاز تجاوز کرد",
            http_status=self.http_status_code,
            grpc_status=self.grpc_status_code,
        )

        data = {}
        if timeout is not None:
            data["timeout"] = timeout
        if operation:
            data["operation"] = operation
        if additional_data:
            data.update(additional_data)
        super().__init__(error, lang, data if data else None)


class DeprecationError(BaseError):
    """Raised when deprecated functionality is used.

    This error is used to signal that a feature, method, or API
    is deprecated and should no longer be used.
    """

    http_status_code: ClassVar[int] = 410  # Gone
    grpc_status_code: ClassVar[int] = 12  # UNIMPLEMENTED

    def __init__(
        self,
        deprecated_feature: str | None = None,
        replacement: str | None = None,
        removal_version: str | None = None,
        lang: LanguageType | None = None,
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize DeprecationError.

        Args:
            deprecated_feature: The name of the deprecated feature.
            replacement: The recommended replacement feature.
            removal_version: The version when the feature will be removed.
            lang: The language for error messages.
            additional_data: Additional context data.
        """
        error = ErrorDetailDTO(
            code="DEPRECATED_FEATURE",
            message_en="This feature is deprecated and should no longer be used",
            message_fa="این ویژگی منسوخ شده و دیگر نباید استفاده شود",
            http_status=self.http_status_code,
            grpc_status=self.grpc_status_code,
        )

        data = {}
        if deprecated_feature:
            data["deprecated_feature"] = deprecated_feature
        if replacement:
            data["replacement"] = replacement
        if removal_version:
            data["removal_version"] = removal_version
        if additional_data:
            data.update(additional_data)
        super().__init__(error, lang, data if data else None)
