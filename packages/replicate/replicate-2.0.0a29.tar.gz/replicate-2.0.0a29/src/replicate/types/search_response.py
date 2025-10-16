# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["SearchResponse", "Collection", "Model", "ModelMetadata", "ModelModel", "Page"]


class Collection(BaseModel):
    description: str
    """A description of the collection"""

    name: str
    """The name of the collection"""

    slug: str
    """The slug of the collection (lowercase with dashes)"""

    models: Optional[List[str]] = None
    """Array of model names in the collection"""


class ModelMetadata(BaseModel):
    generated_description: Optional[str] = None
    """AI-generated detailed description of the model"""

    score: Optional[float] = None
    """Search relevance score"""

    tags: Optional[List[str]] = None
    """Array of descriptive tags for the model"""


class ModelModel(BaseModel):
    cover_image_url: Optional[str] = None
    """A URL for the model's cover image"""

    default_example: Optional[object] = None
    """The model's default example prediction"""

    description: Optional[str] = None
    """A description of the model"""

    github_url: Optional[str] = None
    """A URL for the model's source code on GitHub"""

    is_official: Optional[bool] = None
    """Boolean indicating whether the model is officially maintained by Replicate.

    Official models are always on, have stable API interfaces, and predictable
    pricing.
    """

    latest_version: Optional[object] = None
    """The model's latest version"""

    license_url: Optional[str] = None
    """A URL for the model's license"""

    name: Optional[str] = None
    """The name of the model"""

    owner: Optional[str] = None
    """The name of the user or organization that owns the model"""

    paper_url: Optional[str] = None
    """A URL for the model's paper"""

    run_count: Optional[int] = None
    """The number of times the model has been run"""

    url: Optional[str] = None
    """The URL of the model on Replicate"""

    visibility: Optional[Literal["public", "private"]] = None
    """Whether the model is public or private"""


class Model(BaseModel):
    metadata: ModelMetadata

    model: ModelModel


class Page(BaseModel):
    href: str
    """URL path to the page"""

    name: str
    """Title of the page"""


class SearchResponse(BaseModel):
    collections: List[Collection]
    """Array of collections that match the search query"""

    models: List[Model]
    """
    Array of models that match the search query, each containing model data and
    extra metadata
    """

    pages: List[Page]
    """Array of Replicate documentation pages that match the search query"""

    query: str
    """The search term that was evaluated"""
