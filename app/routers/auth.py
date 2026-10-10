from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_optional, get_token_from_request, verify_csrf
from app.models import User, UserSession
from app.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    AdminLoginRequest,
    UserResponse,
    AuthStatusResponse,
    MessageResponse,
)
from app.security import (
    set_auth_cookies,
    clear_auth_cookies,
    generate_secure_token,
)
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account"
)
def register(
    payload: UserRegisterRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Registers a new customer. Customer accounts can never be created as admin.
    Sets session cookies immediately upon successful registration.
    """
    user = auth_service.register_customer(
        db=db,
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password
    )

    # Establish session
    session_token, csrf_token = auth_service.create_user_session(db, user)
    set_auth_cookies(response, session_token, csrf_token)

    return user


@router.post(
    "/login",
    response_model=UserResponse,
    summary="Authenticate a customer"
)
def login(
    payload: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticates a customer using their email and password.
    Returns HttpOnly session cookie on success.
    """
    user = auth_service.authenticate_customer(
        db=db,
        email=payload.email,
        password=payload.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    session_token, csrf_token = auth_service.create_user_session(db, user)
    set_auth_cookies(response, session_token, csrf_token)

    return user


@router.post(
    "/admin/login",
    response_model=UserResponse,
    summary="Authenticate an administrator"
)
def admin_login(
    payload: AdminLoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticates an administrator using configured admin credentials or database records.
    Returns HttpOnly session cookie with admin privileges on success.
    """
    admin_user = auth_service.authenticate_admin(
        db=db,
        username_or_email=payload.username_or_email,
        password=payload.password
    )
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrator credentials."
        )

    session_token, csrf_token = auth_service.create_user_session(db, admin_user)
    set_auth_cookies(response, session_token, csrf_token)

    return admin_user


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="End current session"
)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Ends the current user session by deleting the database session record
    and clearing all authentication cookies.
    """
    token = get_token_from_request(request)
    if token:
        auth_service.invalidate_session(db, token)

    clear_auth_cookies(response)
    return MessageResponse(message="Successfully logged out.")


@router.get(
    "/me",
    response_model=AuthStatusResponse,
    summary="Get current user status"
)
def get_current_user_status(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Returns the currently logged-in user's profile and active CSRF token.
    Safe endpoint that works for both authenticated and anonymous visitors.
    """
    if not current_user:
        return AuthStatusResponse(
            authenticated=False,
            user=None,
            csrf_token=None
        )

    # Fetch CSRF token for the current session
    token = get_token_from_request(request)
    csrf_token = None
    if token:
        session_rec = db.query(UserSession).filter(UserSession.session_token == token).first()
        if session_rec:
            csrf_token = session_rec.csrf_token

    return AuthStatusResponse(
        authenticated=True,
        user=UserResponse.model_validate(current_user),
        csrf_token=csrf_token
    )
