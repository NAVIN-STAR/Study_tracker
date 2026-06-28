from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import date
import database as db

app = FastAPI(title="Study Tracker")
templates = Jinja2Templates(directory="templates")

db.init_db()

WFH_TASKS = [
    {"key": "wfh_deep1", "time": "1:00–2:30", "label": "Deep work block 1", "tag": "build", "desc": "Project or FastAPI course"},
    {"key": "wfh_deep2", "time": "3:00–4:30", "label": "Deep work block 2", "tag": "learn", "desc": "LLD / Azure AI / RAG course"},
    {"key": "wfh_study3", "time": "5:00–6:00", "label": "Study block 3", "tag": "learn", "desc": "Remaining course module"},
    {"key": "wfh_resume", "time": "7:00–8:30", "label": "Resume or light review", "tag": "resume", "desc": "2–3 bullet rewrites or re-read notes"},
    {"key": "wfh_night", "time": "9:30–11:00", "label": "Post-shift build session", "tag": "build", "desc": "Multi-agent project — no interruptions"},
    {"key": "wfh_review", "time": "11:00–11:30", "label": "Light review or log", "tag": "learn", "desc": "Re-read one topic, update tracker"},
]

OFFICE_TASKS = [
    {"key": "off_precommute", "time": "12:00–1:30", "label": "Study before commute", "tag": "learn", "desc": "Azure AI or RAG — 1–2 videos"},
    {"key": "off_commute", "time": "commute", "label": "Passive learning on commute", "tag": "learn", "desc": "Podcast or LLD video on phone"},
    {"key": "off_night1", "time": "8:30–9:30", "label": "LLD or Resume", "tag": "learn", "desc": "One pattern or one resume section"},
    {"key": "off_night2", "time": "9:30–10:30", "label": "Small project task", "tag": "build", "desc": "Fix a bug, write one function"},
]

TAG_COLORS = {
    "build": ("bg-pro", "text-pro"),
    "learn": ("bg-accent", "text-accent"),
    "resume": ("bg-warning", "text-warning"),
    "work": ("surface-0", "text-muted"),
}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, day_type: str = "wfh", view_date: str = None):
    today = date.today().isoformat()
    if view_date is None:
        view_date = today
    
    # Parse view_date to get display string
    view_date_obj = date.fromisoformat(view_date)
    view_date_display = view_date_obj.strftime("%A, %d %b %Y")
    
    tasks = WFH_TASKS if day_type == "wfh" else OFFICE_TASKS
    done_keys = db.get_checklist_done(view_date)
    viewed_sessions = db.get_sessions_for_date(view_date)
    stats = db.get_stats()
    courses = db.get_courses()
    streak_dates = db.get_streak_data()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "today": today,
        "view_date": view_date,
        "view_date_display": view_date_display,
        "day_type": day_type,
        "tasks": tasks,
        "done_keys": done_keys,
        "viewed_sessions": viewed_sessions,
        "stats": stats,
        "courses": courses,
        "streak_dates": streak_dates,
        "tag_colors": TAG_COLORS,
    })


@app.post("/checklist/toggle")
async def toggle_checklist(request: Request):
    data = await request.json()
    done = db.toggle_checklist(data["date"], data["task_key"])
    return JSONResponse({"done": done})


@app.post("/session/add")
async def add_session(
    request: Request,
    topic: str = Form(...),
    course: str = Form(...),
    duration_mins: int = Form(...),
    day_type: str = Form(...),
    session_date: str = Form(...),
    notes: str = Form(""),
):
    db.add_session(session_date, topic, course, duration_mins, day_type, notes)
    return RedirectResponse(url=f"/?day_type={day_type}", status_code=303)


@app.post("/course/update")
async def update_course(request: Request):
    data = await request.json()
    db.update_course_progress(data["id"], data["progress"])
    return JSONResponse({"ok": True})


@app.delete("/session/{session_id}")
async def delete_session(session_id: int):
    conn = db.get_conn()
    conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()
    return JSONResponse({"ok": True})


@app.get("/sessions", response_class=HTMLResponse)
async def sessions_page(request: Request):
    sessions = db.get_sessions(limit=50)
    courses = db.get_courses()
    return templates.TemplateResponse("sessions.html", {
        "request": request,
        "sessions": sessions,
        "courses": courses,
    })
