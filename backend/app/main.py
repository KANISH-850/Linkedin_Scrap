"""FastAPI application entry point for ReferralPilot AI."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.database.seed import seed_database
from app.database.session import SessionLocal

setup_logging("INFO")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.validate_production_constraints()

    # Seed initial profile, sources, and admin if missing
    db = SessionLocal()
    try:
        seed_database(db)
    except Exception as exc:
        logger.warning(f"Database seed skipped or failed (ensure migrations are applied): {exc}")
    finally:
        db.close()

    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Personal AI-powered career opportunity intelligence and referral management assistant.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def safe_global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."},
        )

    @app.get("/health", tags=["System"])
    def health_check():
        db_ok = False
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db_ok = True
            db.close()
        except Exception:
            db_ok = False
        return {
            "status": "healthy" if db_ok else "degraded",
            "app": settings.app_name,
            "environment": settings.environment,
            "database": "connected" if db_ok else "disconnected",
        }

    app.include_router(router)
    return app


app = create_app()

