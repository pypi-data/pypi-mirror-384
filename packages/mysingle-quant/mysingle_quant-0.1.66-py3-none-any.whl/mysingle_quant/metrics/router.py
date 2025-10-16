"""Metrics utilities and middleware."""

from fastapi import Response

from .collector import MetricsCollector, get_metrics_collector


def create_metrics_router():
    """Create router with metrics endpoints."""
    from fastapi import APIRouter, Depends

    router = APIRouter(prefix="/metrics", tags=["Metrics"])

    @router.get("/")
    async def get_metrics(
        collector: MetricsCollector = Depends(get_metrics_collector),  # noqa: B008
    ) -> dict:
        """Get service metrics."""
        return collector.get_metrics()

    @router.get("/prometheus")
    async def get_prometheus_metrics(
        collector: MetricsCollector = Depends(get_metrics_collector),  # noqa: B008
    ) -> Response:
        """Get metrics in Prometheus format."""
        metrics = collector.get_metrics()

        # Simple Prometheus format
        lines = [
            f'# HELP {metrics["service"]}_uptime_seconds Service uptime in seconds',
            f'# TYPE {metrics["service"]}_uptime_seconds gauge',
            f'{metrics["service"]}_uptime_seconds {metrics["uptime_seconds"]}',
            "",
            f'# HELP {metrics["service"]}_requests_total Total requests',
            f'# TYPE {metrics["service"]}_requests_total counter',
            f'{metrics["service"]}_requests_total {metrics["total_requests"]}',
            "",
            f'# HELP {metrics["service"]}_errors_total Total errors',
            f'# TYPE {metrics["service"]}_errors_total counter',
            f'{metrics["service"]}_errors_total {metrics["total_errors"]}',
            "",
        ]

        # Add per-route metrics
        for route, count in metrics["routes"]["request_count"].items():
            lines.extend(
                [
                    f'# HELP {metrics["service"]}_route_requests_total '
                    f"Total requests for route {route}",
                    f'# TYPE {metrics["service"]}_route_requests_total counter',
                    f'{metrics["service"]}_route_requests_total'
                    f'{{route="{route}"}} {count}',
                    "",
                ]
            )

        return Response(content="\n".join(lines), media_type="text/plain")

    return router
