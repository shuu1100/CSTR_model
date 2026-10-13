"""FastAPI application entry point for CSTR Lab."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.router import api_v1_router
from backend.app.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Computational simulator and analysis platform for an ideal Continuous Stirred-Tank Reactor (CSTR).",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration restricted strictly to local frontend development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
)

# Include versioned API router
app.include_router(api_v1_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root():
    """Root metadata pointer."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "documentation": "/docs",
        "health_check": f"{settings.api_v1_prefix}/health",
        "models": f"{settings.api_v1_prefix}/models",
    }
