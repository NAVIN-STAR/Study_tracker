from typing import Optional
from pydantic import BaseModel


class ChecklistTaskCreate(BaseModel):
    day_type: str
    task_key: str
    label: str
    desc: str = ""
    time: str = ""
    course: str = ""
    duration_minutes: int = 0
    tag: str = ""
    notes: str = ""


class ChecklistTaskUpdate(ChecklistTaskCreate):
    id: int


class ChecklistTaskResponse(BaseModel):
    id: int
    day_type: str
    task_key: str
    key: str
    label: str
    desc: str
    time: str
    course: str
    duration_minutes: int
    tag: str
    notes: str
