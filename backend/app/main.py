from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analytics, health, chat


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Phase 1: no auto-migrate on startup (run setup_db manually)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analytics.router)
app.include_router(chat.router)

@app.get("/")
def root() -> dict:
    return {
        "message": "School Analytics API",
        "docs": "/docs",
        "health": "/health",
        "analytics": "/analytics/latest-year/summary",
        "chat": "/chat",
    }