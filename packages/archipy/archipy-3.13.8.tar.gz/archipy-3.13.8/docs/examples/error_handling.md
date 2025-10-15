# Error Handling Examples

This document provides examples of how to use the error handling system in different scenarios.

## Basic Error Handling

```python
from archipy.models.errors import (
    NotFoundError,
    InvalidArgumentError,
    PermissionDeniedError
)
from archipy.models.types.language_type import LanguageType

def get_user(user_id: str):
    try:
        # Attempt to fetch user
        user = user_repository.find_by_id(user_id)
        if not user:
            raise NotFoundError(
                resource_type="user",
                error_details=f"User with ID {user_id} not found",
                lang=LanguageType.EN
            )
        return user
    except NotFoundError as e:
        # Log the error
        logger.error(f"User not found: {e.to_dict()}")
        # Re-raise or handle as needed
        raise

def update_user_permissions(user_id: str, permissions: list[str]):
    try:
        # Validate input
        if not isinstance(permissions, list):
            raise InvalidArgumentError(
                argument="permissions",
                error_details="Permissions must be a list",
                lang=LanguageType.EN
            )

        # Check permissions
        if not has_admin_access():
            raise PermissionDeniedError(
                operation="update_permissions",
                error_details="Admin access required",
                lang=LanguageType.EN
            )

        # Update permissions
        user_repository.update_permissions(user_id, permissions)
    except (InvalidArgumentError, PermissionDeniedError) as e:
        logger.error(f"Failed to update permissions: {e.to_dict()}")
        raise
```

## Business Logic Error Handling

```python
from archipy.models.errors import (
    InsufficientFundsError,
    BusinessRuleViolationError,
    InvalidStateError
)

def process_transaction(account_id: str, amount: float):
    try:
        # Check account state
        account = account_repository.find_by_id(account_id)
        if not account.is_active:
            raise InvalidStateError(
                current_state="inactive",
                expected_state="active",
                error_details="Account must be active for transactions"
            )

        # Check balance
        if account.balance < amount:
            raise InsufficientFundsError(
                error_details=f"Required amount: {amount}, Available: {account.balance}"
            )

        # Check business rules
        if amount > account.transaction_limit:
            raise BusinessRuleViolationError(
                rule="transaction_limit",
                details=f"Amount exceeds limit of {account.transaction_limit}"
            )

        # Process transaction
        account_repository.process_transaction(account_id, amount)
    except (InsufficientFundsError, BusinessRuleViolationError, InvalidStateError) as e:
        logger.error(f"Transaction failed: {e.to_dict()}")
        raise
```

## System Error Handling

```python
from archipy.models.errors import (
    DatabaseConnectionError,
    DeadlockDetectedError,
    ResourceExhaustedError
)
from typing import Any

def execute_with_retry(operation: callable, max_retries: int = 3) -> Any:
    retries = 0
    while retries < max_retries:
        try:
            return operation()
        except DeadlockDetectedError as e:
            retries += 1
            if retries == max_retries:
                logger.error(f"Max retries exceeded: {e.to_dict()}")
                raise
            logger.warning(f"Deadlock detected, retrying ({retries}/{max_retries})")
            time.sleep(1)  # Wait before retry
        except DatabaseConnectionError as e:
            logger.error(f"Database connection failed: {e.to_dict()}")
            raise  # Don't retry connection errors
        except ResourceExhaustedError as e:
            logger.error(f"Resource exhausted: {e.to_dict()}")
            raise  # Don't retry resource exhaustion

# Usage example
def process_batch(items: list[dict]):
    def batch_operation():
        return database.batch_insert(items)

    try:
        return execute_with_retry(batch_operation)
    except (DeadlockDetectedError, DatabaseConnectionError, ResourceExhaustedError) as e:
        # Handle final failure
        return {"error": e.to_dict()}
```

## Error Response Formatting

