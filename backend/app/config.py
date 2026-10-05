import os
import json
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "Tangentia Employee Referral Portal"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    DEV_MODE: bool = True  # Allows local dev testing with simulated users and local mock storage
    
    # API Prefix
    API_V1_STR: str = "/api"

    # Database (In-Memory Query Engine; Persistent Storage is Microsoft Excel in Azure Blob Storage)
    DATABASE_URL: str = "sqlite:///:memory:"

    # Excel Ledger Storage (Azure Blob Storage or Local)
    EXCEL_STORAGE_TYPE: str = Field(default="mock", description="'blob' for Azure Blob Storage Excel ledger, 'mock' for local development Excel file")
    EXCEL_FILE_PATH: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Tangentia_Referrals.xlsx")
    EXCEL_DRIVE_ID: str = Field(default="", description="Optional legacy Drive ID if configured")
    EXCEL_FILE_ITEM_ID: str = Field(default="", description="Optional legacy item ID")
    EXCEL_WORKBOOK_NAME: str = Field(default="Tangentia_Referrals.xlsx", description="Name of the Excel workbook file")
    
    # Authentication & JWT (Portal HR Admin Login & Employee Zero-Friction)
    JWT_SECRET_KEY: str = Field(default="", description="Secret key for signing JWT tokens")
    ALLOW_DEV_TOKENS: bool = Field(default=False, description="Explicitly allow dev/test tokens. NEVER allowed in production")
    AZURE_TENANT_ID: str = Field(default="common", description="Azure Tenant ID (if applicable)")
    AZURE_CLIENT_ID: str = Field(default="", description="Azure App Client ID (if applicable)")
    AZURE_CLIENT_SECRET: str = Field(default="", description="Azure Client Secret (if applicable)")
    AZURE_HR_GROUP_ID: str = Field(default="", description="Security Group ID for HR Admins (if applicable)")
    
    @property
    def jwt_secret_key(self) -> str:
        """Retrieve JWT signing secret with production safety enforcement."""
        if self.JWT_SECRET_KEY and self.JWT_SECRET_KEY.strip():
            return self.JWT_SECRET_KEY.strip()
        if self.ENVIRONMENT == "production":
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: JWT_SECRET_KEY must be configured in production!"
            )
        return "tangentia-portal-dev-insecure-jwt-key-do-not-use-in-production"

    @property
    def is_dev_token_allowed(self) -> bool:
        """Dev/mock tokens are strictly forbidden in production under all circumstances."""
        if self.ENVIRONMENT == "production":
            return False
        return bool(self.DEV_MODE or self.ALLOW_DEV_TOKENS)

    
    @property
    def AZURE_AUTHORITY(self) -> str:
        return f"https://login.microsoftonline.com/{self.AZURE_TENANT_ID}"

    @property
    def AZURE_JWKS_URL(self) -> str:
        return f"https://login.microsoftonline.com/{self.AZURE_TENANT_ID}/discovery/v2.0/keys"

    # Document & CV Storage (Azure Blob Storage / Local Mock)
    STORAGE_TYPE: str = Field(default="mock", description="'blob' for Azure Blob Storage, 'mock' for local development")
    
    # Azure Blob Storage (used when STORAGE_TYPE == 'blob' or EXCEL_STORAGE_TYPE == 'blob')
    AZURE_STORAGE_CONNECTION_STRING: str = Field(default="", description="Azure Storage Account connection string")
    BLOB_CV_CONTAINER: str = Field(default="referral-cvs", description="Blob container for CV uploads")
    BLOB_DATA_CONTAINER: str = Field(default="referral-data", description="Blob container for Excel workbook")

    # Storage Mock Directory (used when STORAGE_TYPE == 'mock')
    LOCAL_STORAGE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "mock_storage")

    # Security & Upload Validation
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx"]
    ALLOWED_CONTENT_TYPES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]

    # CV Intelligence & HR Suggestions (Isolated & Local-Only)
    CV_INTELLIGENCE_ENABLED: bool = Field(default=False, description="Enable CV Intelligence and HR Suggestions")
    CV_INTELLIGENCE_DB_PATH: str = Field(
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cv_intelligence.db"),
        description="Path to separate SQLite database for CV Intelligence",
    )
    CV_LLM_PROVIDER: str = Field(default="gemini", description="LLM provider")
    CV_LLM_MODEL: str = Field(default="gemini-3.5-flash-lite", description="LLM model identifier")
    GEMINI_API_KEY: str = Field(default="", description="Gemini API Key")
    CV_STORAGE_TYPE: str = Field(
        default="local",
        description="'blob' to sync cv_intelligence.db with Azure Blob Storage, 'local' for local SQLite file only",
    )
    BLOB_CV_INTELLIGENCE_NAME: str = Field(
        default="cv_intelligence.db",
        description="Blob name for cv_intelligence.db in BLOB_DATA_CONTAINER",
    )

    # Jev Relevance Pre-Screen (Additive & Non-blocking)
    TYPESAFE_API_KEY: str = Field(default="", description="TypeSafe AI API key for Jev relevance checks")
    CV_RELEVANCE_CHECK_ENABLED: bool = Field(
        default=False,
        description="Enable Jev pre-screen relevance check at referral submission",
    )
    CV_RELEVANCE_BLOCK_THRESHOLD: float = Field(
        default=0.30,
        description="Jev score below this blocks submission (only if CV_RELEVANCE_BLOCK_ENABLED=True)",
    )
    CV_RELEVANCE_BLOCK_ENABLED: bool = Field(
        default=False,
        description="If True, block submissions below threshold; if False, log warning only",
    )
    CV_RELEVANCE_WARN_THRESHOLD: float = Field(
        default=0.45,
        description="Jev score below this logs a low-relevance warning",
    )

    # Historical Referral Suggestions (Isolated & Local-Only)
    HISTORICAL_REFERRAL_SEARCH_ENABLED: bool = Field(
        default=False,
        description="Enable Historical Referral Suggestions RAG search over archived candidates",
    )
    HISTORICAL_MATCH_THRESHOLD: float = Field(
        default=0.45,
        description="Minimum similarity/relevance threshold for historical candidate suggestions",
    )
    HISTORICAL_RAG_DB_PATH: str = Field(
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "historical_rag.db"),
        description="Path to separate SQLite database/index for Historical RAG embeddings",
    )

    # Duplicate Referral Detection Window (6 Months)
    REFERRAL_DUPLICATE_WINDOW_DAYS: int = Field(
        default=180,
        description="Window in days within which a prior referral is considered a duplicate. Referrals submitted older than this window (e.g. 6 months / 180 days) are considered new submissions without duplication warning.",
    )

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    CORS_ORIGINS_EXTRA: str = Field(default="", description="Comma-separated extra CORS origins for production (appended to CORS_ORIGINS)")
    CORS_ORIGIN_REGEX: Optional[str] = Field(default=None, description="Optional regex for allowed CORS origins (disabled in production unless explicitly configured)")

    @property
    def all_cors_origins(self) -> List[str]:
        """Merged CORS origins: defaults + extra production origins from env."""
        extra = []
        if self.CORS_ORIGINS_EXTRA:
            raw = self.CORS_ORIGINS_EXTRA.strip()
            if raw.startswith("["):
                extra = json.loads(raw)
            else:
                extra = [o.strip() for o in raw.split(",") if o.strip()]
        return list(set(self.CORS_ORIGINS + extra))

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")


settings = Settings()
