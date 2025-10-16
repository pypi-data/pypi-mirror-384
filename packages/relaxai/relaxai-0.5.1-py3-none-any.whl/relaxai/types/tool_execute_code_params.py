# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from .._types import SequenceNotStr

__all__ = ["ToolExecuteCodeParams"]


class ToolExecuteCodeParams(TypedDict, total=False):
    code: Required[str]

    lang: Required[str]

    libraries: SequenceNotStr[str]
