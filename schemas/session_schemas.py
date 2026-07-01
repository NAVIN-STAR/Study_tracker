from typing import Optional
from pydantic import BaseModel


class SessionCreate(BaseModel):
    date: str
    topic: str
    course: str
    duration_mins: int
    day_type: str
    notes: str = ""
    task_key: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    date: str
    topic: str
    course: str
    duration_mins: int
    day_type: str
    notes: str
    task_key: Optional[str] = None
