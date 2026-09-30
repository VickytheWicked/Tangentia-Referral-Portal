import sys
sys.path = [p for p in sys.path if not ("/agents/python" in p or p.startswith("/agents"))]
if "typing_extensions" in sys.modules:
    del sys.modules["typing_extensions"]

import logging
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.api.auth import router as auth_router
from app.api.jobs import router as jobs_router
from app.api.referrals import router as referrals_router
from app.api.hr import router as hr_router
from app.api.analytics import router as analytics_router
from app.api.cv_intelligence import router as cv_intelligence_router
from app.historical_suggestions.api import router as historical_suggestions_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("referral_portal")

# Create tables automatically for SQLite in-memory dev mode; persistent DBs use Alembic migrations
if settings.DATABASE_URL.startswith("sqlite") and ":memory:" in settings.DATABASE_URL:
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Internal Employee Referral Portal for submitting candidates, tracking referrals, and archiving CVs in secure cloud storage.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

@app.on_event("startup")
async def startup_event():
    # If running against PostgreSQL in production, ensure Alembic migrations are up to date
    if settings.DATABASE_URL.startswith("postgresql"):
        try:
            import os
            from alembic.config import Config
            from alembic import command
            alembic_ini_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")
            if os.path.exists(alembic_ini_path):
                migration_url = settings.DATABASE_URL
                if migration_url.startswith("postgresql://"):
                    migration_url = migration_url.replace("postgresql://", "postgresql+psycopg2://", 1)
                cfg.set_main_option("sqlalchemy.url", migration_url)
                command.upgrade(cfg, "head")
                logger.info("Alembic database migrations applied successfully.")
        except Exception as e:
            logger.warning(f"Alembic auto-migration check note: {e}")

    from app.database import SessionLocal
    from app.services.excel import get_excel_service
    from app.services.excel.sync import initialize_and_sync_excel
    from app.services.cats_scheduler import start_cats_scheduler

    db = SessionLocal()
    try:
        excel_svc = get_excel_service()
        initialize_and_sync_excel(db, excel_svc)
    except Exception as e:
        logger.error(f"Failed to synchronize with Microsoft Excel workbook on startup: {e}", exc_info=True)
    finally:
        db.close()


    # Initialize isolated CV Intelligence SQLite database if enabled
    if settings.CV_INTELLIGENCE_ENABLED:
        try:
            from app.cv_intelligence.database import init_cv_db
            init_cv_db()
        except Exception as e:
            logger.error(f"Failed to initialize CV Intelligence database: {e}", exc_info=True)

        try:
            from app.cv_intelligence.requirement_analyzer import ensure_all_openings_processed_by_llm
            startup_db = SessionLocal()
            try:
                ensure_all_openings_processed_by_llm(startup_db)
            finally:
                startup_db.close()
        except Exception as e:
            logger.warning(f"Failed to verify opening requirements on startup: {e}")

    # Start automatic background sync from Tangentia CATS One every 6 hours
    try:
        start_cats_scheduler()
    except Exception as e:
        logger.error(f"Failed to start CATS auto-sync scheduler: {e}", exc_info=True)

    # Start automatic background CV Intelligence processing queue worker
    if settings.CV_INTELLIGENCE_ENABLED:
        try:
            from app.cv_intelligence.queue import start_cv_queue_worker
            start_cv_queue_worker()
        except Exception as e:
            logger.error(f"Failed to start CV queue worker: {e}", exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    from app.services.cats_scheduler import stop_cats_scheduler
    stop_cats_scheduler()
    try:
        from app.cv_intelligence.queue import stop_cv_queue_worker
        stop_cv_queue_worker()
    except Exception as e:
        logger.error(f"Failed to stop CV queue worker: {e}")
    try:
        from app.cv_intelligence.blob_sync import upload_cv_db_to_blob, is_cv_blob_sync_enabled
        if is_cv_blob_sync_enabled():
            upload_cv_db_to_blob()
    except Exception as e:
        logger.error(f"Failed to persist CV Intelligence DB to Azure Blob on shutdown: {e}")

# CORS Middleware - Restrict origins in production to configured origins (no open wildcard)
cors_kwargs = {
    "allow_origins": settings.all_cors_origins,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "expose_headers": ["Content-Disposition"],
}
if settings.CORS_ORIGIN_REGEX:
    cors_kwargs["allow_origin_regex"] = settings.CORS_ORIGIN_REGEX
elif settings.is_dev_token_allowed:
    cors_kwargs["allow_origin_regex"] = r"https://.*\.trycloudflare\.com"

app.add_middleware(CORSMiddleware, **cors_kwargs)



# Global Exception Handler to sanitize unexpected server errors and prevent credential/stack leakage
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected server error occurred. Please contact IT support if the issue persists.",
        },
    )


# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "storage_type": settings.STORAGE_TYPE,
        "dev_mode": settings.DEV_MODE,
    }


# Include API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(jobs_router, prefix=settings.API_V1_STR)
app.include_router(referrals_router, prefix=settings.API_V1_STR)
app.include_router(hr_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(cv_intelligence_router, prefix=settings.API_V1_STR)
app.include_router(historical_suggestions_router, prefix=settings.API_V1_STR)
