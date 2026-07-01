import sqlite3
import secrets
from datetime import date

DB_PATH = "study.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            topic TEXT NOT NULL,
            course TEXT NOT NULL,
            duration_mins INTEGER NOT NULL,
            day_type TEXT NOT NULL,
            notes TEXT,
            task_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Ensure task_key column exists (migration for existing databases)
    try:
        c.execute("ALTER TABLE sessions ADD COLUMN task_key TEXT")
    except sqlite3.OperationalError:
        pass

    c.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            progress INTEGER DEFAULT 0,
            color TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS checklist_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            task_key TEXT NOT NULL,
            UNIQUE(date, task_key)
        )
    """)

    # Seed courses if empty
    courses = [
        ("FastAPI Course", 50, "#378ADD"),
        ("Azure AI (AI-102)", 20, "#534AB7"),
        ("RAG Applications", 26, "#1D9E75"),
        ("LLD Course", 18, "#D85A30"),
        ("Multi-agent Project", 10, "#BA7517"),
        ("Resume", 60, "#993556"),
    ]
    for name, pct, color in courses:
        c.execute("INSERT OR IGNORE INTO courses (name, progress, color) VALUES (?,?,?)", (name, pct, color))

    # Create checklist_tasks table
    c.execute("""
        CREATE TABLE IF NOT EXISTS checklist_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_type TEXT NOT NULL,
            task_key TEXT UNIQUE NOT NULL,
            label TEXT NOT NULL,
            desc TEXT NOT NULL,
            time TEXT NOT NULL,
            course TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            tag TEXT NOT NULL,
            notes TEXT
        )
    """)

    # Seed checklist_tasks if empty
    db_tasks = c.execute("SELECT COUNT(*) as c FROM checklist_tasks").fetchone()["c"]
    if db_tasks == 0:
        initial_tasks = [
            # WFH
            ("wfh", "wfh_deep1", "Deep work block 1", "Project or FastAPI course", "1:00–2:30", "Multi-agent Project", 90, "build", "Deep work block 1 focusing on multi-agent project."),
            ("wfh", "wfh_deep2", "Deep work block 2", "LLD / Azure AI / RAG course", "3:00–4:30", "LLD Course", 90, "learn", "Deep work block 2 focusing on LLD patterns."),
            ("wfh", "wfh_study3", "Study block 3", "Remaining course module", "5:00–6:00", "RAG Applications", 60, "learn", "Study block 3 focusing on RAG applications."),
            ("wfh", "wfh_resume", "Resume or light review", "2–3 bullet rewrites or re-read notes", "7:00–8:30", "Resume", 90, "resume", "Resume tuning and bullet rewrites."),
            ("wfh", "wfh_night", "Post-shift build session", "Multi-agent project — no interruptions", "9:30–11:00", "Multi-agent Project", 90, "build", "Late night multi-agent project coding session."),
            ("wfh", "wfh_review", "Light review or log", "Re-read one topic, update tracker", "11:00–11:30", "LLD Course", 30, "learn", "Review and update tracker."),
            # Office
            ("office", "off_precommute", "Study before commute", "Azure AI or RAG — 1–2 videos", "12:00–1:30", "Azure AI (AI-102)", 90, "learn", "Pre-commute study on Azure AI."),
            ("office", "off_commute", "Passive learning on commute", "Podcast or LLD video on phone", "commute", "Azure AI (AI-102)", 60, "learn", "Passive audio or video learning during commute."),
            ("office", "off_night1", "LLD or Resume", "One pattern or one resume section", "8:30–9:30", "LLD Course", 60, "learn", "Evening study of LLD pattern or resume section."),
            ("office", "off_night2", "Small project task", "Fix a bug, write one function", "9:30–10:30", "Multi-agent Project", 60, "build", "Focused bug fix or feature implementation."),
            # Weekend
            ("weekend", "week_morning", "Weekend morning build", "Deep programming and project build", "10:00–12:00", "Multi-agent Project", 120, "build", "Deep weekend morning coding block."),
            ("weekend", "week_afternoon", "Weekend afternoon RAG", "Build RAG search & indexing features", "2:00–4:00", "RAG Applications", 120, "learn", "Afternoon learning and building RAG applications."),
            ("weekend", "week_evening", "Weekend system design", "Practice LLD design patterns", "5:00–6:30", "LLD Course", 90, "learn", "Practice low level design patterns."),
            ("weekend", "week_review", "Weekend recap & plan", "Resume updates & next week prep", "9:30–10:30", "Resume", 60, "resume", "Recap current week and plan the next.")
        ]
        for dt, key, label, desc, t_time, course, mins, tag, notes in initial_tasks:
            c.execute("""
                INSERT OR IGNORE INTO checklist_tasks (day_type, task_key, label, desc, time, course, duration_minutes, tag, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (dt, key, label, desc, t_time, course, mins, tag, notes))

    conn.commit()
    conn.close()

def _generate_task_key(day_type: str) -> str:
    prefix = (day_type or "task").replace(" ", "_").lower()[:8]
    return f"{prefix}_{secrets.token_hex(3).lower()}"


