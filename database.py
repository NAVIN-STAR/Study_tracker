import sqlite3
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

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

    conn.commit()
    conn.close()

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

def add_session(date_str, topic, course, duration_mins, day_type, notes):
    conn = get_conn()
    conn.execute(
        "INSERT INTO sessions (date, topic, course, duration_mins, day_type, notes) VALUES (?,?,?,?,?,?)",
        (date_str, topic, course, duration_mins, day_type, notes)
    )
    conn.commit()
    conn.close()

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
