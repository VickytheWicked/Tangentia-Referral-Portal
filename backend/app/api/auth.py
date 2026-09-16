from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, LoginRequest, LoginResponse
from app.api.deps import get_current_user
from app.services.auth_service import authenticate_hr_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def hr_login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate HR administrator using @tangentia.com email and password from Tangentia_Referrals.xlsx.
    Issues JWT token upon successful authentication.
    """
    user, token = authenticate_hr_user(
        db=db,
        email=payload.email,
        password=payload.password,
    )
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=user,
    )


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Return the authenticated user profile and permissions"""
    return current_user


@router.get("/config")
async def get_auth_config():
    """Return authentication parameters for frontend client"""
    return {
        "dev_mode": settings.DEV_MODE,
        "auth_domain": "@tangentia.com",
    }
