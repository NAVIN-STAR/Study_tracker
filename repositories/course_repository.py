from typing import List

import database as db


class CourseRepository:
    def get_all(self) -> List[dict]:
        conn = db.get_conn()
        rows = conn.execute("SELECT * FROM courses ORDER BY name").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def add(self, name: str) -> dict:
        conn = db.get_conn()
        cursor = conn.execute("INSERT INTO courses (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return {"id": cursor.lastrowid, "name": name}
