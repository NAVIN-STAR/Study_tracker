from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import database as db
from services.session_service import SessionService

router = APIRouter()
templates = Jinja2Templates(directory="templates")
session_service = SessionService()


@router.get("/sessions", response_class=HTMLResponse)
async def sessions_page(request: Request):
    sessions = session_service.get_all()
    courses = db.get_courses()
    return templates.TemplateResponse(
        "sessions.html",
        {
            "request": request,
            "sessions": sessions,
            "courses": courses,
        },
    )
