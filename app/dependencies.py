from datetime import datetime, timezone
from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import get_db
from app.models import User, UserSession

settings = get_settings()


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extracts session token from HttpOnly cookie or Authorization Bearer header.
    """
    # First check HttpOnly cookie
    cookie_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    # Fallback to Authorization: Bearer <token> (useful for Swagger UI / API clients)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()

    return None


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Returns the authenticated User if valid session exists, otherwise None.
    Does not raise HTTPException.
    """
    token = get_token_from_request(request)
    if not token:
        return None

    session_record = db.query(UserSession).filter(UserSession.session_token == token).first()
    if not session_record:
        return None

    # Check expiration
    now = datetime.now(timezone.utc)
    # Ensure session_record.expires_at is timezone-aware
    expires_at = session_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        # Session expired - remove it
        db.delete(session_record)
        db.commit()
        return None

    return session_record.user


def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """
    Requires an authenticated user (Customer or Admin). Raises 401 if unauthenticated.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in."
        )
    return current_user


def get_current_customer(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Requires an authenticated customer.
    """
    return current_user


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Requires an authenticated admin user. Raises 403 if user is not an admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required."
        )
    return current_user


def verify_csrf(request: Request, db: Session = Depends(get_db)) -> None:
    """
    Validates CSRF token for state-changing HTTP methods when authenticated via cookies.
    """
    # Safe methods do not require CSRF token
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    # Check if request has an active session cookie
    cookie_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not cookie_token:
        # Unauthenticated request or using pure non-cookie API header
        return

    # If cookie authenticated, CSRF token is mandatory
    submitted_csrf = request.headers.get("X-CSRF-Token")
    csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)

    if not submitted_csrf:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing in request headers."
        )

    # Validate against csrf cookie (double-submit)
    if csrf_cookie and submitted_csrf == csrf_cookie:
        return

    # Or validate against active session in DB
    session_record = db.query(UserSession).filter(UserSession.session_token == cookie_token).first()
    if session_record and session_record.csrf_token == submitted_csrf:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid CSRF token."
    )
