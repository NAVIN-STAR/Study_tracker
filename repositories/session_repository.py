import sqlite3
from datetime import date
from typing import List, Optional

import database as db


class SessionRepository:
    def get_all(self) -> List[dict]:
        conn = db.get_conn()
        rows = conn.execute(
            """
            SELECT s.*, t.time AS task_time
            FROM sessions s
            LEFT JOIN checklist_tasks t ON s.task_key = t.task_key
            ORDER BY s.date DESC, s.created_at DESC
            """
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_for_date(self, date_str: str) -> List[dict]:
        conn = db.get_conn()
        rows = conn.execute(
            """
            SELECT s.*, t.time AS task_time
            FROM sessions s
            LEFT JOIN checklist_tasks t ON s.task_key = t.task_key
            WHERE s.date = ?
            ORDER BY s.created_at DESC
            """,
            (date_str,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_today(self) -> List[dict]:
        today = date.today().isoformat()
        conn = db.get_conn()
        rows = conn.execute(
            """
            SELECT s.*, t.time AS task_time
            FROM sessions s
            LEFT JOIN checklist_tasks t ON s.task_key = t.task_key
            WHERE s.date = ?
            ORDER BY s.created_at DESC
            """,
            (today,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_recent(self, limit: int = 30) -> List[dict]:
        conn = db.get_conn()
        rows = conn.execute(
            """
            SELECT s.*, t.time AS task_time
            FROM sessions s
            LEFT JOIN checklist_tasks t ON s.task_key = t.task_key
            ORDER BY s.date DESC, s.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def add(self, date_str: str, topic: str, course: str, duration_mins: int, day_type: str, notes: str, task_key: Optional[str] = None) -> None:
        conn = db.get_conn()
        conn.execute(
            "INSERT INTO sessions (date, topic, course, duration_mins, day_type, notes, task_key) VALUES (?,?,?,?,?,?,?)",
            (date_str, topic, course, duration_mins, day_type, notes, task_key),
        )
        conn.commit()
        conn.close()

    def delete(self, session_id: int) -> None:
        conn = db.get_conn()
        conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        conn.commit()
        conn.close()

    def has_task_been_logged(self, date_str: str, task_key: str) -> bool:
        if not task_key:
            return False
        conn = db.get_conn()
        row = conn.execute(
            "SELECT id FROM sessions WHERE date=? AND task_key=?", (date_str, task_key)
        ).fetchone()
        conn.close()
        return row is not None
