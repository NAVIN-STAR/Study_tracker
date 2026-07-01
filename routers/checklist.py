from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import database as db
from services.checklist_service import ChecklistService
from services.session_service import SessionService

router = APIRouter(prefix="/checklist", tags=["checklist"])
checklist_service = ChecklistService()
session_service = SessionService()


class ChecklistTaskEntry(BaseModel):
    day_type: str
    label: str
    desc: str
    time: str
    course: str
    duration_minutes: int
    tag: str
    notes: Optional[str] = ""
    task_key: Optional[str] = None
    id: Optional[int] = None


class SessionLogEntry(BaseModel):
    task_key: str
    topic: str
    course: str
    duration_mins: int
    notes: Optional[str] = ""


class ChecklistLogPayload(BaseModel):
    date: str
    day_type: str
    sessions: List[SessionLogEntry]


@router.get("/tasks")
async def get_checklist_tasks(day_type: str):
    return JSONResponse({"tasks": checklist_service.get_tasks(day_type)})


@router.post("/task/add")
async def add_checklist_task(payload: ChecklistTaskEntry):
    if not payload.course or not payload.course.strip():
        raise HTTPException(status_code=400, detail="course is required")
    course_name = payload.course.strip()
    db.add_course(course_name)
    task = checklist_service.create_task(
        {
            "day_type": payload.day_type,
            "label": payload.label,
            "desc": payload.desc,
            "time": payload.time,
            "course": course_name,
            "duration_minutes": payload.duration_minutes,
            "tag": payload.tag,
            "notes": payload.notes or "",
            "task_key": payload.task_key,
        }
    )
    return JSONResponse({"ok": True, "task": task, "course": course_name})


@router.post("/task/edit")
async def edit_checklist_task(payload: ChecklistTaskEntry):
    if payload.id is None:
        raise HTTPException(status_code=400, detail="task id is required")
    task = checklist_service.update_task(
        payload.id,
        {
            "day_type": payload.day_type,
            "task_key": payload.task_key or "",
            "label": payload.label,
            "desc": payload.desc,
            "time": payload.time,
            "course": payload.course,
            "duration_minutes": payload.duration_minutes,
            "tag": payload.tag,
            "notes": payload.notes or "",
        },
    )
    return JSONResponse({"ok": True, "task": task})


@router.delete("/task/{task_id}")
async def delete_checklist_task(task_id: int):
    checklist_service.delete_task(task_id)
    return JSONResponse({"ok": True})


@router.post("/toggle")
async def toggle_checklist(request: Request):
    data = await request.json()
    task_key = data.get("task_key")
    date_str = data.get("date")

    if not task_key or not date_str:
        raise HTTPException(status_code=400, detail="task_key and date are required")

    done, locked = checklist_service.toggle_task(date_str, task_key)
    return JSONResponse({"done": done, "locked": locked})


@router.post("/log")
async def log_checklist_sessions(payload: ChecklistLogPayload):
    added_count = 0
    skipped_count = 0

    for session in payload.sessions:
        if db.has_task_been_logged(payload.date, session.task_key):
            skipped_count += 1
        else:
            session_service.add_session(
                {
                    "date": payload.date,
                    "topic": session.topic,
                    "course": session.course,
                    "duration_mins": session.duration_mins,
                    "day_type": payload.day_type,
                    "notes": session.notes,
                    "task_key": session.task_key,
                }
            )
            added_count += 1

    stats = db.get_stats()
    viewed_sessions = db.get_sessions_for_date(payload.date)
    streak_dates = db.get_streak_data()
    logged_task_keys = [session["task_key"] for session in viewed_sessions if session.get("task_key")]

    return JSONResponse(
        {
            "added": added_count,
            "skipped": skipped_count,
            "stats": stats,
            "viewed_sessions": viewed_sessions,
            "logged_task_keys": logged_task_keys,
            "streak_dates": streak_dates,
        }
    )
