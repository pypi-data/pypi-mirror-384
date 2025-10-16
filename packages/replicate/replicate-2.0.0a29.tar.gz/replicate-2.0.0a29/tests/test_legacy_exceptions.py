"""Tests for legacy exception import compatibility."""

from __future__ import annotations


def test_legacy_exception_imports():
    """Test that exceptions can be imported from replicate.exceptions."""
    # Test importing individual exceptions from replicate.exceptions
    # All imports are intentionally kept to test that they can be imported
    # Test that imported exceptions are the same as the ones from replicate
    import replicate
    from replicate.exceptions import (
        APIError,
        ModelError,
        ConflictError,  # noqa: F401 # pyright: ignore[reportUnusedImport]
        NotFoundError,
        APIStatusError,  # noqa: F401 # pyright: ignore[reportUnusedImport]
        RateLimitError,
        ReplicateError,
        APITimeoutError,
        BadRequestError,
        APIConnectionError,
        AuthenticationError,
        InternalServerError,
        PermissionDeniedError,  # noqa: F401 # pyright: ignore[reportUnusedImport]
        UnprocessableEntityError,  # noqa: F401 # pyright: ignore[reportUnusedImport]
        APIResponseValidationError,  # noqa: F401 # pyright: ignore[reportUnusedImport]
    )

    assert ModelError is replicate._exceptions.ModelError
    assert APIError is replicate.APIError
    assert ReplicateError is replicate.ReplicateError
    assert BadRequestError is replicate.BadRequestError
    assert AuthenticationError is replicate.AuthenticationError
    assert NotFoundError is replicate.NotFoundError
    assert RateLimitError is replicate.RateLimitError
    assert InternalServerError is replicate.InternalServerError
    assert APIConnectionError is replicate.APIConnectionError
    assert APITimeoutError is replicate.APITimeoutError


def test_readme_example_import():
    """Test that the import pattern shown in README works correctly."""
    # This is the exact import pattern shown in the README
    import replicate
    from replicate.exceptions import ModelError

    # Verify ModelError is the correct class
    assert ModelError is replicate._exceptions.ModelError


def test_exception_module_all_exports():
    """Test that replicate.exceptions.__all__ contains all expected exceptions."""
    import replicate.exceptions

    expected_exceptions = [
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

    assert set(replicate.exceptions.__all__) == set(expected_exceptions)

    # Also verify they can all be accessed
    for exc_name in expected_exceptions:
        assert hasattr(replicate.exceptions, exc_name)
