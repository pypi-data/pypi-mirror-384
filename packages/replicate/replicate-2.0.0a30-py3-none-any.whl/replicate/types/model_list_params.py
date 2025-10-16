# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["ModelListParams"]


class ModelListParams(TypedDict, total=False):
    sort_by: Literal["model_created_at", "latest_version_created_at"]
    """Field to sort models by. Defaults to `latest_version_created_at`."""

    sort_direction: Literal["asc", "desc"]
    """Sort direction. Defaults to `desc` (descending, newest first)."""
