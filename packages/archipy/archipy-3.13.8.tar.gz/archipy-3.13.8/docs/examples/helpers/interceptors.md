# Interceptor Examples

This page demonstrates how to use ArchiPy's interceptors for cross-cutting concerns like logging, tracing, and error
handling.

## gRPC Interceptors

### Tracing Interceptor

The tracing interceptor adds request/response tracking to gRPC services:

```python
import grpc
from concurrent import futures
from typing import Any, Callable

from archipy.helpers.interceptors.grpc.trace import GrpcServerTraceInterceptor
from archipy.models.errors import InternalError


# Create a gRPC server with tracing
def create_grpc_server(max_workers: int = 10) -> grpc.Server:
    """Create a gRPC server with tracing interceptor.

    Args:
        max_workers: Maximum worker threads for the server

    Returns:
        Configured gRPC server instance
    """
    try:
        # Initialize the tracing interceptor
        trace_interceptor = GrpcServerTraceInterceptor()

        # Create the server with the interceptor
        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=max_workers),
            interceptors=[trace_interceptor]
        )
        return server
    except Exception as e:
        raise InternalError(error_details="Failed to create gRPC server") from e


# Usage
server = create_grpc_server()
# Add your services to the server
# my_service.add_to_server(server)
# server.add_insecure_port('[::]:50051')
# server.start()
```

## FastAPI Interceptors

### Request Logging

Log all incoming requests and responses:

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Awaitable, Callable

from archipy.helpers.interceptors.fastapi.logging import RequestLoggingMiddleware
from archipy.helpers.utils.app_utils import AppUtils
from archipy.configs.base_config import BaseConfig

# Create a FastAPI app with request logging
app = AppUtils.create_fastapi_app()

# Add the logging middleware
app.add_middleware(RequestLoggingMiddleware)


# Example endpoint
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

### Performance Monitoring

Monitor endpoint performance:

```python
from fastapi import FastAPI
from typing import Awaitable, Callable, Dict, Any

from archipy.helpers.interceptors.fastapi.performance import PerformanceMonitoringMiddleware
from archipy.helpers.utils.app_utils import AppUtils
from archipy.configs.base_config import BaseConfig

# Create a FastAPI app
app = AppUtils.create_fastapi_app()

# Add the performance monitoring middleware
app.add_middleware(PerformanceMonitoringMiddleware)


# Example endpoint
@app.get("/process")
async def process_data(query: str) -> Dict[str, Any]:
    # Some processing here
    return {"query": query, "result": "processed"}

# The middleware will log performance metrics for each request
# Example log: "Endpoint GET /process completed in 123.45ms"
```

## Using Multiple Interceptors

Combining multiple interceptors together:

```python
import grpc
from concurrent import futures
from fastapi import FastAPI

from archipy.helpers.interceptors.grpc.trace import GrpcServerTraceInterceptor
from archipy.helpers.interceptors.fastapi.logging import RequestLoggingMiddleware
from archipy.helpers.interceptors.fastapi.performance import PerformanceMonitoringMiddleware
from archipy.helpers.utils.app_utils import AppUtils


# Create a FastAPI app with multiple interceptors
def create_fastapi_app() -> FastAPI:
    app = AppUtils.create_fastapi_app()

    # Add middlewares in order (last added = first executed)
    app.add_middleware(PerformanceMonitoringMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    return app


# Create a gRPC server with the tracing interceptor
def create_grpc_server() -> grpc.Server:
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[GrpcServerTraceInterceptor()]
    )

    return server
```
