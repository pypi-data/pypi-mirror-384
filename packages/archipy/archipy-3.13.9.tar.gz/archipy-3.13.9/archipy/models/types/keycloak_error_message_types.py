# Add these to your ErrorMessageType enum
from enum import Enum
from typing import TYPE_CHECKING

from archipy.models.dtos.error_dto import ErrorDetailDTO

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


class KeycloakErrorMessageType(Enum):
    """Enumeration of Keycloak error message types.

    Contains predefined error message templates for common Keycloak operations
    and authentication scenarios, providing localized error messages in both
    Farsi and English.
    """

    REALM_ALREADY_EXISTS = ErrorDetailDTO(
        code="REALM_ALREADY_EXISTS",
        message_en="Realm already exists",
        message_fa="قلمرو از قبل وجود دارد",
        http_status=409,
        grpc_status=6,
    )

    USER_ALREADY_EXISTS = ErrorDetailDTO(
        code="USER_ALREADY_EXISTS",
        message_en="User already exists",
        message_fa="کاربر از قبل وجود دارد",
        http_status=409,
        grpc_status=6,
    )

    CLIENT_ALREADY_EXISTS = ErrorDetailDTO(
        code="CLIENT_ALREADY_EXISTS",
        message_en="Client already exists",
        message_fa="کلاینت از قبل وجود دارد",
        http_status=409,
        grpc_status=6,
    )

    ROLE_ALREADY_EXISTS = ErrorDetailDTO(
        code="ROLE_ALREADY_EXISTS",
        message_en="Role already exists",
        message_fa="نقش از قبل وجود دارد",
        http_status=409,
        grpc_status=6,
    )

    INVALID_CREDENTIALS = ErrorDetailDTO(
        code="INVALID_CREDENTIALS",
        message_en="Invalid credentials",
        message_fa="اطلاعات ورود نامعتبر",
        http_status=401,
        grpc_status=16,
    )

    RESOURCE_NOT_FOUND = ErrorDetailDTO(
        code="RESOURCE_NOT_FOUND",
        message_en="Resource not found",
        message_fa="منبع یافت نشد",
        http_status=404,
        grpc_status=5,
    )

    INSUFFICIENT_PERMISSIONS = ErrorDetailDTO(
        code="INSUFFICIENT_PERMISSIONS",
        message_en="Insufficient permissions",
        message_fa="دسترسی کافی نیست",
        http_status=403,
        grpc_status=7,
    )

    VALIDATION_ERROR = ErrorDetailDTO(
        code="VALIDATION_ERROR",
        message_en="Validation error",
        message_fa="خطای اعتبارسنجی",
        http_status=400,
        grpc_status=3,
    )

    PASSWORD_POLICY_VIOLATION = ErrorDetailDTO(
        code="PASSWORD_POLICY_VIOLATION",
        message_en="Password does not meet policy requirements",
        message_fa="رمز عبور الزامات سیاست را برآورده نمی‌کند",
        http_status=400,
        grpc_status=3,
    )

    CONNECTION_TIMEOUT = ErrorDetailDTO(
        code="CONNECTION_TIMEOUT",
        message_en="Connection timeout",
        message_fa="زمان اتصال به پایان رسید",
        http_status=504,
        grpc_status=4,
    )

    SERVICE_UNAVAILABLE = ErrorDetailDTO(
        code="SERVICE_UNAVAILABLE",
        message_en="Service unavailable",
        message_fa="سرویس در دسترس نیست",
        http_status=503,
        grpc_status=14,
    )
