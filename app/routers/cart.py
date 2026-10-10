from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, verify_csrf
from app.models import User
from app.schemas import (
    CartResponse,
    CartItemAdd,
    CartItemUpdate,
    MessageResponse,
)
from app.services import cart_service

router = APIRouter(prefix="/api/cart", tags=["Shopping Cart"])


@router.get(
    "",
    response_model=CartResponse,
    summary="Retrieve the authenticated customer's shopping cart"
)
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all items currently in the authenticated customer's shopping cart,
    including real-time unit prices, line subtotals, and overall order total.
    """
    items, total_items, total_amount = cart_service.get_user_cart(db, current_user.id)
    return CartResponse(
        items=items,
        total_items=total_items,
        total_amount=total_amount
    )


@router.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a product to the shopping cart"
)
def add_to_cart(
    payload: CartItemAdd,
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db)
):
    """
    Adds a specified quantity of a product to the user's cart.
    If the product already exists in the cart, increments the existing quantity.
    """
    cart_service.add_to_cart(
        db=db,
        user_id=current_user.id,
        product_id=payload.product_id,
        quantity=payload.quantity
    )

    items, total_items, total_amount = cart_service.get_user_cart(db, current_user.id)
    return CartResponse(
        items=items,
        total_items=total_items,
        total_amount=total_amount
    )


@router.patch(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Update item quantity in shopping cart"
)
def update_cart_item(
    item_id: int,
    payload: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db)
):
    """
    Updates the quantity of a specific cart item.
    Enforces that the item belongs to the authenticated customer and does not exceed available stock.
    """
    cart_service.update_cart_item_quantity(
        db=db,
        user_id=current_user.id,
        item_id=item_id,
        quantity=payload.quantity
    )

    items, total_items, total_amount = cart_service.get_user_cart(db, current_user.id)
    return CartResponse(
        items=items,
        total_items=total_items,
        total_amount=total_amount
    )


@router.delete(
    "/items/{item_id}",
    response_model=MessageResponse,
    summary="Remove an item from the shopping cart"
)
def remove_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db)
):
    """
    Removes a specific item from the authenticated customer's shopping cart.
    """
    cart_service.remove_cart_item(
        db=db,
        user_id=current_user.id,
        item_id=item_id
    )
    return MessageResponse(message="Item removed from shopping cart.")
