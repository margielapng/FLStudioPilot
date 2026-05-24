from pydantic import BaseModel
from typing import Any, Optional


class CommandRequest(BaseModel):
    text: str


class CommandResponse(BaseModel):
    success: bool
    action: Optional[str] = None
    params: Optional[dict[str, Any]] = None
    message: str
    fl_result: Optional[str] = None


class FLStatus(BaseModel):
    connected: bool
    fl_version: Optional[str] = None
    project_name: Optional[str] = None
    bpm: Optional[float] = None
    playing: Optional[bool] = None
