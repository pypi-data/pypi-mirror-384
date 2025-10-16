from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LearningSessionData(BaseModel):
    """Data transfer object for learning session storage."""
    
    team_id: Optional[int] = None
    agent_id: Optional[int] = None
    team_identifier: Optional[str] = None
    agent_identifier: Optional[str] = None
    session_id: str
    previous_memory: Optional[str] = None
    updated_memory: Optional[str] = None
    account_id: int
    has_changes: bool
    learning_summary: str
    confidence_score: Optional[float] = None