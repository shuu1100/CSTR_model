"""Aggregated API v1 router."""

from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.models import router as models_router
from backend.app.api.v1.simulations import router as simulations_router
from backend.app.api.v1.datasets import router as datasets_router
from backend.app.api.v1.analysis import router as analysis_router
from backend.app.api.v1.ml import router as ml_router
from backend.app.api.v1.history import router as history_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(models_router)
api_v1_router.include_router(simulations_router)
api_v1_router.include_router(datasets_router)
api_v1_router.include_router(analysis_router)
api_v1_router.include_router(ml_router)
api_v1_router.include_router(history_router)


