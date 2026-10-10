from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

VALID_CATEGORIES = [
    "Fruits",
    "Vegetables",
    "Dairy",
    "Grains",
    "Snacks",
    "Beverages",
    "Household Essentials"
]


# ============================================================================
# Generic Response Schemas
# ============================================================================
class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


# ============================================================================
# Authentication Schemas
# ============================================================================
class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of customer")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (at least 6 characters)")
    confirm_password: str = Field(..., description="Must match password")

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Full name cannot be empty")
        return trimmed

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class AdminLoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=1, description="Admin username or email")
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[UserResponse] = None
    csrf_token: Optional[str] = None


# ============================================================================
# Product Schemas
# ============================================================================
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: Decimal = Field(..., gt=Decimal("0.00"), decimal_places=2)
    image_url: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None, max_length=2000)
    category: str = Field(...)
    stock_quantity: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Product name cannot be empty")
        return trimmed

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        trimmed = v.strip()
        if trimmed not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(VALID_CATEGORIES)}")
        return trimmed

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            return None
        if not (trimmed.startswith("http://") or trimmed.startswith("https://") or trimmed.startswith("/static/")):
            raise ValueError("Image URL must start with http://, https://, or /static/")
        return trimmed


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    price: Optional[Decimal] = Field(default=None, gt=Decimal("0.00"), decimal_places=2)
    image_url: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None, max_length=2000)
    category: Optional[str] = None
    stock_quantity: Optional[int] = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Product name cannot be empty")
        return trimmed

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if trimmed not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(VALID_CATEGORIES)}")
        return trimmed

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            return None
        if not (trimmed.startswith("http://") or trimmed.startswith("https://") or trimmed.startswith("/static/")):
            raise ValueError("Image URL must start with http://, https://, or /static/")
        return trimmed


class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ============================================================================
# Cart Schemas
# ============================================================================
class CartItemAdd(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, gt=0, le=100)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0, le=100)


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    category: str
    unit_price: Decimal
    image_url: Optional[str] = None
    quantity: int
    stock_quantity: int
    line_subtotal: Decimal


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_items: int
    total_amount: Decimal


# ============================================================================
# Order Schemas
# ============================================================================
class OrderCreateRequest(BaseModel):
    shipping_name: Optional[str] = Field(default=None, max_length=100)
    shipping_address: Optional[str] = Field(default=None, max_length=300)
    shipping_phone: Optional[str] = Field(default=None, max_length=20)


class OrderItemResponse(BaseModel):
    id: int
    product_id: Optional[int] = None
    product_name: str
    unit_price: Decimal
    quantity: int
    line_subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: Decimal
    order_status: str
    created_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int


# ============================================================================
# Admin Dashboard Schemas
# ============================================================================
class AdminDashboardStats(BaseModel):
    total_products: int
    total_customers: int
    total_orders: int
    total_revenue: Decimal
    low_stock_count: int
