from datetime import date
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import database as db
from services.checklist_service import ChecklistService
from services.session_service import SessionService

router = APIRouter()
templates = Jinja2Templates(directory="templates")
checklist_service = ChecklistService()
session_service = SessionService()

DAY_TYPES = [
    {"key": "wfh", "label": "WFH"},
    {"key": "office", "label": "Office"},
    {"key": "weekend", "label": "Weekend"},
]

TAG_COLORS = {
    "build": ("bg-pro", "text-pro"),
    "learn": ("bg-accent", "text-accent"),
    "resume": ("bg-warning", "text-warning"),
    "work": ("surface-0", "text-muted"),
}


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, day_type: str = "wfh", view_date: Optional[str] = None):
    today = date.today().isoformat()
    if view_date is None:
        view_date = today

    view_date_obj = date.fromisoformat(view_date)
    view_date_display = view_date_obj.strftime("%A, %d %b %Y")

    tasks = checklist_service.get_tasks(day_type)
    done_keys = checklist_service.get_done(view_date)
    viewed_sessions = session_service.get_for_date(view_date)
    stats = db.get_stats()
    courses = db.get_courses()
    streak_dates = db.get_streak_data()
    logged_keys = [session["task_key"] for session in viewed_sessions if session.get("task_key")]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "today": today,
            "view_date": view_date,
            "view_date_display": view_date_display,
            "day_type": day_type,
            "tasks": tasks,
            "done_keys": done_keys,
            "logged_keys": logged_keys,
            "viewed_sessions": viewed_sessions,
            "stats": stats,
            "courses": courses,
            "streak_dates": streak_dates,
            "tag_colors": TAG_COLORS,
            "day_types": DAY_TYPES,
        },
    )


@router.post("/session/add")
async def add_session(
    request: Request,
    topic: str = Form(...),
    course: str = Form(...),
    duration_mins: int = Form(...),
    day_type: str = Form(...),
    session_date: str = Form(...),
    notes: str = Form(""),
):
    session_service.add_session(
        {
            "date": session_date,
            "topic": topic,
            "course": course,
            "duration_mins": duration_mins,
            "day_type": day_type,
            "notes": notes,
        }
    )
    return RedirectResponse(url=f"/?day_type={day_type}&view_date={session_date}", status_code=303)


@router.delete("/session/{session_id}")
async def delete_session(session_id: int):
    session_service.delete_session(session_id)
    return JSONResponse({"ok": True})


@router.post("/course/update")
async def update_course(request: Request):
    data = await request.json()
    db.update_course_progress(data["id"], data["progress"])
    return JSONResponse({"ok": True})
