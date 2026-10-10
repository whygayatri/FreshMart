from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import User, Order
from app.schemas import AdminDashboardStats, OrderResponse, OrderListResponse
from app.services import order_service

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])


@router.get(
    "/stats",
    response_model=AdminDashboardStats,
    summary="Get aggregated store metrics for admin dashboard"
)
def get_dashboard_stats(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Returns high-level business analytics:
    total products, registered customers, orders count, total revenue, and low stock count.
    """
    return order_service.get_admin_dashboard_stats(db)


@router.get(
    "/orders",
    response_model=OrderListResponse,
    summary="List all store orders across customers (Admin only)"
)
def list_all_store_orders(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Allows administrators to inspect all customer orders placed across the store.
    """
    all_orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return OrderListResponse(
        orders=[OrderResponse.model_validate(o) for o in all_orders],
        total=len(all_orders)
    )