```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from archipy.models.errors import BaseError
from archipy.models.types.language_type import LanguageType
from datetime import datetime

def handle_error(error: BaseError) -> dict:
    """Convert error to API response format."""
    error_dict = error.to_dict()
    return {
        "status": "error",
        "error": error_dict,
        "timestamp": datetime.utcnow().isoformat()
    }

# FastAPI error handler
@app.exception_handler(BaseError)
async def error_handler(request: Request, exc: BaseError):
    return JSONResponse(
        status_code=exc.http_status_code or 500,
        content=handle_error(exc)
    )

# Example usage in endpoint
@app.get("/users/{user_id}")
async def get_user(user_id: str):
    try:
        user = user_service.get_user(user_id)
        return {"status": "success", "data": user}
    except NotFoundError as e:
        # Let the exception handler handle it
        raise
```

## Error Logging and Monitoring

```python
from archipy.models.errors import (
    InternalError,
    UnknownError,
    ConfigurationError
)
import sentry_sdk

def log_error(error: BaseError, context: dict | None = None):
    """Log error with context and send to monitoring service."""
    error_dict = error.to_dict()

    # Add context if provided
    if context:
        error_dict["context"] = context

    # Log to application logger
    logger.error(
        f"Error occurred: {error_dict['error']}",
        extra={"error": error_dict}
    )

    # Send to monitoring service
    if isinstance(error, (InternalError, UnknownError, ConfigurationError)):
        sentry_sdk.capture_exception(error)

# Example usage
def process_request(request_data: dict):
    try:
        # Process request
        result = service.process(request_data)
        return result
    except BaseError as e:
        log_error(e, context={"request_data": request_data})
        raise
```

## Exception Chaining

```python
from archipy.models.errors import (
    DatabaseQueryError,
    InvalidEntityTypeError,
    BaseEntity
)

# Good - Preserving original error context
def fetch_entity(entity_type: type, entity_uuid: str) -> BaseEntity:
    try:
        result = session.get(entity_type, entity_uuid)
        if not result:
            raise NotFoundError(
                resource_type=entity_type.__name__,
                error_details=f"Entity with UUID {entity_uuid} not found"
            )
        return result
    except Exception as e:
        raise DatabaseQueryError() from e

# Good - Type validation with specific error
def validate_entity(entity: object) -> None:
    if not isinstance(entity, BaseEntity):
        raise InvalidEntityTypeError(
            message=f"Expected BaseEntity subclass, got {type(entity).__name__}",
            expected_type="BaseEntity",
            actual_type=type(entity).__name__
        )
```

## Error Recovery Strategies

```python
from archipy.models.errors import (
    CacheMissError,
    ServiceUnavailableError,
    ResourceExhaustedError
)

class ErrorRecovery:
    @staticmethod
    def handle_cache_miss(error: CacheMissError):
        """Handle cache miss by fetching from primary source."""
        try:
            # Fetch from database
            data = database.get(error.key)
            # Update cache
            cache.set(error.key, data)
            return data
        except Exception as e:
            logger.error(f"Failed to recover from cache miss: {str(e)}")
            raise  # Re-raise after logging

    @staticmethod
    def handle_service_unavailable(error: ServiceUnavailableError):
        """Handle service unavailability with fallback."""
        if error.service == "primary":
            try:
                # Try fallback service
                return fallback_service.get_data()
            except Exception as e:
                # Preserve error chain
                raise ServiceUnavailableError(
                    service="fallback",
                    error_details="Both primary and fallback services unavailable"
                ) from e
        raise

    @staticmethod
    def handle_resource_exhaustion(error: ResourceExhaustedError):
        """Handle resource exhaustion with cleanup."""
        if error.resource_type == "memory":
            # Perform cleanup
            gc.collect()
            try:
                # Retry operation
                return retry_operation()
            except Exception as e:
                # Preserve error chain
                raise ResourceExhaustedError(
                    resource_type="memory",
                    error_details="Resource exhaustion persisted after cleanup"
                ) from e
        raise

# Example usage
def get_data(key: str):
    try:
        return cache.get(key)
    except CacheMissError as e:
        return ErrorRecovery.handle_cache_miss(e)
    except ServiceUnavailableError as e:
        return ErrorRecovery.handle_service_unavailable(e)
    except ResourceExhaustedError as e:
        return ErrorRecovery.handle_resource_exhaustion(e)
```
