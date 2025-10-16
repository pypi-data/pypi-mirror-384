"""Gemini AI adapter for exc2issue.

This package provides integration with Google's Gemini AI API for generating
intelligent GitHub issue descriptions from error records.
"""

from .client import GeminiClient

__all__ = ["GeminiClient"]
