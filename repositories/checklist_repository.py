from typing import List, Optional

import database as db


class ChecklistRepository:
    def get_tasks(self, day_type: str) -> List[dict]:
        conn = db.get_conn()
        rows = conn.execute(
            "SELECT * FROM checklist_tasks WHERE day_type=? ORDER BY id", (day_type,)
        ).fetchall()
        conn.close()
        tasks = []
        for row in rows:
            task = dict(row)
            task["key"] = task["task_key"]
            tasks.append(task)
        return tasks

    def add_task(self, day_type: str, task_key: str, label: str, desc: str, time_str: str, course: str, duration_minutes: int, tag: str, notes: str) -> dict:
        conn = db.get_conn()
        cursor = conn.execute(
            """
            INSERT INTO checklist_tasks (day_type, task_key, label, desc, time, course, duration_minutes, tag, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (day_type, task_key, label, desc, time_str, course, duration_minutes, tag, notes),
        )
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

    def update_task(self, task_id: int, day_type: str, task_key: str, label: str, desc: str, time_str: str, course: str, duration_minutes: int, tag: str, notes: str) -> dict:
        conn = db.get_conn()
        conn.execute(
            """
            UPDATE checklist_tasks
            SET day_type=?, task_key=?, label=?, desc=?, time=?, course=?, duration_minutes=?, tag=?, notes=?
            WHERE id=?
            """,
            (day_type, task_key, label, desc, time_str, course, duration_minutes, tag, notes, task_id),
        )
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

    def delete_task(self, task_id: int) -> None:
        conn = db.get_conn()
        conn.execute("DELETE FROM checklist_tasks WHERE id=?", (task_id,))
        conn.commit()
        conn.close()

    def toggle_checklist(self, date_str: str, task_key: str) -> bool:
        conn = db.get_conn()
        existing = conn.execute(
            "SELECT id FROM checklist_completions WHERE date=? AND task_key=?",
            (date_str, task_key),
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

    def get_done(self, date_str: str) -> List[str]:
        conn = db.get_conn()
        rows = conn.execute(
            "SELECT task_key FROM checklist_completions WHERE date=?", (date_str,)
        ).fetchall()
        conn.close()
        return [r["task_key"] for r in rows]
