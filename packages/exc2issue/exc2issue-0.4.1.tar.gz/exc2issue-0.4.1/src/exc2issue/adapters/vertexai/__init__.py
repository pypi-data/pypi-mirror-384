"""Vertex AI adapter for exc2issue.

This package provides integration with Google Cloud Vertex AI API for generating
intelligent GitHub issue descriptions from error records.
"""

from .client import VertexAIClient

__all__ = ["VertexAIClient"]
