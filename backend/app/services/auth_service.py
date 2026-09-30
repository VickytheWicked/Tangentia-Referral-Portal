import logging
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, UserRole
from app.services.excel import get_excel_service

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique random 16-byte salt."""
    salt = secrets.token_hex(16)
    iterations = 100_000
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${hash_bytes.hex()}"


def verify_password(plain_password: str, stored_password_or_hash: str) -> bool:
    """
    Verify a plain password against a stored PBKDF2 hash or legacy plaintext.
    Uses constant-time comparison to prevent timing attacks.
    """
    if not stored_password_or_hash or not plain_password:
        return False
    stored = stored_password_or_hash.strip()
    plain = plain_password.strip()

    if stored.startswith("pbkdf2_sha256$"):
        parts = stored.split("$")
        if len(parts) == 4:
            try:
                iterations = int(parts[1])
                salt = parts[2]
                expected_hash_hex = parts[3]
                computed = hashlib.pbkdf2_hmac(
                    "sha256",
                    plain.encode("utf-8"),
                    salt.encode("utf-8"),
                    iterations,
                ).hex()
                return hmac.compare_digest(computed, expected_hash_hex)
            except Exception:
                return False

    # Fallback constant-time comparison for legacy unhashed entries
    return hmac.compare_digest(plain.encode("utf-8"), stored.encode("utf-8"))


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token for authenticated HR sessions"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=JWT_EXPIRATION_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token"""
    # Development / test tokens bypass — strictly disallowed in production
    if settings.is_dev_token_allowed:
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
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[JWT_ALGORITHM])
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
            detail="User does not exist. Please verify your email address or contact your administrator.",
        )

    # 3. Restrict to HR role only
    if target_role not in [UserRole.HR_ADMIN.value, "hr", "hr_admin", "hr admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to HR administrators only. Employees do not require a login.",
        )

    # 4. Verify password securely using constant-time hash comparison
    if not verify_password(password, target_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password incorrect. Please check your password and try again.",
        )

    # Compute secure hash for database storage (never store plaintext)
    secure_db_password = target_password if (target_password and target_password.startswith("pbkdf2_sha256$")) else hash_password(password)

    # 5. Sync to database
    if not db_user:
        db_user = User(
            id=target_id or f"user-hr-{clean_email.split('@')[0]}",
            name=target_name,
            email=clean_email,
            password=secure_db_password,
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
        if not db_user.password or not db_user.password.startswith("pbkdf2_sha256$") or not verify_password(password, db_user.password):
            db_user.password = secure_db_password
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
