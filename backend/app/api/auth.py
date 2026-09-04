from fastapi import APIRouter, Depends
from app.config import settings
from app.models.user import User
from app.schemas.user import UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Return the authenticated user profile and permissions"""
    return current_user


@router.get("/config")
async def get_auth_config():
    """Return public Microsoft Entra ID authentication parameters for the frontend client"""
    return {
        "tenant_id": settings.AZURE_TENANT_ID,
        "client_id": settings.AZURE_CLIENT_ID,
        "authority": settings.AZURE_AUTHORITY,
        "dev_mode": settings.DEV_MODE,
    }
