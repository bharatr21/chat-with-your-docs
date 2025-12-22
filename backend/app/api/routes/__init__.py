"""
API route modules
"""
from fastapi import APIRouter
from . import chat, documents, sessions, models

api_router = APIRouter()

api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
