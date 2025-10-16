# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["EmailReplyParams"]


class EmailReplyParams(TypedDict, total=False):
    from_: Required[Annotated[str, PropertyInfo(alias="from")]]

    html: Required[str]

    bcc: Union[str, SequenceNotStr[str]]

    cc: Union[str, SequenceNotStr[str]]

    from_name: str

    is_draft: bool

    reply_all: bool

    subject: str

    text: str

    to: Union[str, SequenceNotStr[str]]
