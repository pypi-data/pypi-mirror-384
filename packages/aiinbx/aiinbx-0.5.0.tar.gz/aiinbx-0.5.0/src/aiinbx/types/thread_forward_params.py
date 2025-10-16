# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["ThreadForwardParams"]


class ThreadForwardParams(TypedDict, total=False):
    to: Required[Union[str, SequenceNotStr[str]]]

    bcc: Union[str, SequenceNotStr[str]]

    cc: Union[str, SequenceNotStr[str]]

    from_: Annotated[str, PropertyInfo(alias="from")]

    from_name: str

    include_attachments: Annotated[bool, PropertyInfo(alias="includeAttachments")]

    is_draft: bool

    note: str
