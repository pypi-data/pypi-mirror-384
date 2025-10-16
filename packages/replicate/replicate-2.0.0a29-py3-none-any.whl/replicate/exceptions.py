"""
Legacy compatibility module for exception imports.

This module provides backward compatibility for users importing exceptions
from `replicate.exceptions` instead of directly from `replicate`.

All exceptions are also available directly from the `replicate` module.
"""

from __future__ import annotations

# Import all exceptions from the internal module
from ._exceptions import (
    APIError,
    ModelError,
    ConflictError,
    NotFoundError,
    APIStatusError,
    RateLimitError,
    ReplicateError,
    APITimeoutError,
    BadRequestError,
    APIConnectionError,
    AuthenticationError,
    InternalServerError,
    PermissionDeniedError,
    UnprocessableEntityError,
    APIResponseValidationError,
)

__all__ = [
    "APIConnectionError",
    "APIError",
    "APIResponseValidationError",
    "APIStatusError",
    "APITimeoutError",
    "AuthenticationError",
    "BadRequestError",
    "ConflictError",
    "InternalServerError",
    "ModelError",
    "NotFoundError",
    "PermissionDeniedError",
    "RateLimitError",
    "ReplicateError",
    "UnprocessableEntityError",
]
