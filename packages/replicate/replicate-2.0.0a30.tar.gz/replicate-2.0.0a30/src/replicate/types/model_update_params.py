# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["ModelUpdateParams"]


class ModelUpdateParams(TypedDict, total=False):
    model_owner: Required[str]

    model_name: Required[str]

    description: str
    """A description of the model."""

    github_url: str
    """A URL for the model's source code on GitHub."""

    license_url: str
    """A URL for the model's license."""

    paper_url: str
    """A URL for the model's paper."""

    readme: str
    """The README content of the model."""

    weights_url: str
    """A URL for the model's weights."""
