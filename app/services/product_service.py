from typing import Optional, List, Tuple
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session
from app.models import Product, CartItem, OrderItem
from app.schemas import ProductCreate, ProductUpdate


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    """
    Retrieves a single product by its primary key ID.
    """
    return db.query(Product).filter(Product.id == product_id).first()


def list_products(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: Optional[str] = "newest",
    page: int = 1,
    limit: int = 20
) -> Tuple[List[Product], int]:
    """
    Lists products with optional search query, category filter, sorting, and pagination.
    """
    query = db.query(Product)

    # Search filter (name or description)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern)
            )
        )

    # Category filter
    if category and category.strip() and category.strip().lower() != "all":
        query = query.filter(Product.category == category.strip())

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(asc(Product.price))
    elif sort_by == "price_desc":
        query = query.order_by(desc(Product.price))
    elif sort_by == "name_asc":
        query = query.order_by(asc(Product.name))
    elif sort_by == "name_desc":
        query = query.order_by(desc(Product.name))
    else:  # newest
        query = query.order_by(desc(Product.created_at))

    total = query.count()

    # Pagination
    offset = max(0, (page - 1) * limit)
    products = query.offset(offset).limit(limit).all()

    return products, total


def create_product(db: Session, product_in: ProductCreate) -> Product:
    """
    Creates a new grocery product.
    """
    product = Product(
        name=product_in.name.strip(),
        price=product_in.price,
        image_url=product_in.image_url,
        description=product_in.description,
        category=product_in.category.strip(),
        stock_quantity=product_in.stock_quantity
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, product_in: ProductUpdate) -> Optional[Product]:
    """
    Updates an existing product's fields.
    """
    product = get_product_by_id(db, product_id)
    if not product:
        return None

    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "name" and value is not None:
            value = value.strip()
        elif field == "category" and value is not None:
            value = value.strip()
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> bool:
    """
    Deletes a product safely.
    Removes references from active carts and detaches foreign keys in historical order items.
    """
    product = get_product_by_id(db, product_id)
    if not product:
        return False

    # Clean up active carts with this product
    db.query(CartItem).filter(CartItem.product_id == product_id).delete()

    # In historical order items, unlink product_id to preserve the order snapshots intact
    db.query(OrderItem).filter(OrderItem.product_id == product_id).update(
        {OrderItem.product_id: None},
        synchronize_session=False
    )

    db.delete(product)
    db.commit()
    return True
