from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, verify_csrf
from app.models import User
from app.schemas import (
    OrderCreateRequest,
    OrderResponse,
    OrderListResponse,
)
from app.services import order_service

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an order from the current shopping cart"
)
def create_order(
    payload: OrderCreateRequest = None,
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db)
):
    """
    Executes a transactional checkout:
    - Verifies items exist in cart.
    - Validates inventory stock and current prices.
    - Decrements stock.
    - Stores immutable item snapshots in order.
    - Clears the cart.
    """
    order = order_service.create_order_from_cart(db=db, user_id=current_user.id)
    return order


@router.get(
    "",
    response_model=OrderListResponse,
    summary="Retrieve the authenticated customer's order history"
)
def list_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all previous grocery orders placed by the currently logged-in customer.
    Customers cannot see other users' orders.
    """
    orders = order_service.get_user_orders(db=db, user_id=current_user.id)
    return OrderListResponse(
        orders=[OrderResponse.model_validate(o) for o in orders],
        total=len(orders)
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Retrieve details for a specific order"
)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns full details and item snapshots for a specific order.
    Customers can only access their own orders; admins can view any order.
    """
    order = order_service.get_order_by_id(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
        is_admin=current_user.is_admin()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} was not found."
        )
    return order
