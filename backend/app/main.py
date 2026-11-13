"""FastAPI application entry point for ReferralPilot AI."""

import time
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


OPENAPI_TAGS = [
    {"name": "System", "description": "System health diagnostics, database connectivity, and uptime monitoring."},
    {"name": "Auth", "description": "JWT-based authentication, user registration, and access token validation."},
    {"name": "Profile", "description": "Candidate positioning target, skills, graduation batch, and education management."},
    {"name": "Discovery", "description": "Multi-source discovery runs, scheduler execution, and source adapter metrics."},
    {"name": "Opportunities", "description": "Verified opportunities, classification badges, and manual link submission."},
    {"name": "Applications", "description": "Application lifecycle tracking, referral requests, and interview status."},
    {"name": "Interactions", "description": "Networking interactions, outreach logging, and referral conversation records."},
    {"name": "Follow-ups", "description": "Automated schedule reminders and pending networking follow-ups."},
    {"name": "Analytics", "description": "Candidate conversion funnel, match score distribution, and source performance."},
    {"name": "Telegram", "description": "Telegram webhook handlers for mobile post capture and automated notifications."},
]


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "ReferralPilot AI is an autonomous career intelligence and opportunity discovery platform "
            "engineered for engineering students and graduates to target high-ROI referrals, internships, "
            "hackathons, scholarships, and AI/ML research programs."
        ),
        openapi_tags=OPENAPI_TAGS,
        docs_url="/docs",
        redoc_url="/redoc",
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
        db_latency_ms = None
        opp_count = 0
        try:
            start_t = time.perf_counter()
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db_latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
            try:
                opp_count = db.execute(text("SELECT count(*) FROM opportunities")).scalar() or 0
            except Exception:
                opp_count = 0
            db_ok = True
            db.close()
        except Exception as exc:
            logger.warning(f"Health check database ping failed: {exc}")
            db_ok = False

        return {
            "status": "healthy" if db_ok else "degraded",
            "app": settings.app_name,
            "version": "1.0.0",
            "environment": settings.environment,
            "database": {
                "status": "connected" if db_ok else "disconnected",
                "latency_ms": db_latency_ms,
            },
            "stats": {
                "persisted_opportunities": opp_count,
            },
        }

    app.include_router(router)
    return app


app = create_app()

