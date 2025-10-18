# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from ..._types import SequenceNotStr

__all__ = ["ComputerMoveMouseParams"]


class ComputerMoveMouseParams(TypedDict, total=False):
    x: Required[int]
    """X coordinate to move the cursor to"""

    y: Required[int]
    """Y coordinate to move the cursor to"""

    hold_keys: SequenceNotStr[str]
    """Modifier keys to hold during the move"""
