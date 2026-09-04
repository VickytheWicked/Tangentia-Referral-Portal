from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.user import User, UserRole
from app.services.auth_service import verify_microsoft_token, sync_user_session

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_dev_role: Optional[str] = Header(None, alias="X-Dev-Role"),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate Microsoft Entra ID token and retrieve the authenticated user record.
    Rejects any unauthenticated or unauthorized access.
    """
    token = None
    if credentials:
        token = credentials.credentials

    # Fallback to dev mode default token if none provided in dev mode
    if not token:
        if settings.DEV_MODE:
            # Check dev role requested
            if x_dev_role == "hr_admin":
                token = "dev-hr-token"
            else:
                token = "dev-employee-token"
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please sign in with your corporate Microsoft account.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    claims = await verify_microsoft_token(token)
    
    # Handle dev role override if DEV_MODE is enabled
    role_override = None
    if settings.DEV_MODE and x_dev_role in [UserRole.EMPLOYEE.value, UserRole.HR_ADMIN.value]:
        role_override = x_dev_role

    user = sync_user_session(db, claims, explicit_role_override=role_override)
    return user


async def require_hr_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensure the authenticated user holds the HR_ADMIN role.
    Raises 403 Forbidden if the user is a standard employee.
    """
    if current_user.role != UserRole.HR_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This action requires HR / Administrator privileges.",
        )
    return current_user
