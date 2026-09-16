import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, UserRole
from app.services.excel import get_excel_service

logger = logging.getLogger(__name__)

JWT_SECRET_KEY = getattr(settings, "JWT_SECRET_KEY", "tangentia-portal-super-secret-jwt-key-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token for authenticated HR sessions"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=JWT_EXPIRATION_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token"""
    # Development / test tokens bypass
    if settings.DEV_MODE:
        if token == "dev-hr-token" or token.startswith("dev-hr"):
            return {
                "sub": "user-hr-001",
                "email": "hr.lead@tangentia.com",
                "name": "Marcus Vance",
                "role": UserRole.HR_ADMIN.value,
            }
        elif token == "dev-employee-token" or token.startswith("dev-employee"):
            return {
                "sub": "user-emp-001",
                "email": "employee@tangentia.com",
                "name": "Vansh Rupesh (Employee)",
                "role": UserRole.EMPLOYEE.value,
            }

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_hr_user(db: Session, email: str, password: str) -> Tuple[User, str]:
    """
    Authenticate an HR user against the Tangentia_Referrals.xlsx Users worksheet.
    - Validates domain ends with @tangentia.com
    - Confirms HR role
    - Checks plain-text password from Excel
    - Generates and returns (User, JWT token)
    """
    clean_email = email.strip().lower()

    # 1. Enforce @tangentia.com domain
    if not clean_email.endswith("@tangentia.com"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication restricted. Only @tangentia.com corporate email addresses are permitted.",
        )

    # 2. Look up user in Excel workbook
    excel_svc = get_excel_service()
    excel_user = None
    try:
        excel_user = excel_svc.get_user_by_email(clean_email)
    except Exception as e:
        logger.warning(f"Could not read user from Excel: {e}")

    # Fallback to in-memory / database user
    db_user = db.query(User).filter(User.email.ilike(clean_email)).first()

    target_name = "HR Administrator"
    target_role = None
    target_dept = "Human Resources"
    target_password = None
    target_id = None

    if excel_user:
        target_name = str(excel_user.get("Name") or "HR Administrator")
        target_role = str(excel_user.get("Role") or "").strip().lower()
        target_dept = str(excel_user.get("Department") or "Human Resources")
        target_password = str(excel_user.get("Password") or "")
        target_id = str(excel_user.get("User ID") or "")
    elif db_user:
        target_name = db_user.name
        target_role = db_user.role.lower() if db_user.role else ""
        target_dept = db_user.department or "Human Resources"
        target_password = db_user.password or ""
        target_id = db_user.id
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found. Please verify your email is configured in the Users sheet of Tangentia_Referrals.xlsx.",
        )

    # 3. Restrict to HR role only
    if target_role not in [UserRole.HR_ADMIN.value, "hr", "hr_admin", "hr admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to HR administrators only. Employees do not require a login.",
        )

    # 4. Verify password
    if not target_password or target_password.strip() != password.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials configured in the Excel file.",
        )

    # 5. Sync to database
    if not db_user:
        db_user = User(
            id=target_id or f"user-hr-{clean_email.split('@')[0]}",
            name=target_name,
            email=clean_email,
            password=target_password,
            role=UserRole.HR_ADMIN.value,
            department=target_dept,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    else:
        updated = False
        if db_user.role != UserRole.HR_ADMIN.value:
            db_user.role = UserRole.HR_ADMIN.value
            updated = True
        if target_password and db_user.password != target_password:
            db_user.password = target_password
            updated = True
        if updated:
            db.commit()
            db.refresh(db_user)

    # 6. Issue access token
    token = create_access_token({
        "sub": db_user.id,
        "email": db_user.email,
        "name": db_user.name,
        "role": db_user.role,
    })

    return db_user, token
