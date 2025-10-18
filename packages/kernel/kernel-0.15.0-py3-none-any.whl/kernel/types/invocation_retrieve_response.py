# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["InvocationRetrieveResponse"]


class InvocationRetrieveResponse(BaseModel):
    id: str
    """ID of the invocation"""

    action_name: str
    """Name of the action invoked"""

    app_name: str
    """Name of the application"""

    started_at: datetime
    """RFC 3339 Nanoseconds timestamp when the invocation started"""

    status: Literal["queued", "running", "succeeded", "failed"]
    """Status of the invocation"""

    version: str
    """Version label for the application"""

    finished_at: Optional[datetime] = None
    """
    RFC 3339 Nanoseconds timestamp when the invocation finished (null if still
    running)
    """

    output: Optional[str] = None
    """Output produced by the action, rendered as a JSON string.

    This could be: string, number, boolean, array, object, or null.
    """

    payload: Optional[str] = None
    """Payload provided to the invocation.

    This is a string that can be parsed as JSON.
    """

    status_reason: Optional[str] = None
    """Status reason"""
