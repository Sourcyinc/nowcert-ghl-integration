"""
API v1
"""
from fastapi import APIRouter
from app.api.v1.endpoints import webhooks, sync

api_router = APIRouter()

# Incluir routers
api_router.include_router(
    webhooks.router,
    prefix="/webhooks",
    tags=["Webhooks"]
)

api_router.include_router(
    sync.router,
    prefix="/sync",
    tags=["Sincronización"]
)

