"""
Pydantic data models for the eCommerce API Server.
"""
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, EmailStr


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class ProductCategory(str, Enum):
    ELECTRONICS = "electronics"
    APPAREL = "apparel"
    ACCESSORIES = "accessories"
    BOOKS = "books"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


# Auth Models
class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.USER


class UserLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user_id: str
    username: str
    role: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserProfileResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    created_at: str


# Product Models
class ProductCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=1000)
    price: float = Field(..., ge=0.01)
    category: ProductCategory
    stock: int = Field(..., ge=0)


class ProductUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0.01)
    category: Optional[ProductCategory] = None
    stock: Optional[int] = Field(None, ge=0)


class ProductResponse(BaseModel):
    id: str
    title: str
    description: str
    price: float
    category: str
    stock: int
    created_at: str


class PaginatedProductsResponse(BaseModel):
    total: int
    offset: int
    limit: int
    items: List[ProductResponse]


# Order Models
class OrderItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(..., ge=1, le=100)


class OrderCreateRequest(BaseModel):
    items: List[OrderItemRequest] = Field(..., min_length=1)
    shipping_address: str = Field(..., min_length=5)


class OrderItemResponse(BaseModel):
    product_id: str
    title: str
    price: float
    quantity: int
    line_total: float


class OrderResponse(BaseModel):
    id: str
    user_id: str
    items: List[OrderItemResponse]
    subtotal: float
    tax: float
    total: float
    status: OrderStatus
    shipping_address: str
    created_at: str


class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatus
