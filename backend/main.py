"""
FastAPI Application Entrypoint.
"""

import os
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
from backend.services.demo_monitoring_service import demo_monitoring_service
from backend.workers.monitoring_manager import monitoring_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Explainable Forest Fire Detection Backend API...")
    init_db()

    # Seed initial cameras and baseline telemetry if empty (useful for fresh cloud deployments)
    try:
        from scripts.seed_database import seed
        seed()
    except Exception as exc:
        logger.warning("Database seed check notice: %s", exc)

    # Ensure media directories exist
    media_path = Path(settings.MEDIA_ROOT)
    (media_path / "originals").mkdir(parents=True, exist_ok=True)
    (media_path / "heatmaps").mkdir(parents=True, exist_ok=True)

    # Optional embedded Telegram bot for single-service cloud deployments (e.g. Render Free Tier)
    bot_app = None
    if settings.TELEGRAM_ENABLED and os.environ.get("RUN_BOT_IN_API", "false").lower() in ("true", "1", "yes"):
        try:
            from bot import start_bot_async
            bot_app = await start_bot_async()
        except Exception as exc:
            logger.warning("Could not launch embedded Telegram bot: %s", exc)

    yield

    # Shutdown
    logger.info("Shutting down API and releasing worker resources...")
    if bot_app:
        try:
            if bot_app.updater and bot_app.updater.running:
                await bot_app.updater.stop()
            await bot_app.stop()
            await bot_app.shutdown()
        except Exception as exc:
            logger.warning("Error stopping embedded Telegram bot: %s", exc)

    demo_monitoring_service.stop()
    monitoring_manager.shutdown_all()
    logger.info("Shutdown completed.")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Real-Time Detection of Forest Fires Using FireNet-CNN and Explainable AI Techniques",
    lifespan=lifespan
)

# CORS Middleware (supports local development, specific origins, and cloud wildcards)
cors_origins = settings.get_cors_origins()
allow_all = "*" in cors_origins or settings.CORS_ORIGINS.strip() == "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else cors_origins,
    allow_credentials=not allow_all,
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
