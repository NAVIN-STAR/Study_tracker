from datetime import date
from typing import List, Optional

import database as db
from repositories.session_repository import SessionRepository


class SessionService:
    def __init__(self):
        self.session_repo = SessionRepository()

    def get_all(self) -> List[dict]:
        return self.session_repo.get_all()

    def get_for_date(self, date_str: str) -> List[dict]:
        return self.session_repo.get_for_date(date_str)

    def get_today(self) -> List[dict]:
        return self.session_repo.get_today()

    def add_session(self, payload: dict) -> None:
        self.session_repo.add(
            payload["date"],
            payload.get("topic", ""),
            payload.get("course", ""),
            int(payload.get("duration_mins", 0)),
            payload.get("day_type", ""),
            payload.get("notes", ""),
            payload.get("task_key"),
        )

    def delete_session(self, session_id: int) -> None:
        self.session_repo.delete(session_id)

    def auto_log_pending_tasks(self, date_str: str, day_type: str, notes: str, course: Optional[str] = None) -> None:
        from repositories.checklist_repository import ChecklistRepository

        checklist_repo = ChecklistRepository()
        done = checklist_repo.get_done(date_str)
        tasks = checklist_repo.get_tasks(day_type)
        course_name = course or ""
        for task in tasks:
            if task["task_key"] in done:
                self.session_repo.add(
                    date_str,
                    task.get("label", ""),
                    course_name or task.get("course", ""),
                    int(task.get("duration_minutes", 0) or 0),
                    day_type,
                    notes,
                    task["task_key"],
                )