def add_course(name: str, progress: int = 0, color: str = None):
    name = (name or "").strip()
    if not name:
        return None
    conn = get_conn()
    existing = conn.execute("SELECT * FROM courses WHERE name=?", (name,)).fetchone()
    if existing:
        conn.close()
        return dict(existing)
    if not color:
        color = "#378ADD"
    cursor = conn.execute(
        "INSERT INTO courses (name, progress, color) VALUES (?,?,?)",
        (name, progress, color),
    )
    conn.commit()
    conn.close()
    return {"id": cursor.lastrowid, "name": name, "progress": progress, "color": color}


def get_courses():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM courses ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_course_progress(course_id: int, progress: int):
    conn = get_conn()
    conn.execute("UPDATE courses SET progress=? WHERE id=?", (progress, course_id))
    conn.commit()
    conn.close()

def add_session(date_str, topic, course, duration_mins, day_type, notes, task_key=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO sessions (date, topic, course, duration_mins, day_type, notes, task_key) VALUES (?,?,?,?,?,?,?)",
        (date_str, topic, course, duration_mins, day_type, notes, task_key)
    )
    conn.commit()
    conn.close()

def has_task_been_logged(date_str, task_key):
    if not task_key:
        return False
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM sessions WHERE date=? AND task_key=?", (date_str, task_key)
    ).fetchone()
    conn.close()
    return row is not None

def get_sessions(limit=30):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM sessions ORDER BY date DESC, created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_streak_data():
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT date FROM sessions ORDER BY date DESC LIMIT 60"
    ).fetchall()
    conn.close()
    return [r["date"] for r in rows]

def get_today_sessions():
    today = date.today().isoformat()
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM sessions WHERE date=? ORDER BY created_at DESC", (today,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_sessions_for_date(date_str):
    """Get all sessions for a specific date"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM sessions WHERE date=? ORDER BY created_at DESC", (date_str,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def toggle_checklist(date_str, task_key):
    conn = get_conn()
    existing = conn.execute(
        "SELECT id FROM checklist_completions WHERE date=? AND task_key=?",
        (date_str, task_key)
    ).fetchone()
    if existing:
        conn.execute("DELETE FROM checklist_completions WHERE date=? AND task_key=?", (date_str, task_key))
        done = False
    else:
        conn.execute("INSERT INTO checklist_completions (date, task_key) VALUES (?,?)", (date_str, task_key))
        done = True
    conn.commit()
    conn.close()
    return done

def get_checklist_done(date_str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT task_key FROM checklist_completions WHERE date=?", (date_str,)
    ).fetchall()
    conn.close()
    return [r["task_key"] for r in rows]

def get_stats():
    conn = get_conn()
    total_mins = conn.execute("SELECT COALESCE(SUM(duration_mins),0) as t FROM sessions").fetchone()["t"]
    total_sessions = conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()["c"]
    today = date.today().isoformat()
    today_mins = conn.execute(
        "SELECT COALESCE(SUM(duration_mins),0) as t FROM sessions WHERE date=?", (today,)
    ).fetchone()["t"]
    conn.close()
    return {
        "total_hours": round(total_mins / 60, 1),
        "total_sessions": total_sessions,
        "today_mins": today_mins,
    }

def get_checklist_tasks(day_type: str):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM checklist_tasks WHERE day_type=? ORDER BY id", (day_type,)).fetchall()
    conn.close()
    tasks = []
    for row in rows:
        task = dict(row)
        task["key"] = task["task_key"]
        tasks.append(task)
    return tasks


def add_checklist_task(day_type, label, desc, time_str, course, duration_minutes, tag, notes, task_key=None):
    if not task_key:
        task_key = _generate_task_key(day_type)
    conn = get_conn()
    cursor = conn.execute("""
        INSERT INTO checklist_tasks (day_type, task_key, label, desc, time, course, duration_minutes, tag, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (day_type, task_key, label, desc, time_str, course, duration_minutes, tag, notes))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {
        "id": task_id,
        "day_type": day_type,
        "task_key": task_key,
        "key": task_key,
        "label": label,
        "desc": desc,
        "time": time_str,
        "course": course,
        "duration_minutes": duration_minutes,
        "tag": tag,
        "notes": notes,
    }


def update_checklist_task(task_id, day_type, task_key, label, desc, time_str, course, duration_minutes, tag, notes):
    conn = get_conn()
    conn.execute("""
        UPDATE checklist_tasks
        SET day_type=?, task_key=?, label=?, desc=?, time=?, course=?, duration_minutes=?, tag=?, notes=?
        WHERE id=?
    """, (day_type, task_key, label, desc, time_str, course, duration_minutes, tag, notes, task_id))
    conn.commit()
    conn.close()
    return {
        "id": task_id,
        "day_type": day_type,
        "task_key": task_key,
        "key": task_key,
        "label": label,
        "desc": desc,
        "time": time_str,
        "course": course,
        "duration_minutes": duration_minutes,
        "tag": tag,
        "notes": notes,
    }

def delete_checklist_task(task_id):
    conn = get_conn()
    conn.execute("DELETE FROM checklist_tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
