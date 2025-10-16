"""Metrics collection protocol and infrastructure for exc2issue.

This module provides a callback-based metrics system that allows users to plug in
their preferred metrics backend (Prometheus, StatsD, DataDog, etc.).

The library instruments the code but doesn't configure or expose metrics - that's
the responsibility of the library user.
"""

from typing import Protocol


class MetricsCollector(Protocol):
    """Interface that users implement for their metrics backend.

    This protocol defines the contract for metrics collection. Users implement
    this interface to integrate their preferred metrics system (Prometheus,
    StatsD, DataDog, etc.).
    """

    def record_duration(self, function_name: str, duration_seconds: float) -> None:
        """Record function execution duration.

        Args:
            function_name: Name of the function that was executed
            duration_seconds: Duration of execution in seconds
        """
        raise NotImplementedError

    def record_error(
        self, function_name: str, error_type: str, error: BaseException
    ) -> None:
        """Record error occurrence.

        Args:
            function_name: Name of the function where error occurred
            error_type: Type of the error (e.g., "ValueError", "RuntimeError", "SystemExit")
            error: The actual exception object (Exception or BaseException like SystemExit)
        """
        raise NotImplementedError

    def record_success(self, function_name: str) -> None:
        """Record successful execution (optional).

        Args:
            function_name: Name of the function that completed successfully
        """
        raise NotImplementedError


# Global registry for metrics collector
_metrics_state: dict[str, MetricsCollector | None] = {"collector": None}


def set_metrics_collector(collector: MetricsCollector | None) -> None:
    """Configure the metrics collector (called by library users).

    This function allows users to register their metrics collector implementation.
    Once registered, the library will automatically collect metrics during
    function execution.

    Args:
        collector: Implementation of MetricsCollector protocol or None to clear

    Example:
        >>> from exc2issue.observability import set_metrics_collector
        >>> from prometheus_client import Counter, Histogram
        >>>
        >>> class PrometheusCollector:
        ...     def __init__(self):
        ...         self.duration = Histogram('exc2issue_duration_seconds',
        ...                                   'Duration', ['function'])
        ...         self.errors = Counter('exc2issue_errors_total',
        ...                               'Errors', ['function', 'error_type'])
        ...
        ...     def record_duration(self, function_name, duration_seconds):
        ...         self.duration.labels(function=function_name).observe(duration_seconds)
        ...
        ...     def record_error(self, function_name, error_type, error):
        ...         self.errors.labels(function=function_name,
        ...                           error_type=error_type).inc()
        ...
        ...     def record_success(self, function_name):
        ...         pass  # Optional
        >>>
        >>> set_metrics_collector(PrometheusCollector())
    """
    _metrics_state["collector"] = collector


def get_metrics_collector() -> MetricsCollector | None:
    """Get current metrics collector.

    Returns:
        The currently registered metrics collector, or None if not configured
    """
    return _metrics_state["collector"]
