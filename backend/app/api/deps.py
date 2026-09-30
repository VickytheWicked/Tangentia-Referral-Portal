from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.user import User, UserRole
from app.services.auth_service import decode_access_token

security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Optionally retrieve the authenticated user from JWT Bearer token.
    Returns None if unauthenticated or token is invalid, allowing guest employee access.
    """
    if not credentials or not credentials.credentials:
        return None

    token = credentials.credentials
    try:
        claims = decode_access_token(token)
        user_id = claims.get("sub")
        email = claims.get("email")
        query = db.query(User)
        if user_id:
            user = query.filter(User.id == user_id).first()
            if user:
                return user
        if email:
            user = query.filter(User.email.ilike(email)).first()
            if user:
                return user
        return None
    except Exception:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_dev_role: Optional[str] = Header(None, alias="X-Dev-Role"),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate JWT access token and retrieve the authenticated user record.
    Rejects any unauthenticated access with 401 Unauthorized.
    """
    token = None
    if credentials:
        token = credentials.credentials

    # Test / Dev token fallback if explicitly provided (strictly disallowed in production)
    if not token and settings.is_dev_token_allowed and x_dev_role:
        token = "dev-hr-token" if x_dev_role == "hr_admin" else "dev-employee-token"

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in with your @tangentia.com HR account.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = decode_access_token(token)
    user_id = claims.get("sub")
    email = claims.get("email")

    user = None
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
    if not user and email:
        user = db.query(User).filter(User.email.ilike(email)).first()

    if not user:
        # Re-create in-memory user if present in claims
        user = User(
            id=user_id or "user-hr-001",
            name=claims.get("name", "HR Administrator"),
            email=email or "hr.lead@tangentia.com",
            role=claims.get("role", UserRole.HR_ADMIN.value),
            department="Human Resources",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


async def require_hr_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensure the authenticated user holds the HR_ADMIN role.
    Raises 403 Forbidden if the user is not an HR administrator.
    """
    if current_user.role != UserRole.HR_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This action requires HR / Administrator privileges.",
        )
    return current_user
