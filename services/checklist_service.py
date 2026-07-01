from datetime import date
from typing import List, Optional

from repositories.checklist_repository import ChecklistRepository
from repositories.session_repository import SessionRepository


class ChecklistService:
    def __init__(self):
        self.checklist_repo = ChecklistRepository()
        self.session_repo = SessionRepository()

    def get_tasks(self, day_type: str) -> List[dict]:
        return self.checklist_repo.get_tasks(day_type)

    def get_done(self, date_str: str) -> List[str]:
        return self.checklist_repo.get_done(date_str)

    def toggle_task(self, date_str: str, task_key: str) -> tuple[bool, bool]:
        already_logged = self.session_repo.has_task_been_logged(date_str, task_key)
        if already_logged:
            return False, True

        done = self.checklist_repo.toggle_checklist(date_str, task_key)
        return done, False

    def create_task(self, payload: dict) -> dict:
        return self.checklist_repo.add_task(
            payload["day_type"],
            payload["task_key"],
            payload["label"],
            payload.get("desc", ""),
            payload.get("time", ""),
            payload.get("course", ""),
            payload.get("duration_minutes", 0),
            payload.get("tag", ""),
            payload.get("notes", ""),
        )

    def update_task(self, task_id: int, payload: dict) -> dict:
        return self.checklist_repo.update_task(
            task_id,
            payload["day_type"],
            payload["task_key"],
            payload["label"],
            payload.get("desc", ""),
            payload.get("time", ""),
            payload.get("course", ""),
            payload.get("duration_minutes", 0),
            payload.get("tag", ""),
            payload.get("notes", ""),
        )

    def delete_task(self, task_id: int) -> None:
        self.checklist_repo.delete_task(task_id)

    def build_checklist_context(self, day_type: str, today: Optional[str] = None) -> dict:
        current_date = today or date.today().isoformat()
        tasks = self.get_tasks(day_type)
        done_keys = self.get_done(current_date)
        return {
            "tasks": tasks,
            "done_keys": done_keys,
            "date": current_date,
        }
