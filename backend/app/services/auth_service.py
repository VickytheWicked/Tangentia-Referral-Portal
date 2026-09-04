import logging
import httpx
from typing import Dict, Any, Optional
from jose import jwt, jwk
from jose.exceptions import JWTError, ExpiredSignatureError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

# Cached JWKS keys
_jwks_cache: Optional[Dict[str, Any]] = None


async def get_entra_jwks() -> Dict[str, Any]:
    """Fetch and cache Microsoft Entra ID public signing keys (JWKS)"""
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.AZURE_JWKS_URL)
            if response.status_code == 200:
                _jwks_cache = response.json()
                return _jwks_cache
            else:
                logger.error(f"Failed to fetch JWKS from Entra ID: {response.status_code}")
    except Exception as e:
        logger.error(f"Error connecting to Entra ID JWKS endpoint: {e}")

    return {"keys": []}


async def verify_microsoft_token(token: str) -> Dict[str, Any]:
    """
    Verify Microsoft Entra ID access token or ID token.
    Extracts authenticated user identity: oid, email, name, roles/groups.
    """
    # Development Mode bypass / simulated tokens for local testing
    if settings.DEV_MODE:
        if token == "dev-employee-token" or token.startswith("dev-employee"):
            return {
                "oid": "entra-user-dev-employee-001",
                "email": "employee@tangentia.com",
                "name": "Vansh Rupesh (Employee)",
                "roles": [UserRole.EMPLOYEE.value],
                "groups": [],
            }
        elif token == "dev-hr-token" or token.startswith("dev-hr"):
            return {
                "oid": "entra-user-dev-hr-001",
                "email": "hr.lead@tangentia.com",
                "name": "Marcus Vance (HR Admin)",
                "roles": [UserRole.HR_ADMIN.value],
                "groups": [settings.AZURE_HR_GROUP_ID] if settings.AZURE_HR_GROUP_ID else ["hr-admins"],
            }

    # Production Entra ID Verification
    try:
        # Decode header without verification to get Key ID (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token header: Missing 'kid'",
            )

        jwks = await get_entra_jwks()
        key_dict = next((k for k in jwks.get("keys", []) if k["kid"] == kid), None)
        if not key_dict:
            # Refresh JWKS cache and retry
            global _jwks_cache
            _jwks_cache = None
            jwks = await get_entra_jwks()
            key_dict = next((k for k in jwks.get("keys", []) if k["kid"] == kid), None)

        if not key_dict:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token signing key not found in Entra ID JWKS.",
            )

        # Validate token against RSA public key
        public_key = jwk.construct(key_dict)
        decoded = jwt.decode(
            token,
            public_key.to_pem().decode("utf-8"),
            algorithms=["RS256"],
            audience=settings.AZURE_CLIENT_ID if settings.AZURE_CLIENT_ID else None,
            options={"verify_aud": bool(settings.AZURE_CLIENT_ID)},
        )

        # Extract normalized claims
        oid = decoded.get("oid") or decoded.get("sub")
        email = decoded.get("preferred_username") or decoded.get("email") or decoded.get("upn")
        name = decoded.get("name") or email or "Company Employee"
        roles = decoded.get("roles", [])
        groups = decoded.get("groups", [])

        if not oid or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing required user identity claims (oid/email).",
            )

        return {
            "oid": oid,
            "email": email.lower().strip(),
            "name": name,
            "roles": roles,
            "groups": groups,
        }

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please sign in again.",
        )
    except JWTError as e:
        logger.warning(f"JWT verification failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
        )


def sync_user_session(db: Session, claims: Dict[str, Any], explicit_role_override: Optional[str] = None) -> User:
    """
    Ensure user identity exists in the database and synchronize their Entra ID attributes and role.
    """
    oid = claims["oid"]
    email = claims["email"]
    name = claims["name"]
    roles = claims.get("roles", [])
    groups = claims.get("groups", [])

    # Find existing user by entra_user_id or email
    user = db.query(User).filter(
        (User.entra_user_id == oid) | (User.email == email)
    ).first()

    # Determine role
    is_hr = False
    if explicit_role_override:
        is_hr = (explicit_role_override == UserRole.HR_ADMIN.value)
    elif "HR_Admin" in roles or "hr_admin" in roles or UserRole.HR_ADMIN.value in roles:
        is_hr = True
    elif settings.AZURE_HR_GROUP_ID and settings.AZURE_HR_GROUP_ID in groups:
        is_hr = True
    elif "hr-admins" in groups:
        is_hr = True

    determined_role = UserRole.HR_ADMIN.value if is_hr else UserRole.EMPLOYEE.value

    if not user:
        user = User(
            entra_user_id=oid,
            name=name,
            email=email,
            role=determined_role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update user attributes if changed
        updated = False
        if user.entra_user_id != oid:
            user.entra_user_id = oid
            updated = True
        if user.name != name:
            user.name = name
            updated = True
        # If user is marked HR in Entra, upgrade in DB; otherwise retain existing DB role if assigned by admin
        if is_hr and user.role != UserRole.HR_ADMIN.value:
            user.role = UserRole.HR_ADMIN.value
            updated = True
        elif explicit_role_override and user.role != explicit_role_override:
            user.role = explicit_role_override
            updated = True
            
        if updated:
            db.commit()
            db.refresh(user)

    return user
