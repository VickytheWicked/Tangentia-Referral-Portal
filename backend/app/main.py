import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.api.auth import router as auth_router
from app.api.jobs import router as jobs_router
from app.api.referrals import router as referrals_router
from app.api.hr import router as hr_router
from app.api.analytics import router as analytics_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("referral_portal")

# Create tables if using SQLite or quick dev mode
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Internal Employee Referral Portal for submitting candidates and uploading CVs to Microsoft SharePoint via Microsoft Graph API.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

@app.on_event("startup")
async def startup_event():
    from app.database import SessionLocal
    from app.services.excel import get_excel_service
    from app.services.excel.sync import initialize_and_sync_excel

    db = SessionLocal()
    try:
        excel_svc = get_excel_service()
        initialize_and_sync_excel(db, excel_svc)
    except Exception as e:
        logger.error(f"Failed to synchronize with Microsoft Excel workbook on startup: {e}", exc_info=True)
    finally:
        db.close()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler to sanitize unexpected server errors and prevent credential/stack leakage
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
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
        "sharepoint_storage": settings.SHAREPOINT_STORAGE_TYPE,
        "dev_mode": settings.DEV_MODE,
    }


# Include API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(jobs_router, prefix=settings.API_V1_STR)
app.include_router(referrals_router, prefix=settings.API_V1_STR)
app.include_router(hr_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
