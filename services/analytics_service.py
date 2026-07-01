from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List

import database as db


class AnalyticsService:
    def _load_sessions(self):
        conn = db.get_conn()
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY date DESC, created_at DESC"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _session_dates(self):
        return sorted({s["date"] for s in self._load_sessions() if s.get("date")})

    def _compute_streaks(self):
        dates = set(self._session_dates())
        if not dates:
            return {"current": 0, "longest": 0}

        current = 0
        day = date.today()
        while day.isoformat() in dates:
            current += 1
            day -= timedelta(days=1)

        longest = 0
        streak = 0
        prev_day = None
        for day_str in sorted(dates):
            day_value = date.fromisoformat(day_str)
            if prev_day and (day_value - prev_day).days == 1:
                streak += 1
            else:
                streak = 1
            longest = max(longest, streak)
            prev_day = day_value

        return {"current": current, "longest": longest}

    def get_dashboard_summary(self, goal_mins: int = 1500) -> Dict:
        sessions = self._load_sessions()
        today = date.today().isoformat()
        week_start = (date.today() - timedelta(days=6)).isoformat()
        month_start = date.today().replace(day=1).isoformat()

        today_mins = sum(s["duration_mins"] for s in sessions if s.get("date") == today)
        week_mins = sum(
            s["duration_mins"]
            for s in sessions
            if week_start <= s.get("date", "") <= today
        )
        month_mins = sum(
            s["duration_mins"]
            for s in sessions
            if month_start <= s.get("date", "") <= today
        )
        total_mins = sum(s["duration_mins"] for s in sessions)
        streaks = self._compute_streaks()

        return {
            "today_mins": today_mins,
            "week_mins": week_mins,
            "month_mins": month_mins,
            "total_mins": total_mins,
            "today_hours": round(today_mins / 60, 1),
            "week_hours": round(week_mins / 60, 1),
            "month_hours": round(month_mins / 60, 1),
            "total_hours": round(total_mins / 60, 1),
            "current_streak": streaks["current"],
            "longest_streak": streaks["longest"],
            "goal_mins": goal_mins,
            "goal_progress": min(100, round((week_mins / goal_mins) * 100)) if goal_mins else 0,
            "goal_remaining": max(0, goal_mins - week_mins) if goal_mins else 0,
        }

    def get_weekly_stats(self, goal_mins: int = 1500) -> Dict:
        sessions = self._load_sessions()
        today = date.today().isoformat()
        week_start = (date.today() - timedelta(days=6)).isoformat()
        week_mins = sum(
            s["duration_mins"]
            for s in sessions
            if week_start <= s.get("date", "") <= today
        )
        progress = min(100, round((week_mins / goal_mins) * 100)) if goal_mins else 0
        return {
            "goal_mins": goal_mins,
            "current_mins": week_mins,
            "progress_percent": progress,
            "remaining_mins": max(0, goal_mins - week_mins) if goal_mins else 0,
            "week_start": week_start,
            "week_end": today,
        }

    def get_activity_chart(self, days: int = 30) -> List[Dict]:
        sessions = self._load_sessions()
        today = date.today()
        result = []
        for offset in range(days - 1, -1, -1):
            day = today - timedelta(days=offset)
            day_iso = day.isoformat()
            mins = sum(s["duration_mins"] for s in sessions if s.get("date") == day_iso)
            result.append({"date": day_iso, "label": day.strftime("%b %d"), "mins": mins})
        return result

    def get_heatmap_data(self, weeks: int = 8) -> List[List[Dict]]:
        today = date.today()
        cells = []
        for week in range(weeks):
            week_cells = []
            for weekday in range(7):
                day = today - timedelta(days=((weeks - 1 - week) * 7) + (6 - weekday))
                day_iso = day.isoformat()
                mins = sum(
                    s["duration_mins"]
                    for s in self._load_sessions()
                    if s.get("date") == day_iso
                )
                week_cells.append({"date": day_iso, "mins": mins, "day": day.strftime("%a")})
            cells.append(week_cells)
        return cells

    def get_course_breakdown(self) -> List[Dict]:
        sessions = self._load_sessions()
        totals = defaultdict(int)
        for session in sessions:
            course = (session.get("course") or "Uncategorized").strip() or "Uncategorized"
            totals[course] += int(session.get("duration_mins") or 0)

        total_mins = sum(totals.values()) or 1
        items = [
            {
                "course": course,
                "mins": mins,
                "percent": round((mins / total_mins) * 100),
            }
            for course, mins in sorted(totals.items(), key=lambda item: item[1], reverse=True)
        ]
        return items

    def get_productivity_metrics(self) -> Dict:
        sessions = self._load_sessions()
        if not sessions:
            return {
                "most_studied_course": "—",
                "least_studied_course": "—",
                "average_session_length": 0,
                "average_daily_study_time": 0,
                "average_weekly_study_time": 0,
                "total_sessions": 0,
                "longest_session": 0,
            }

        breakdown = self.get_course_breakdown()
        total_mins = sum(s["duration_mins"] for s in sessions)
        active_dates = self._session_dates()
        weeks_with_activity = max(1, len(self._week_starts(active_dates)))

        return {
            "most_studied_course": breakdown[0]["course"] if breakdown else "—",
            "least_studied_course": breakdown[-1]["course"] if breakdown else "—",
            "average_session_length": round(sum(s["duration_mins"] for s in sessions) / len(sessions)),
            "average_daily_study_time": round(total_mins / max(1, len(active_dates))),
            "average_weekly_study_time": round(total_mins / weeks_with_activity),
            "total_sessions": len(sessions),
            "longest_session": max(s["duration_mins"] for s in sessions),
        }

    def get_day_of_week_analysis(self) -> List[Dict]:
        sessions = self._load_sessions()
        totals = defaultdict(int)
        names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for session in sessions:
            date_value = session.get("date")
            if not date_value:
                continue
            day_name = date.fromisoformat(date_value).strftime("%A")
            totals[day_name] += int(session.get("duration_mins") or 0)

        return [
            {"day": day, "mins": totals.get(day, 0), "hours": round(totals.get(day, 0) / 60, 1)}
            for day in names
        ]

    def get_schedule_type_breakdown(self) -> List[Dict]:
        sessions = self._load_sessions()
        totals = defaultdict(int)
        for session in sessions:
            totals[session.get("day_type") or "unknown"] += int(session.get("duration_mins") or 0)

        return [
            {"day_type": day_type, "mins": mins, "hours": round(mins / 60, 1)}
            for day_type, mins in sorted(totals.items(), key=lambda item: item[1], reverse=True)
        ]

    def get_monthly_trends(self, months: int = 6) -> List[Dict]:
        sessions = self._load_sessions()
        month_totals = defaultdict(int)
        for session in sessions:
            date_value = session.get("date")
            if not date_value:
                continue
            month_key = date.fromisoformat(date_value).strftime("%Y-%m")
            month_totals[month_key] += int(session.get("duration_mins") or 0)

        ordered = []
        current = date.today().replace(day=1)
        for offset in range(months - 1, -1, -1):
            year = current.year
            month = current.month - offset
            while month <= 0:
                month += 12
                year -= 1
            while month > 12:
                month -= 12
                year += 1
            month_key = f"{year:04d}-{month:02d}"
            ordered.append({"month": month_key, "mins": month_totals.get(month_key, 0), "hours": round(month_totals.get(month_key, 0) / 60, 1)})
        return ordered

    def get_recent_activity(self, limit: int = 8) -> List[Dict]:
        sessions = self._load_sessions()
        return [
            {
                "date": s.get("date"),
                "topic": s.get("topic") or "Untitled session",
                "course": s.get("course") or "Uncategorized",
                "duration_mins": int(s.get("duration_mins") or 0),
                "day_type": s.get("day_type") or "unknown",
            }
            for s in sessions[:limit]
        ]

    def get_learning_insights(self) -> List[str]:
        summary = self.get_dashboard_summary()
        weekly = self.get_weekly_stats(goal_mins=1500)
        breakdown = self.get_course_breakdown()
        day_analysis = self.get_day_of_week_analysis()
        schedule = self.get_schedule_type_breakdown()

        insights = []
        if summary["current_streak"] > 0:
            insights.append(f"Your current streak is {summary['current_streak']} days — keep it going.")
        if summary["current_streak"] >= summary["longest_streak"]:
            insights.append("This is your longest streak so far.")
        if weekly["progress_percent"] >= 80:
            insights.append("You are on pace to beat your weekly goal.")
        elif weekly["progress_percent"] < 50:
            insights.append("You are behind your weekly goal, so a short focused session would help.")
        if breakdown:
            top = breakdown[0]
            insights.append(f"{top['course']} is your most studied course right now.")
        if day_analysis:
            most_productive = max(day_analysis, key=lambda item: item["mins"])
            insights.append(f"{most_productive['day']} is your most productive day so far.")
        if schedule:
            top_schedule = schedule[0]
            insights.append(f"{top_schedule['day_type'].upper()} contributes the most study time in your routine.")
        return insights

    def _week_starts(self, dates: List[str]) -> List[str]:
        weeks = set()
        for date_str in dates:
            try:
                current = date.fromisoformat(date_str)
            except ValueError:
                continue
            week_start = current - timedelta(days=current.weekday())
            weeks.add(week_start.isoformat())
        return sorted(weeks)
