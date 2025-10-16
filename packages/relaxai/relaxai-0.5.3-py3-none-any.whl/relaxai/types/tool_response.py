# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel

__all__ = ["ToolResponse", "Plot"]


class Plot(BaseModel):
    content_base64: str

    filename: str

    format: str


class ToolResponse(BaseModel):
    execution_time: float

    exit_code: int

    security_checked: bool

    stderr: str

    stdout: str

    success: bool

    plots: Optional[List[Plot]] = None

    violations: Optional[List[str]] = None
