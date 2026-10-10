import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from fastapi import Response
from app.config import get_settings

settings = get_settings()
_ph = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Hashes a plain text password using Argon2.
    """
    return _ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against an Argon2 hash.
    Returns True if valid, False otherwise.
    """
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    except Exception:
        return False


def generate_secure_token(nbytes: int = 32) -> str:
    """
    Generates a cryptographically strong URL-safe random string.
    """
    return secrets.token_urlsafe(nbytes)


def calculate_session_expiry(hours: Optional[int] = None) -> datetime:
    """
    Calculates UTC expiration time for a session.
    """
    h = hours if hours is not None else settings.SESSION_EXPIRE_HOURS
    return datetime.now(timezone.utc) + timedelta(hours=h)


def set_auth_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    """
    Sets secure HttpOnly session cookie and accessible CSRF cookie.
    """
    max_age = settings.SESSION_EXPIRE_HOURS * 3600

    # HttpOnly session cookie - inaccessible to JavaScript
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        max_age=max_age,
        expires=max_age,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE
    )

    # CSRF cookie - readable by frontend JavaScript for double-submit header
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=max_age,
        expires=max_age,
        path="/",
        httponly=False,
        samesite="lax",
        secure=settings.COOKIE_SECURE
    )


def clear_auth_cookies(response: Response) -> None:
    """
    Clears session and CSRF cookies on logout.
    """
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE
    )
    response.delete_cookie(
        key=settings.CSRF_COOKIE_NAME,
        path="/",
        httponly=False,
        samesite="lax",
        secure=settings.COOKIE_SECURE
    )
