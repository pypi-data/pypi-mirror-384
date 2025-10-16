"""Metrics utilities and middleware."""

import time
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .router import MetricsCollector


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics."""

    def __init__(self, app: Any, collector: MetricsCollector) -> None:
        super().__init__(app)
        self.collector = collector

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Process request and collect metrics."""
        start_time = time.time()

        # Get route pattern if available
        route_path = request.url.path
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "path"):
                route_path = route.path

        # Process request
        response: Response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        self.collector.record_request(
            method=request.method,
            path=route_path,
            status_code=response.status_code,
            duration=duration,
        )

        # Add metrics headers
        response.headers["X-Response-Time"] = f"{duration:.4f}s"

        return response


def create_metrics_middleware(service_name: str) -> type:
    """Create metrics middleware for the given service.

    Args:
        service_name: Name of the service

    Returns:
        Middleware class configured for the service
    """
    global _metrics_collector

    # Initialize metrics collector
    _metrics_collector = MetricsCollector(service_name)

    # Create middleware class
    class ServiceMetricsMiddleware(MetricsMiddleware):
        def __init__(self, app):
            if _metrics_collector is None:
                raise RuntimeError("Metrics collector not initialized")
            super().__init__(app, _metrics_collector)

    return ServiceMetricsMiddleware
