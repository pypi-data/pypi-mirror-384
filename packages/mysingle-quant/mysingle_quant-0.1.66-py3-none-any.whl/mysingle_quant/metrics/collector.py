"""Metrics utilities and middleware."""

import time
from collections import defaultdict, deque
from typing import Any


class MetricsCollector:
    """Simple in-memory metrics collector."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.request_count: defaultdict[str, int] = defaultdict(int)
        self.request_duration: defaultdict[str, deque[float]] = defaultdict(deque)
        self.error_count: defaultdict[str, int] = defaultdict(int)
        self.start_time = time.time()

    def record_request(
        self, method: str, path: str, status_code: int, duration: float
    ) -> None:
        """Record a request metric."""
        route_key = f"{method}:{path}"

        # Count requests
        self.request_count[route_key] += 1

        # Store duration (keep last 1000 requests)
        self.request_duration[route_key].append(duration)
        if len(self.request_duration[route_key]) > 1000:
            self.request_duration[route_key].popleft()

        # Count errors (4xx and 5xx)
        if status_code >= 400:
            self.error_count[route_key] += 1

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics summary."""
        total_requests = sum(self.request_count.values())
        total_errors = sum(self.error_count.values())
        uptime = time.time() - self.start_time

        # Calculate average response times
        avg_response_times = {}
        for route, durations in self.request_duration.items():
            if durations:
                avg_response_times[route] = sum(durations) / len(durations)

        return {
            "service": self.service_name,
            "uptime_seconds": uptime,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "requests_per_second": total_requests / uptime if uptime > 0 else 0,
            "routes": {
                "request_count": dict(self.request_count),
                "error_count": dict(self.error_count),
                "avg_response_time": avg_response_times,
            },
        }


# Global metrics collector
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        raise RuntimeError("Metrics collector not initialized.")
    return _metrics_collector
