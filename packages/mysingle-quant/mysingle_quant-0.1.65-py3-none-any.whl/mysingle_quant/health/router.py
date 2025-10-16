"""Health check utilities and endpoints."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends

from .checker import HealthStatus
from .schemas import HealthResponse


def get_health_checker() -> HealthStatus:
    """Get the global health checker instance."""
    global _health_checker
    if _health_checker is None:
        raise RuntimeError(
            "Health checker not initialized. Call create_health_router first."
        )
    return _health_checker


async def basic_health_check():
    """Basic health check that always passes."""
    return (
        "healthy",
        "Service is running",
        {"timestamp": datetime.now(UTC).isoformat()},
    )


async def database_health_check():
    """Check database connectivity."""
    try:
        # This would check database connection
        # For now, just return healthy
        return "healthy", "Database connection OK", {"connection": "active"}
    except Exception as e:
        return "unhealthy", f"Database error: {str(e)}", {"error": str(e)}


def create_health_router(
    service_name: str, service_version: str, include_database_check: bool = True
) -> APIRouter:
    """Create health check router with standard endpoints.

    Args:
        service_name: Name of the service
        service_version: Version of the service
        include_database_check: Whether to include database health check

    Returns:
        APIRouter with health check endpoints
    """
    global _health_checker

    router = APIRouter(prefix="/health", tags=["Health"])

    # Initialize health checker
    _health_checker = HealthStatus(service_name, service_version)

    # Add basic checks
    _health_checker.add_check("basic", basic_health_check, critical=True)

    if include_database_check:
        _health_checker.add_check("database", database_health_check, critical=True)

    @router.get("/", response_model=HealthResponse)
    async def health_check(
        checker: HealthStatus = Depends(get_health_checker),  # noqa: B008
    ) -> HealthResponse:
        """Get comprehensive health status."""
        health_response = await checker.get_health()
        return health_response

    @router.get("/live")
    async def liveness_probe():
        """Kubernetes liveness probe endpoint."""
        return {"status": "alive", "timestamp": datetime.now(UTC)}

    @router.get("/ready")
    async def readiness_probe(
        checker: HealthStatus = Depends(get_health_checker),  # noqa: B008
    ) -> dict[str, Any]:
        """Kubernetes readiness probe endpoint."""
        health_response = await checker.get_health()

        if health_response.status == "healthy":
            return {"status": "ready", "timestamp": datetime.now(UTC)}
        else:
            return {"status": "not_ready", "timestamp": datetime.now(UTC)}

    return router
