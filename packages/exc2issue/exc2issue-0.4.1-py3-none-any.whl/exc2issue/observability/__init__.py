"""Observability infrastructure for exc2issue.

This submodule provides observability capabilities including:
- Metrics collection with pluggable backends
- Future extensibility for tracing, logging, and monitoring integrations

The metrics system allows users to plug in their preferred metrics backend
(Prometheus, StatsD, DataDog, etc.) through a clean protocol interface.
"""

from exc2issue.observability.metrics_collector import (
    MetricsCollector,
    get_metrics_collector,
    set_metrics_collector,
)

__all__ = [
    "MetricsCollector",
    "set_metrics_collector",
    "get_metrics_collector",
]
