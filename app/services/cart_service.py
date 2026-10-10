from decimal import Decimal
from typing import List, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import CartItem, Product
from app.schemas import CartItemResponse


def get_user_cart(db: Session, user_id: int) -> Tuple[List[CartItemResponse], int, Decimal]:
    """
    Retrieves all cart items for a given user, calculating current prices and line totals.
    Silently cleans up any cart items where the underlying product no longer exists.
    """
    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    cleaned_items: List[CartItemResponse] = []
    total_amount = Decimal("0.00")
    total_items = 0

    items_to_delete = []

    for item in cart_items:
        product = item.product
        if not product:
            items_to_delete.append(item)
            continue

        unit_price = Decimal(str(product.price))
        line_subtotal = unit_price * item.quantity
        total_amount += line_subtotal
        total_items += item.quantity

        cleaned_items.append(
            CartItemResponse(
                id=item.id,
                product_id=product.id,
                product_name=product.name,
                category=product.category,
                unit_price=unit_price,
                image_url=product.image_url,
                quantity=item.quantity,
                stock_quantity=product.stock_quantity,
                line_subtotal=line_subtotal
            )
        )

    if items_to_delete:
        for itm in items_to_delete:
            db.delete(itm)
        db.commit()

    return cleaned_items, total_items, total_amount


def add_to_cart(db: Session, user_id: int, product_id: int, quantity: int = 1) -> CartItem:
    """
    Adds a product to the user's cart or increments quantity if already present.
    Enforces available stock limits.
    """
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than zero."
        )

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )

    if product.stock_quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{product.name}' is currently out of stock."
        )

    # Check if item is already in user's cart
    existing_item = db.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.product_id == product_id
    ).first()

    if existing_item:
        new_quantity = existing_item.quantity + quantity
        if new_quantity > product.stock_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add {quantity} more. Stock limit reached ({product.stock_quantity} available, {existing_item.quantity} already in cart)."
            )
        existing_item.quantity = new_quantity
        db.commit()
        db.refresh(existing_item)
        return existing_item

    # New cart item
    if quantity > product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add {quantity} items. Only {product.stock_quantity} available in stock."
        )

    new_item = CartItem(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


def update_cart_item_quantity(db: Session, user_id: int, item_id: int, quantity: int) -> None:
    """
    Updates the quantity of a specific cart item.
    If quantity <= 0, the item is removed.
    """
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found."
        )

    if item.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this cart item."
        )

    if quantity <= 0:
        db.delete(item)
        db.commit()
        return

    product = item.product
    if not product:
        db.delete(item)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product no longer available."
        )

    if quantity > product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested quantity {quantity} exceeds available stock of {product.stock_quantity}."
        )

    item.quantity = quantity
    db.commit()


def remove_cart_item(db: Session, user_id: int, item_id: int) -> None:
    """
    Removes an item from the customer's cart.
    """
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found."
        )

    if item.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this cart item."
        )

    db.delete(item)
    db.commit()


def clear_cart(db: Session, user_id: int) -> None:
    """
    Clears all items in a user's cart.
    """
    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    db.commit()
