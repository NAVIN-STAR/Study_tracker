from fastapi import FastAPI

import database as db
from routers.analytics import router as analytics_router
from routers.checklist import router as checklist_router
from routers.home import router as home_router
from routers.sessions import router as sessions_router

app = FastAPI(title="Study Tracker")
db.init_db()

app.include_router(home_router)
app.include_router(checklist_router)
app.include_router(analytics_router)
app.include_router(sessions_router)

