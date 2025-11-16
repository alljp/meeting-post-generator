from fastapi import APIRouter
from app.api.v1 import auth, calendar, meetings, settings, social, recall

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(social.router, prefix="/social", tags=["social"])
api_router.include_router(recall.router, prefix="/recall", tags=["recall"])

