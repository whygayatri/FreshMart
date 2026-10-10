from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user_optional, get_token_from_request
from app.models import User, UserSession
from app.schemas import VALID_CATEGORIES
from app.security import generate_secure_token
from app.services import product_service, cart_service, order_service

settings = get_settings()
templates = Jinja2Templates(directory="templates")

router = APIRouter(include_in_schema=False)


def prepare_template_context(
    request: Request,
    response: Response,
    current_user: Optional[User],
    db: Session,
    extra: Optional[dict] = None
) -> dict:
    """
    Builds the base context passed to all Jinja2 templates, ensuring CSRF tokens
    and user session information are always available.
    """
    # Determine CSRF token
    csrf_token = request.cookies.get(settings.CSRF_COOKIE_NAME)
    if not csrf_token:
        # Check active session in DB if user is authenticated
        token = get_token_from_request(request)
        if token:
            session_rec = db.query(UserSession).filter(UserSession.session_token == token).first()
            if session_rec:
                csrf_token = session_rec.csrf_token

    if not csrf_token:
        csrf_token = generate_secure_token(32)
        response.set_cookie(
            key=settings.CSRF_COOKIE_NAME,
            value=csrf_token,
            path="/",
            httponly=False,
            samesite="lax",
            secure=settings.COOKIE_SECURE
        )

    # Cart count if logged in
    cart_count = 0
    if current_user and current_user.role == "customer":
        _, cart_count, _ = cart_service.get_user_cart(db, current_user.id)

    context = {
        "request": request,
        "app_name": settings.APP_NAME,
        "user": current_user,
        "csrf_token": csrf_token,
        "cart_count": cart_count,
        "categories": VALID_CATEGORIES
    }

    if extra:
        context.update(extra)

    return context


@router.get("/")
def home_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Storefront Homepage: Displays hero banner, categories, product catalog, search bar.
    """
    response = Response()
    # Preload initial products for server-side rendering
    products, total = product_service.list_products(db=db, limit=36)

    context = prepare_template_context(
        request=request,
        response=response,
        current_user=current_user,
        db=db,
        extra={
            "products": products,
            "total_products": total,
            "active_category": "All"
        }
    )
    rendered = templates.TemplateResponse(request=request, name="index.html", context=context)
    # Copy any cookies set during preparation
    for cookie_header in response.raw_headers:
        if cookie_header[0].lower() == b"set-cookie":
            rendered.raw_headers.append(cookie_header)
    return rendered


@router.get("/login")
def login_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Customer Login Page. Redirects to homepage if already authenticated.
    """
    if current_user:
        if current_user.is_admin():
            return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    response = Response()
    context = prepare_template_context(request, response, current_user, db)
    rendered = templates.TemplateResponse(request=request, name="login.html", context=context)
    for cookie_header in response.raw_headers:
        if cookie_header[0].lower() == b"set-cookie":
            rendered.raw_headers.append(cookie_header)
    return rendered


@router.get("/register")
def register_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Customer Registration Page. Redirects if already authenticated.
    """
    if current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    response = Response()
    context = prepare_template_context(request, response, current_user, db)
    rendered = templates.TemplateResponse(request=request, name="register.html", context=context)
    for cookie_header in response.raw_headers:
        if cookie_header[0].lower() == b"set-cookie":
            rendered.raw_headers.append(cookie_header)
    return rendered


@router.get("/cart")
def cart_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Shopping Cart Page. Requires customer authentication.
    """
    if not current_user:
        return RedirectResponse(url="/login?next=/cart", status_code=status.HTTP_302_FOUND)

    response = Response()
    items, total_items, total_amount = cart_service.get_user_cart(db, current_user.id)

    context = prepare_template_context(
        request=request,
        response=response,
        current_user=current_user,
        db=db,
        extra={
            "cart_items": items,
            "total_items": total_items,
            "total_amount": total_amount
        }
    )
    rendered = templates.TemplateResponse(request=request, name="cart.html", context=context)
    for cookie_header in response.raw_headers:
        if cookie_header[0].lower() == b"set-cookie":
            rendered.raw_headers.append(cookie_header)
    return rendered


@router.get("/checkout")
def checkout_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Checkout Page. Requires customer authentication and non-empty cart.
    """
    if not current_user:
        return RedirectResponse(url="/login?next=/checkout", status_code=status.HTTP_302_FOUND)

    response = Response()
    items, total_items, total_amount = cart_service.get_user_cart(db, current_user.id)
    if not items:
        return RedirectResponse(url="/cart", status_code=status.HTTP_302_FOUND)

    context = prepare_template_context(
        request=request,
        response=response,
        current_user=current_user,
        db=db,
        extra={
            "cart_items": items,
            "total_items": total_items,
            "total_amount": total_amount
        }
    )
    rendered = templates.TemplateResponse(request=request, name="checkout.html", context=context)
    for cookie_header in response.raw_headers:
        if cookie_header[0].lower() == b"set-cookie":
            rendered.raw_headers.append(cookie_header)
    return rendered


@router.get("/orders")
def orders_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Customer Order History Page.
    """
    if not current_user:
        return RedirectResponse(url="/login?next=/orders", status_code=status.HTTP_302_FOUND)

    response = Response()
    user_orders = order_service.get_user_orders(db, current_user.id)

    context = prepare_template_context(
        request=request,
        response=response,
        current_user=current_user,
        db=db,
        extra={
            "orders": user_orders
        }
    )
    rendered = templates.TemplateResponse(request=request, name="orders.html", context=context)
    for cookie_header in response.raw_headers:
        if cookie_header[0].lower() == b"set-cookie":
            rendered.raw_headers.append(cookie_header)
    return rendered


@router.get("/order-confirmation")
def order_confirmation_page(
    request: Request,
    order_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Order Confirmation Page after successful checkout.
    """
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    response = Response()
    order = order_service.get_order_by_id(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
        is_admin=current_user.is_admin()
    )
    if not order:
        return RedirectResponse(url="/orders", status_code=status.HTTP_302_FOUND)

    context = prepare_template_context(
        request=request,
        response=response,
        current_user=current_user,
        db=db,
        extra={
            "order": order
        }
    )
    rendered = templates.TemplateResponse(request=request, name="order_confirmation.html", context=context)
    for cookie_header in response.raw_headers:
        if cookie_header[0].lower() == b"set-cookie":
            rendered.raw_headers.append(cookie_header)
    return rendered


@router.get("/admin/login")
def admin_login_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Dedicated Admin Login Page.
    """
    if current_user and current_user.is_admin():
        return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_302_FOUND)

    response = Response()
    context = prepare_template_context(request, response, current_user, db)
    rendered = templates.TemplateResponse(request=request, name="admin_login.html", context=context)
    for cookie_header in response.raw_headers:
        if cookie_header[0].lower() == b"set-cookie":
            rendered.raw_headers.append(cookie_header)
    return rendered


@router.get("/admin/dashboard")
def admin_dashboard_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Admin Inventory Management & Business Analytics Dashboard.
    Requires authenticated administrator session.
    """
    if not current_user or not current_user.is_admin():
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

    response = Response()
    stats = order_service.get_admin_dashboard_stats(db)
    products, _ = product_service.list_products(db=db, limit=200)

    context = prepare_template_context(
        request=request,
        response=response,
        current_user=current_user,
        db=db,
        extra={
            "stats": stats,
            "products": products
        }
    )
    rendered = templates.TemplateResponse(request=request, name="admin_dashboard.html", context=context)
    for cookie_header in response.raw_headers:
        if cookie_header[0].lower() == b"set-cookie":
            rendered.raw_headers.append(cookie_header)
    return rendered
