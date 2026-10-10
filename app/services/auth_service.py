from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import User, UserSession
from app.security import (
    hash_password,
    verify_password,
    generate_secure_token,
    calculate_session_expiry,
)

settings = get_settings()


def ensure_admin_user(db: Session) -> User:
    """
    Ensures that the default admin user exists in the database.
    Synchronizes credentials from environment if admin is not already present.
    """
    admin = db.query(User).filter(
        (User.role == "admin") | (User.email == settings.ADMIN_EMAIL.lower())
    ).first()

    if not admin:
        admin = User(
            full_name="Store Administrator",
            email=settings.ADMIN_EMAIL.lower(),
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    return admin


def register_customer(db: Session, full_name: str, email: str, password: str) -> User:
    """
    Registers a new customer account.
    Rejects duplicate email addresses.
    """
    clean_email = email.strip().lower()

    # Check for duplicate email
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )

    # Hash password securely with Argon2
    hashed = hash_password(password)

    new_user = User(
        full_name=full_name.strip(),
        email=clean_email,
        password_hash=hashed,
        role="customer"  # Customers can never self-register as admin
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_customer(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticates a customer by email and password.
    Returns user if credentials match, else None.
    """
    clean_email = email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()

    if not user:
        return None

    # Verify role is customer
    if user.role != "customer":
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def authenticate_admin(db: Session, username_or_email: str, password: str) -> Optional[User]:
    """
    Authenticates an administrator using configured admin credentials or database records.
    """
    clean_identifier = username_or_email.strip().lower()

    # 1. First check if matches env config admin username or admin email
    is_config_admin = (
        clean_identifier == settings.ADMIN_USERNAME.lower()
        or clean_identifier == settings.ADMIN_EMAIL.lower()
    )

    if is_config_admin and password == settings.ADMIN_PASSWORD:
        # Ensure admin exists in DB
        admin = ensure_admin_user(db)
        return admin

    # 2. Check DB for admin user record
    admin = db.query(User).filter(
        (User.email == clean_identifier) & (User.role == "admin")
    ).first()

    if admin and verify_password(password, admin.password_hash):
        return admin

    return None


def create_user_session(db: Session, user: User) -> Tuple[str, str]:
    """
    Creates a new user session in the database and returns (session_token, csrf_token).
    """
    session_token = generate_secure_token(32)
    csrf_token = generate_secure_token(32)
    expires_at = calculate_session_expiry()

    session_record = UserSession(
        session_token=session_token,
        csrf_token=csrf_token,
        user_id=user.id,
        expires_at=expires_at
    )

    db.add(session_record)
    db.commit()
    return session_token, csrf_token


def invalidate_session(db: Session, session_token: str) -> None:
    """
    Deletes the session record from the database to log out the user.
    """
    if not session_token:
        return
    db.query(UserSession).filter(UserSession.session_token == session_token).delete()
    db.commit()
