"""
FastAPI Application Entrypoint.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.core.logging import logger
from backend.db.session import init_db
from backend.api.router import api_router
from backend.workers.monitoring_manager import monitoring_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Explainable Forest Fire Detection Backend API...")
    init_db()

    # Ensure media directories exist
    media_path = Path(settings.MEDIA_ROOT)
    (media_path / "originals").mkdir(parents=True, exist_ok=True)
    (media_path / "heatmaps").mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    logger.info("Shutting down API and releasing worker resources...")
    monitoring_manager.shutdown_all()
    logger.info("Shutdown completed.")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Real-Time Detection of Forest Fires Using FireNet-CNN and Explainable AI Techniques",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Media Directory for Evidence & Heatmaps
media_dir = Path(settings.MEDIA_ROOT)
media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_dir.resolve())), name="media")

# Register API Routers
app.include_router(api_router)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "path": request.url.path}
    )


@app.get("/", summary="Root API Information")
def root():
    return {
        "title": settings.APP_NAME,
        "version": "1.0.0",
        "documentation": "/docs",
        "status": "operational"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
