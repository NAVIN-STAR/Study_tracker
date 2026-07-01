from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from services.analytics_service import AnalyticsService

router = APIRouter()
templates = Jinja2Templates(directory="templates")
analytics_service = AnalyticsService()


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    summary = analytics_service.get_dashboard_summary()
    weekly = analytics_service.get_weekly_stats(goal_mins=summary["goal_mins"])
    activity = analytics_service.get_activity_chart()
    heatmap = analytics_service.get_heatmap_data()
    course_breakdown = analytics_service.get_course_breakdown()
    productivity = analytics_service.get_productivity_metrics()
    day_analysis = analytics_service.get_day_of_week_analysis()
    schedule_breakdown = analytics_service.get_schedule_type_breakdown()
    monthly_trends = analytics_service.get_monthly_trends()
    recent_activity = analytics_service.get_recent_activity()
    insights = analytics_service.get_learning_insights()

    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "summary": summary,
            "weekly": weekly,
            "activity": activity,
            "heatmap": heatmap,
            "course_breakdown": course_breakdown,
            "productivity": productivity,
            "day_analysis": day_analysis,
            "schedule_breakdown": schedule_breakdown,
            "monthly_trends": monthly_trends,
            "recent_activity": recent_activity,
            "insights": insights,
        },
    )
