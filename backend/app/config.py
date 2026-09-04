import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "Tangentia Employee Referral Portal"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    DEV_MODE: bool = True  # Allows local dev testing with simulated Entra user and local mock SharePoint storage
    
    # API Prefix
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = "sqlite:///./referrals.db"  # SQLite default for local zero-config testing; set to postgresql://user:pass@host:5432/db in production
    
    # Microsoft Entra ID (Azure AD)
    AZURE_TENANT_ID: str = Field(default="common", description="Azure AD Tenant ID")
    AZURE_CLIENT_ID: str = Field(default="", description="Azure AD App Registration Client ID")
    AZURE_CLIENT_SECRET: str = Field(default="", description="Azure AD Client Secret")
    AZURE_HR_GROUP_ID: str = Field(default="", description="Entra ID Security Group ID for HR Admins")
    
    @property
    def AZURE_AUTHORITY(self) -> str:
        return f"https://login.microsoftonline.com/{self.AZURE_TENANT_ID}"

    @property
    def AZURE_JWKS_URL(self) -> str:
        return f"https://login.microsoftonline.com/{self.AZURE_TENANT_ID}/discovery/v2.0/keys"

    # Microsoft SharePoint Online
    SHAREPOINT_STORAGE_TYPE: str = Field(default="mock", description="'graph' for real Microsoft Graph, 'mock' for local development")
    SHAREPOINT_SITE_ID: str = Field(default="", description="SharePoint Site ID (tenant.sharepoint.com,site-id,web-id)")
    SHAREPOINT_DRIVE_ID: str = Field(default="", description="SharePoint Document Library Drive ID")
    SHAREPOINT_ROOT_FOLDER: str = Field(default="Referral-CVs", description="Root folder in document library for CVs")
    
    # Storage Mock Directory (used when SHAREPOINT_STORAGE_TYPE == 'mock')
    LOCAL_STORAGE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "mock_sharepoint")

    # Security & Upload Validation
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx"]
    ALLOWED_CONTENT_TYPES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")


settings = Settings()
