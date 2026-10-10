from math import ceil
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, verify_csrf
from app.models import User
from app.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    MessageResponse,
)
from app.services import product_service

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get(
    "",
    response_model=ProductListResponse,
    summary="List and search grocery products"
)
def list_products(
    search: Optional[str] = Query(None, description="Search products by name or description"),
    category: Optional[str] = Query(None, description="Filter products by category name"),
    sort_by: Optional[str] = Query(
        "newest",
        description="Sort ordering: newest, price_asc, price_desc, name_asc, name_desc"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Retrieves a paginated list of grocery products with optional keyword search and category filtering.
    """
    products, total = product_service.list_products(
        db=db,
        search=search,
        category=category,
        sort_by=sort_by,
        page=page,
        limit=limit
    )

    total_pages = ceil(total / limit) if total > 0 else 1

    return ProductListResponse(
        products=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get single product details"
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Returns full details for a single grocery product by its ID.
    """
    product = product_service.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} was not found."
        )
    return product


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product (Admin only)"
)
def create_product(
    payload: ProductCreate,
    admin: User = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db)
):
    """
    Creates a new grocery product in inventory. Only administrators are authorized.
    """
    return product_service.create_product(db, payload)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product details (Admin only)"
)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    admin: User = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db)
):
    """
    Updates an existing grocery product. Only administrators are authorized.
    """
    updated_product = product_service.update_product(db, product_id, payload)
    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} was not found."
        )
    return updated_product


@router.delete(
    "/{product_id}",
    response_model=MessageResponse,
    summary="Delete a product (Admin only)"
)
def delete_product(
    product_id: int,
    admin: User = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db)
):
    """
    Safely deletes a product from inventory while preserving historical order receipts.
    Only administrators are authorized.
    """
    deleted = product_service.delete_product(db, product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} was not found."
        )
    return MessageResponse(message=f"Product with ID {product_id} successfully deleted.")
