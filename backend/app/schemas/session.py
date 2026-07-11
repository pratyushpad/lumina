from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SessionCreate(BaseModel):
    name: Optional[str] = "New Session"


class SessionRename(BaseModel):
    name: str


class SessionResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    document_count: int = 0
    message_count: int = 0


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int
