from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Order, OrderItem, CartItem, Product, User
from app.schemas import AdminDashboardStats


def create_order_from_cart(db: Session, user_id: int) -> Order:
    """
    Creates an order from the user's cart in a transactional manner:
    1. Validates that the cart is not empty.
    2. Checks real-time stock and prices.
    3. Decrements inventory quantities.
    4. Creates Order and OrderItem records with immutable price snapshots.
    5. Clears the customer's cart.
    Rolls back automatically on failure.
    """
    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your shopping cart is empty. Please add items before checking out."
        )

    try:
        total_amount = Decimal("0.00")
        order_items_to_create: List[OrderItem] = []

        for item in cart_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A product in your cart is no longer available."
                )

            if product.stock_quantity < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}, in your cart: {item.quantity}."
                )

            # Reduce stock
            product.stock_quantity -= item.quantity

            unit_price = Decimal(str(product.price))
            line_subtotal = unit_price * item.quantity
            total_amount += line_subtotal

            order_item = OrderItem(
                product_id=product.id,
                product_name=product.name,
                unit_price=unit_price,
                quantity=item.quantity,
                line_subtotal=line_subtotal
            )
            order_items_to_create.append(order_item)

        # Create master Order
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            order_status="completed"
        )
        db.add(order)
        db.flush()  # Allocates order.id

        # Associate and save OrderItems
        for oi in order_items_to_create:
            oi.order_id = order.id
            db.add(oi)

        # Clear cart for the user
        db.query(CartItem).filter(CartItem.user_id == user_id).delete()

        db.commit()
        db.refresh(order)
        return order

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process order. Please try again."
        ) from exc


def get_user_orders(db: Session, user_id: int) -> List[Order]:
    """
    Retrieves all past orders for a specific customer, sorted newest first.
    """
    return db.query(Order).filter(
        Order.user_id == user_id
    ).order_by(Order.created_at.desc()).all()


def get_order_by_id(db: Session, order_id: int, user_id: int, is_admin: bool = False) -> Optional[Order]:
    """
    Retrieves an order by its ID.
    Enforces authorization: customers can only view their own orders; admins can view any.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return None

    if not is_admin and order.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this order."
        )

    return order


def get_admin_dashboard_stats(db: Session) -> AdminDashboardStats:
    """
    Calculates aggregated statistics for the admin dashboard.
    """
    total_products = db.query(Product).count()
    total_customers = db.query(User).filter(User.role == "customer").count()
    total_orders = db.query(Order).count()

    raw_revenue = db.query(func.sum(Order.total_amount)).scalar()
    total_revenue = Decimal(str(raw_revenue)) if raw_revenue is not None else Decimal("0.00")

    # Count products with low stock (5 or fewer items remaining)
    low_stock_count = db.query(Product).filter(Product.stock_quantity <= 5).count()

    return AdminDashboardStats(
        total_products=total_products,
        total_customers=total_customers,
        total_orders=total_orders,
        total_revenue=total_revenue,
        low_stock_count=low_stock_count
    )
