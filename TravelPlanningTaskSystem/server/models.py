from pydantic import BaseModel
from typing import Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "user_main"
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    status: str
    agenda: Optional[str] = None
    draft_contents: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
