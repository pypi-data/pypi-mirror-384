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


class ErrorMessageType(Enum):
    """Enumeration of exception types with associated error details.

    This class defines a set of standard exception types, each with an associated error code,
    English and Farsi messages, and corresponding HTTP and gRPC status codes.

    Attributes:
        UNAUTHENTICATED: Indicates that the user is not authenticated.
        INVALID_PHONE: Indicates an invalid Iranian phone number.
        INVALID_LANDLINE: Indicates an invalid Iranian landline number.
        INVALID_NATIONAL_CODE: Indicates an invalid national code format.
        TOKEN_EXPIRED: Indicates that the authentication token has expired.
        INVALID_TOKEN: Indicates an invalid authentication token.
        PERMISSION_DENIED: Indicates that the user does not have permission for the operation.
        NOT_FOUND: Indicates that the requested resource was not found.
        ALREADY_EXISTS: Indicates that the resource already exists.
        INVALID_ARGUMENT: Indicates an invalid argument was provided.
        OUT_OF_RANGE: Indicates that a value is out of the acceptable range.
        DEADLINE_EXCEEDED: Indicates that the operation deadline was exceeded.
        FAILED_PRECONDITION: Indicates that the operation preconditions were not met.
        RESOURCE_EXHAUSTED: Indicates that the resource limit has been reached.
        ABORTED: Indicates that the operation was aborted.
        CANCELLED: Indicates that the operation was cancelled.
        INVALID_ENTITY_TYPE: Indicates an invalid entity type.
        INTERNAL_ERROR: Indicates an internal system error.
        DATA_LOSS: Indicates critical data loss.
        UNIMPLEMENTED: Indicates that the operation is not implemented.
        DEPRECATION: Indicates that the operation is deprecated.
        UNAVAILABLE: Indicates that the service is unavailable.
        UNKNOWN_ERROR: Indicates an unknown error occurred.
        DEADLOCK: Indicates a deadlock condition was detected.
    """

    # Authentication Errors (400, 401, 403)
    UNAUTHENTICATED = ErrorDetailDTO.create_error_detail(
        code="UNAUTHENTICATED",
        message_en="You are not authorized to perform this action.",
        message_fa="شما مجوز انجام این عمل را ندارید.",
        http_status=HTTPStatus.UNAUTHORIZED if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAUTHENTICATED if GRPC_AVAILABLE else None,
    )
    INVALID_PHONE = ErrorDetailDTO.create_error_detail(
        code="INVALID_PHONE",
        message_en="Invalid Iranian phone number",
        message_fa="شماره تلفن همراه ایران نامعتبر است.",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    INVALID_LANDLINE = ErrorDetailDTO.create_error_detail(
        code="INVALID_LANDLINE",
        message_en="Invalid Iranian landline number",
        message_fa="شماره تلفن ثابت ایران نامعتبر است.",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    INVALID_NATIONAL_CODE = ErrorDetailDTO.create_error_detail(
        code="INVALID_NATIONAL_CODE",
        message_en="Invalid national code format",
        message_fa="فرمت کد ملی وارد شده اشتباه است.",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    TOKEN_EXPIRED = ErrorDetailDTO.create_error_detail(
        code="TOKEN_EXPIRED",
        message_en="Authentication token has expired",
        message_fa="توکن احراز هویت منقضی شده است.",
        http_status=HTTPStatus.UNAUTHORIZED if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAUTHENTICATED if GRPC_AVAILABLE else None,
    )

    INVALID_TOKEN = ErrorDetailDTO.create_error_detail(
        code="INVALID_TOKEN",
        message_en="Invalid authentication token",
        message_fa="توکن احراز هویت نامعتبر است.",
        http_status=HTTPStatus.UNAUTHORIZED if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAUTHENTICATED if GRPC_AVAILABLE else None,
    )

    PERMISSION_DENIED = ErrorDetailDTO.create_error_detail(
        code="PERMISSION_DENIED",
        message_en="Permission denied for this operation",
        message_fa="دسترسی برای انجام این عملیات وجود ندارد.",
        http_status=HTTPStatus.FORBIDDEN if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.PERMISSION_DENIED if GRPC_AVAILABLE else None,
    )

    # Resource Errors (404, 409)
    NOT_FOUND = ErrorDetailDTO.create_error_detail(
        code="NOT_FOUND",
        message_en="Requested resource not found",
        message_fa="منبع درخواستی یافت نشد.",
        http_status=HTTPStatus.NOT_FOUND if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.NOT_FOUND if GRPC_AVAILABLE else None,
    )

    ALREADY_EXISTS = ErrorDetailDTO.create_error_detail(
        code="ALREADY_EXISTS",
        message_en="Resource already exists",
        message_fa="منبع از قبل موجود است.",
        http_status=HTTPStatus.CONFLICT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.ALREADY_EXISTS if GRPC_AVAILABLE else None,
    )

    # Validation Errors (400)
    INVALID_ARGUMENT = ErrorDetailDTO.create_error_detail(
        code="INVALID_ARGUMENT",
        message_en="Invalid argument provided",
        message_fa="پارامتر ورودی نامعتبر است.",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    INVALID_PASSWORD = ErrorDetailDTO.create_error_detail(
        code="INVALID_PASSWORD",
        message_en="Password does not meet the security requirements",
        message_fa="رمز عبور الزامات امنیتی را برآورده نمی‌کند.",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    OUT_OF_RANGE = ErrorDetailDTO.create_error_detail(
        code="OUT_OF_RANGE",
        message_en="Value is out of acceptable range",
        message_fa="مقدار خارج از محدوده مجاز است.",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.OUT_OF_RANGE if GRPC_AVAILABLE else None,
    )

    # Operation Errors (408, 409, 412, 429)
    DEADLINE_EXCEEDED = ErrorDetailDTO.create_error_detail(
        code="DEADLINE_EXCEEDED",
        message_en="Operation deadline exceeded",
        message_fa="مهلت انجام عملیات به پایان رسیده است.",
        http_status=HTTPStatus.REQUEST_TIMEOUT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.DEADLINE_EXCEEDED if GRPC_AVAILABLE else None,
    )

    FAILED_PRECONDITION = ErrorDetailDTO.create_error_detail(
        code="FAILED_PRECONDITION",
        message_en="Operation preconditions not met",
        message_fa="پیش‌نیازهای عملیات برآورده نشده است.",
        http_status=HTTPStatus.PRECONDITION_FAILED if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.FAILED_PRECONDITION if GRPC_AVAILABLE else None,
    )

    RESOURCE_EXHAUSTED = ErrorDetailDTO.create_error_detail(
        code="RESOURCE_EXHAUSTED",
        message_en="Resource limit has been reached",
        message_fa="محدودیت منابع به پایان رسیده است.",
        http_status=HTTPStatus.TOO_MANY_REQUESTS if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.RESOURCE_EXHAUSTED if GRPC_AVAILABLE else None,
    )

    ABORTED = ErrorDetailDTO.create_error_detail(
        code="ABORTED",
        message_en="Operation was aborted",
        message_fa="عملیات متوقف شد.",
        http_status=HTTPStatus.CONFLICT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.ABORTED if GRPC_AVAILABLE else None,
    )

    CANCELLED = ErrorDetailDTO.create_error_detail(
        code="CANCELLED",
        message_en="Operation was cancelled",
        message_fa="عملیات لغو شد.",
        http_status=HTTPStatus.CONFLICT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.CANCELLED if GRPC_AVAILABLE else None,
    )

    INSUFFICIENT_BALANCE = ErrorDetailDTO.create_error_detail(
        code="INSUFFICIENT_BALANCE",
        message_en="Insufficient balance for operation",
        message_fa="عدم موجودی کافی برای عملیات.",
        http_status=HTTPStatus.PAYMENT_REQUIRED if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.FAILED_PRECONDITION if GRPC_AVAILABLE else None,
    )

    # System Errors (500, 501, 503)
    INVALID_ENTITY_TYPE = ErrorDetailDTO.create_error_detail(
        code="INVALID_ENTITY",
        message_en="Invalid entity type",
        message_fa="نوع موجودیت نامعتبر است.",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )
    INTERNAL_ERROR = ErrorDetailDTO.create_error_detail(
        code="INTERNAL_ERROR",
        message_en="Internal system error occurred",
        message_fa="خطای داخلی سیستم رخ داده است.",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    DATA_LOSS = ErrorDetailDTO.create_error_detail(
        code="DATA_LOSS",
        message_en="Critical data loss detected",
        message_fa="از دست دادن اطلاعات حیاتی تشخیص داده شد.",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.DATA_LOSS if GRPC_AVAILABLE else None,
    )

    UNIMPLEMENTED = ErrorDetailDTO.create_error_detail(
        code="UNIMPLEMENTED",
        message_en="Requested operation is not implemented",
        message_fa="عملیات درخواستی پیاده‌سازی نشده است.",
        http_status=HTTPStatus.NOT_IMPLEMENTED if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNIMPLEMENTED if GRPC_AVAILABLE else None,
    )

    DEPRECATION = ErrorDetailDTO.create_error_detail(
        code="DEPRECATION",
        message_en="This operation is deprecated and will be removed in a future version.",
        message_fa="این عملیات منسوخ شده و در نسخه‌های آینده حذف خواهد شد.",
        http_status=HTTPStatus.GONE if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAVAILABLE if GRPC_AVAILABLE else None,
    )

    UNAVAILABLE = ErrorDetailDTO.create_error_detail(
        code="UNAVAILABLE",
        message_en="Service is currently unavailable",
        message_fa="سرویس در حال حاضر در دسترس نیست.",
        http_status=HTTPStatus.SERVICE_UNAVAILABLE if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAVAILABLE if GRPC_AVAILABLE else None,
    )

    UNKNOWN_ERROR = ErrorDetailDTO.create_error_detail(
        code="UNKNOWN_ERROR",
        message_en="An unknown error occurred",
        message_fa="خطای ناشناخته‌ای رخ داده است.",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNKNOWN if GRPC_AVAILABLE else None,
    )

    DEADLOCK = ErrorDetailDTO.create_error_detail(
        code="DEADLOCK",
        message_en="Deadlock detected",
        message_fa="خطای قفل‌شدگی (Deadlock) تشخیص داده شد.",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    # Authentication & Authorization
    INVALID_CREDENTIALS = ErrorDetailDTO.create_error_detail(
        code="INVALID_CREDENTIALS",
        message_en="Invalid username or password",
        message_fa="نام کاربری یا رمز عبور نامعتبر است",
        http_status=HTTPStatus.UNAUTHORIZED if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAUTHENTICATED if GRPC_AVAILABLE else None,
    )

    ACCOUNT_LOCKED = ErrorDetailDTO.create_error_detail(
        code="ACCOUNT_LOCKED",
        message_en="Account has been locked due to too many failed attempts",
        message_fa="حساب کاربری به دلیل تلاش‌های ناموفق متعدد قفل شده است",
        http_status=HTTPStatus.FORBIDDEN if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.PERMISSION_DENIED if GRPC_AVAILABLE else None,
    )

    ACCOUNT_DISABLED = ErrorDetailDTO.create_error_detail(
        code="ACCOUNT_DISABLED",
        message_en="Account has been disabled",
        message_fa="حساب کاربری غیرفعال شده است",
        http_status=HTTPStatus.FORBIDDEN if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.PERMISSION_DENIED if GRPC_AVAILABLE else None,
    )

    SESSION_EXPIRED = ErrorDetailDTO.create_error_detail(
        code="SESSION_EXPIRED",
        message_en="Session has expired",
        message_fa="نشست کاربری منقضی شده است",
        http_status=HTTPStatus.UNAUTHORIZED if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAUTHENTICATED if GRPC_AVAILABLE else None,
    )

    INVALID_REFRESH_TOKEN = ErrorDetailDTO.create_error_detail(
        code="INVALID_REFRESH_TOKEN",
        message_en="Invalid refresh token",
        message_fa="توکن تازه‌سازی نامعتبر است",
        http_status=HTTPStatus.UNAUTHORIZED if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAUTHENTICATED if GRPC_AVAILABLE else None,
    )

    INVALID_VERIFICATION_CODE = ErrorDetailDTO.create_error_detail(
        code="INVALID_VERIFICATION_CODE",
        message_en="Invalid verification code",
        message_fa="کد تایید نامعتبر است",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    # Resource & Data
    CONFLICT = ErrorDetailDTO.create_error_detail(
        code="CONFLICT",
        message_en="Resource conflict detected",
        message_fa="تعارض در منابع تشخیص داده شد",
        http_status=HTTPStatus.CONFLICT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.ABORTED if GRPC_AVAILABLE else None,
    )

    INVALID_FORMAT = ErrorDetailDTO.create_error_detail(
        code="INVALID_FORMAT",
        message_en="Invalid data format",
        message_fa="فرمت داده نامعتبر است",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    FILE_TOO_LARGE = ErrorDetailDTO.create_error_detail(
        code="FILE_TOO_LARGE",
        message_en="File size exceeds the maximum allowed limit",
        message_fa="حجم فایل از حد مجاز بیشتر است",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    INVALID_FILE_TYPE = ErrorDetailDTO.create_error_detail(
        code="INVALID_FILE_TYPE",
        message_en="File type is not supported",
        message_fa="نوع فایل پشتیبانی نمی‌شود",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    QUOTA_EXCEEDED = ErrorDetailDTO.create_error_detail(
        code="QUOTA_EXCEEDED",
        message_en="Storage quota has been exceeded",
        message_fa="سهمیه ذخیره‌سازی به پایان رسیده است",
        http_status=HTTPStatus.FORBIDDEN if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.RESOURCE_EXHAUSTED if GRPC_AVAILABLE else None,
    )

    RATE_LIMIT_EXCEEDED = ErrorDetailDTO.create_error_detail(
        code="RATE_LIMIT_EXCEEDED",
        message_en="Rate limit has been exceeded",
        message_fa="محدودیت نرخ درخواست به پایان رسیده است",
        http_status=HTTPStatus.TOO_MANY_REQUESTS if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.RESOURCE_EXHAUSTED if GRPC_AVAILABLE else None,
    )

    # Network & Communication
    CONNECTION_TIMEOUT = ErrorDetailDTO.create_error_detail(
        code="CONNECTION_TIMEOUT",
        message_en="Connection timed out",
        message_fa="اتصال با تایم‌اوت مواجه شد",
        http_status=HTTPStatus.REQUEST_TIMEOUT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.DEADLINE_EXCEEDED if GRPC_AVAILABLE else None,
    )

    NETWORK_ERROR = ErrorDetailDTO.create_error_detail(
        code="NETWORK_ERROR",
        message_en="Network error occurred",
        message_fa="خطای شبکه رخ داده است",
        http_status=HTTPStatus.BAD_GATEWAY if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAVAILABLE if GRPC_AVAILABLE else None,
    )

    SERVICE_UNAVAILABLE = ErrorDetailDTO.create_error_detail(
        code="SERVICE_UNAVAILABLE",
        message_en="Service is currently unavailable",
        message_fa="سرویس در حال حاضر در دسترس نیست",
        http_status=HTTPStatus.SERVICE_UNAVAILABLE if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAVAILABLE if GRPC_AVAILABLE else None,
    )

    GATEWAY_TIMEOUT = ErrorDetailDTO.create_error_detail(
        code="GATEWAY_TIMEOUT",
        message_en="Gateway timeout",
        message_fa="تایم‌اوت دروازه",
        http_status=HTTPStatus.GATEWAY_TIMEOUT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.DEADLINE_EXCEEDED if GRPC_AVAILABLE else None,
    )

    BAD_GATEWAY = ErrorDetailDTO.create_error_detail(
        code="BAD_GATEWAY",
        message_en="Bad gateway",
        message_fa="دروازه نامعتبر",
        http_status=HTTPStatus.BAD_GATEWAY if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAVAILABLE if GRPC_AVAILABLE else None,
    )

    # Business Logic
    INVALID_STATE = ErrorDetailDTO.create_error_detail(
        code="INVALID_STATE",
        message_en="Invalid state for the requested operation",
        message_fa="وضعیت نامعتبر برای عملیات درخواستی",
        http_status=HTTPStatus.CONFLICT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.FAILED_PRECONDITION if GRPC_AVAILABLE else None,
    )

    BUSINESS_RULE_VIOLATION = ErrorDetailDTO.create_error_detail(
        code="BUSINESS_RULE_VIOLATION",
        message_en="Business rule violation",
        message_fa="نقض قوانین کسب و کار",
        http_status=HTTPStatus.CONFLICT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.FAILED_PRECONDITION if GRPC_AVAILABLE else None,
    )

    INSUFFICIENT_FUNDS = ErrorDetailDTO.create_error_detail(
        code="INSUFFICIENT_FUNDS",
        message_en="Insufficient funds for the operation",
        message_fa="موجودی ناکافی برای عملیات",
        http_status=HTTPStatus.PAYMENT_REQUIRED if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.FAILED_PRECONDITION if GRPC_AVAILABLE else None,
    )

    INVALID_OPERATION = ErrorDetailDTO.create_error_detail(
        code="INVALID_OPERATION",
        message_en="Operation is not allowed in the current context",
        message_fa="عملیات در وضعیت فعلی مجاز نیست",
        http_status=HTTPStatus.FORBIDDEN if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.PERMISSION_DENIED if GRPC_AVAILABLE else None,
    )

    MAINTENANCE_MODE = ErrorDetailDTO.create_error_detail(
        code="MAINTENANCE_MODE",
        message_en="System is currently in maintenance mode",
        message_fa="سیستم در حال حاضر در حالت تعمیر و نگهداری است",
        http_status=HTTPStatus.SERVICE_UNAVAILABLE if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAVAILABLE if GRPC_AVAILABLE else None,
    )

    # Validation
    INVALID_EMAIL = ErrorDetailDTO.create_error_detail(
        code="INVALID_EMAIL",
        message_en="Invalid email format",
        message_fa="فرمت ایمیل نامعتبر است",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    INVALID_DATE = ErrorDetailDTO.create_error_detail(
        code="INVALID_DATE",
        message_en="Invalid date format",
        message_fa="فرمت تاریخ نامعتبر است",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    INVALID_URL = ErrorDetailDTO.create_error_detail(
        code="INVALID_URL",
        message_en="Invalid URL format",
        message_fa="فرمت URL نامعتبر است",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    INVALID_IP = ErrorDetailDTO.create_error_detail(
        code="INVALID_IP",
        message_en="Invalid IP address format",
        message_fa="فرمت آدرس IP نامعتبر است",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    INVALID_JSON = ErrorDetailDTO.create_error_detail(
        code="INVALID_JSON",
        message_en="Invalid JSON format",
        message_fa="فرمت JSON نامعتبر است",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    # Database & Storage Errors
    DATABASE_ERROR = ErrorDetailDTO.create_error_detail(
        code="DATABASE_ERROR",
        message_en="Database error occurred",
        message_fa="خطای پایگاه داده رخ داده است",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    DATABASE_CONNECTION_ERROR = ErrorDetailDTO.create_error_detail(
        code="DATABASE_CONNECTION_ERROR",
        message_en="Failed to connect to the database",
        message_fa="خطا در اتصال به پایگاه داده",
        http_status=HTTPStatus.SERVICE_UNAVAILABLE if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAVAILABLE if GRPC_AVAILABLE else None,
    )

    DATABASE_QUERY_ERROR = ErrorDetailDTO.create_error_detail(
        code="DATABASE_QUERY_ERROR",
        message_en="Error executing database query",
        message_fa="خطا در اجرای پرس و جوی پایگاه داده",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    DATABASE_TRANSACTION_ERROR = ErrorDetailDTO.create_error_detail(
        code="DATABASE_TRANSACTION_ERROR",
        message_en="Error in database transaction",
        message_fa="خطا در تراکنش پایگاه داده",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    DATABASE_TIMEOUT_ERROR = ErrorDetailDTO.create_error_detail(
        code="DATABASE_TIMEOUT_ERROR",
        message_en="Database operation timed out",
        message_fa="عملیات پایگاه داده با تایم‌اوت مواجه شد",
        http_status=HTTPStatus.REQUEST_TIMEOUT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.DEADLINE_EXCEEDED if GRPC_AVAILABLE else None,
    )

    DATABASE_CONSTRAINT_ERROR = ErrorDetailDTO.create_error_detail(
        code="DATABASE_CONSTRAINT_ERROR",
        message_en="Database constraint violation",
        message_fa="نقض محدودیت پایگاه داده",
        http_status=HTTPStatus.CONFLICT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.FAILED_PRECONDITION if GRPC_AVAILABLE else None,
    )

    DATABASE_INTEGRITY_ERROR = ErrorDetailDTO.create_error_detail(
        code="DATABASE_INTEGRITY_ERROR",
        message_en="Database integrity violation",
        message_fa="نقض یکپارچگی پایگاه داده",
        http_status=HTTPStatus.CONFLICT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.FAILED_PRECONDITION if GRPC_AVAILABLE else None,
    )

    DATABASE_DEADLOCK_ERROR = ErrorDetailDTO.create_error_detail(
        code="DATABASE_DEADLOCK_ERROR",
        message_en="Database deadlock detected",
        message_fa="قفل‌شدگی پایگاه داده تشخیص داده شد",
        http_status=HTTPStatus.CONFLICT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.ABORTED if GRPC_AVAILABLE else None,
    )

    DATABASE_SERIALIZATION_ERROR = ErrorDetailDTO.create_error_detail(
        code="DATABASE_SERIALIZATION_ERROR",
        message_en="Database serialization failure",
        message_fa="خطای سریال‌سازی پایگاه داده",
        http_status=HTTPStatus.CONFLICT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.ABORTED if GRPC_AVAILABLE else None,
    )

    DATABASE_CONFIGURATION_ERROR = ErrorDetailDTO.create_error_detail(
        code="DATABASE_CONFIGURATION_ERROR",
        message_en="Database configuration error",
        message_fa="خطای پیکربندی پایگاه داده",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    STORAGE_ERROR = ErrorDetailDTO.create_error_detail(
        code="STORAGE_ERROR",
        message_en="Storage access error occurred",
        message_fa="خطا در دسترسی به فضای ذخیره‌سازی",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    # Cache Errors
    CACHE_ERROR = ErrorDetailDTO.create_error_detail(
        code="CACHE_ERROR",
        message_en="Error accessing cache",
        message_fa="خطا در دسترسی به حافظه نهان",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    CACHE_MISS = ErrorDetailDTO.create_error_detail(
        code="CACHE_MISS",
        message_en="Requested data not found in cache",
        message_fa="داده درخواستی در حافظه نهان یافت نشد",
        http_status=HTTPStatus.NOT_FOUND if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.NOT_FOUND if GRPC_AVAILABLE else None,
    )

    # Message Queue Errors
    QUEUE_ERROR = ErrorDetailDTO.create_error_detail(
        code="QUEUE_ERROR",
        message_en="Error in message queue operation",
        message_fa="خطا در عملیات صف پیام",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    QUEUE_FULL = ErrorDetailDTO.create_error_detail(
        code="QUEUE_FULL",
        message_en="Message queue is full",
        message_fa="صف پیام پر است",
        http_status=HTTPStatus.SERVICE_UNAVAILABLE if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.RESOURCE_EXHAUSTED if GRPC_AVAILABLE else None,
    )

    # Search Engine Errors
    SEARCH_ERROR = ErrorDetailDTO.create_error_detail(
        code="SEARCH_ERROR",
        message_en="Error performing search operation",
        message_fa="خطا در انجام عملیات جستجو",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    SEARCH_TIMEOUT = ErrorDetailDTO.create_error_detail(
        code="SEARCH_TIMEOUT",
        message_en="Search operation timed out",
        message_fa="عملیات جستجو با تایم‌اوت مواجه شد",
        http_status=HTTPStatus.REQUEST_TIMEOUT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.DEADLINE_EXCEEDED if GRPC_AVAILABLE else None,
    )

    # External Service Errors
    EXTERNAL_SERVICE_ERROR = ErrorDetailDTO.create_error_detail(
        code="EXTERNAL_SERVICE_ERROR",
        message_en="Error in external service",
        message_fa="خطا در سرویس خارجی",
        http_status=HTTPStatus.BAD_GATEWAY if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAVAILABLE if GRPC_AVAILABLE else None,
    )

    EXTERNAL_SERVICE_TIMEOUT = ErrorDetailDTO.create_error_detail(
        code="EXTERNAL_SERVICE_TIMEOUT",
        message_en="External service request timed out",
        message_fa="درخواست به سرویس خارجی با تایم‌اوت مواجه شد",
        http_status=HTTPStatus.GATEWAY_TIMEOUT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.DEADLINE_EXCEEDED if GRPC_AVAILABLE else None,
    )

    # Security Errors
    SECURITY_ERROR = ErrorDetailDTO.create_error_detail(
        code="SECURITY_ERROR",
        message_en="Security violation detected",
        message_fa="نقض امنیتی تشخیص داده شد",
        http_status=HTTPStatus.FORBIDDEN if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.PERMISSION_DENIED if GRPC_AVAILABLE else None,
    )

    INVALID_SIGNATURE = ErrorDetailDTO.create_error_detail(
        code="INVALID_SIGNATURE",
        message_en="Invalid digital signature",
        message_fa="امضای دیجیتال نامعتبر است",
        http_status=HTTPStatus.UNAUTHORIZED if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAUTHENTICATED if GRPC_AVAILABLE else None,
    )

    INVALID_CERTIFICATE = ErrorDetailDTO.create_error_detail(
        code="INVALID_CERTIFICATE",
        message_en="Invalid security certificate",
        message_fa="گواهی امنیتی نامعتبر است",
        http_status=HTTPStatus.UNAUTHORIZED if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.UNAUTHENTICATED if GRPC_AVAILABLE else None,
    )

    # Configuration Errors
    CONFIGURATION_ERROR = ErrorDetailDTO.create_error_detail(
        code="CONFIGURATION_ERROR",
        message_en="Error in system configuration",
        message_fa="خطا در پیکربندی سیستم",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    MISSING_CONFIGURATION = ErrorDetailDTO.create_error_detail(
        code="MISSING_CONFIGURATION",
        message_en="Required configuration is missing",
        message_fa="پیکربندی مورد نیاز وجود ندارد",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.FAILED_PRECONDITION if GRPC_AVAILABLE else None,
    )

    # Integration Errors
    INTEGRATION_ERROR = ErrorDetailDTO.create_error_detail(
        code="INTEGRATION_ERROR",
        message_en="Error in system integration",
        message_fa="خطا در یکپارچه‌سازی سیستم",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    INCOMPATIBLE_VERSION = ErrorDetailDTO.create_error_detail(
        code="INCOMPATIBLE_VERSION",
        message_en="Incompatible system version",
        message_fa="نسخه سیستم ناسازگار است",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.FAILED_PRECONDITION if GRPC_AVAILABLE else None,
    )

    # Monitoring & Logging Errors
    MONITORING_ERROR = ErrorDetailDTO.create_error_detail(
        code="MONITORING_ERROR",
        message_en="Error in monitoring system",
        message_fa="خطا در سیستم نظارت",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    LOGGING_ERROR = ErrorDetailDTO.create_error_detail(
        code="LOGGING_ERROR",
        message_en="Error in logging system",
        message_fa="خطا در سیستم ثبت رویدادها",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    # Backup & Recovery Errors
    BACKUP_ERROR = ErrorDetailDTO.create_error_detail(
        code="BACKUP_ERROR",
        message_en="Error in backup operation",
        message_fa="خطا در عملیات پشتیبان‌گیری",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    RECOVERY_ERROR = ErrorDetailDTO.create_error_detail(
        code="RECOVERY_ERROR",
        message_en="Error in recovery operation",
        message_fa="خطا در عملیات بازیابی",
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INTERNAL if GRPC_AVAILABLE else None,
    )

    # Resource Management Errors
    RESOURCE_LOCKED = ErrorDetailDTO.create_error_detail(
        code="RESOURCE_LOCKED",
        message_en="Resource is currently locked",
        message_fa="منبع در حال حاضر قفل شده است",
        http_status=HTTPStatus.CONFLICT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.ABORTED if GRPC_AVAILABLE else None,
    )

    RESOURCE_BUSY = ErrorDetailDTO.create_error_detail(
        code="RESOURCE_BUSY",
        message_en="Resource is currently busy",
        message_fa="منبع در حال حاضر مشغول است",
        http_status=HTTPStatus.CONFLICT if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.ABORTED if GRPC_AVAILABLE else None,
    )

    # Time-related Errors
    INVALID_TIMESTAMP = ErrorDetailDTO.create_error_detail(
        code="INVALID_TIMESTAMP",
        message_en="Invalid timestamp format",
        message_fa="فرمت زمان نامعتبر است",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )

    TIMEZONE_ERROR = ErrorDetailDTO.create_error_detail(
        code="TIMEZONE_ERROR",
        message_en="Error in timezone conversion",
        message_fa="خطا در تبدیل منطقه زمانی",
        http_status=HTTPStatus.BAD_REQUEST if HTTP_AVAILABLE else None,
        grpc_status=StatusCode.INVALID_ARGUMENT if GRPC_AVAILABLE else None,
    )
