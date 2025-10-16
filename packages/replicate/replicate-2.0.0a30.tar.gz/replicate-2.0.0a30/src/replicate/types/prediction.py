# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import TYPE_CHECKING, Dict, Union, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Prediction", "URLs", "Metrics"]


class URLs(BaseModel):
    cancel: str
    """Cancel the prediction via API"""

    get: str
    """Retrieve the latest state of the prediction via API"""

    web: str
    """View the prediction in a browser"""

    stream: Optional[str] = None
    """An event source to stream the output of the prediction via API"""


class Metrics(BaseModel):
    total_time: Optional[float] = None
    """The total time, in seconds, that the prediction took to complete"""

    if TYPE_CHECKING:
        # Some versions of Pydantic <2.8.0 have a bug and don’t allow assigning a
        # value to this field, so for compatibility we avoid doing it at runtime.
        __pydantic_extra__: Dict[str, object] = FieldInfo(init=False)  # pyright: ignore[reportIncompatibleVariableOverride]

        # Stub to indicate that arbitrary properties are accepted.
        # To access properties that are not valid identifiers you can use `getattr`, e.g.
        # `getattr(obj, '$type')`
        def __getattr__(self, attr: str) -> object: ...
    else:
        __pydantic_extra__: Dict[str, object]


class Prediction(BaseModel):
    id: str

    created_at: datetime
    """The time that the prediction was created"""

    data_removed: bool
    """Whether the prediction output has been deleted"""

    error: Optional[str] = None
    """An error string if the model status is `"failed"`"""

    input: Dict[str, object]
    """The prediction input"""

    model: str
    """The name of the model that created the prediction"""

    output: object
    """
    The prediction output, which can be any JSON-serializable value, depending on
    the model
    """

    status: Literal["starting", "processing", "succeeded", "failed", "canceled"]

    urls: URLs
    """URLs for working with the prediction"""

    version: Union[str, Literal["hidden"]]
    """The ID of the model version that created the prediction"""

    completed_at: Optional[datetime] = None
    """The time that the model completed the prediction and all outputs were uploaded"""

    deadline: Optional[datetime] = None
    """
    The absolute time at which the prediction will be automatically canceled if it
    has not completed
    """

    deployment: Optional[str] = None
    """The name of the deployment that created the prediction"""

    logs: Optional[str] = None
    """The log output from the model"""

    metrics: Optional[Metrics] = None
    """Additional metrics associated with the prediction"""

    started_at: Optional[datetime] = None
    """The time that the model began the prediction"""
