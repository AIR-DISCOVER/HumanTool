from pydantic import BaseModel
from typing import Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "user_main"
    session_id: Optional[str] = None
    stream: Optional[bool] = True

class ChatResponse(BaseModel):
    response: str
    status: str
    session_id: str
    agenda: Optional[str] = None
    draft_contents: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None

class DraftUpdateRequest(BaseModel):
    session_id: str
    draft_id: str
    content: str

class HealthResponse(BaseModel):
    status: str
    agent_available: bool
    active_sessions: int
    timestamp: float

class ExportResponse(BaseModel):
    session_id: str
    export_content: str
    exported_at: float
