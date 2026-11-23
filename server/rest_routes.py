"""
FastAPI REST API Route definitions.
"""
import uuid
import html
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from server.db import db, hash_pw
from server.models import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserProfileResponse,
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductResponse,
    PaginatedProductsResponse,
    OrderCreateRequest,
    OrderResponse,
    OrderItemResponse,
    OrderStatusUpdateRequest,
    OrderStatus,
)
from server.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    require_admin,
)

router = APIRouter()


# ==============================================================================
# Auth Endpoints
# ==============================================================================
@router.post("/api/v1/auth/register", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest):
    # Check duplicate username
    for u in db.users.values():
        if u["username"].lower() == payload.username.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{payload.username}' is already registered",
            )
        if u["email"].lower() == payload.email.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{payload.email}' is already registered",
            )

    new_id = f"usr_{uuid.uuid4().hex[:8]}"
    new_user = {
        "id": new_id,
        "username": payload.username,
        "email": payload.email,
        "password_hash": hash_pw(payload.password),
        "role": payload.role.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.users[new_id] = new_user
    return UserProfileResponse(**new_user)


@router.post("/api/v1/auth/login", response_model=TokenResponse)
def login(payload: UserLoginRequest):
    user = None
    for u in db.users.values():
        if u["username"] == payload.username:
            user = u
            break

    if not user or user["password_hash"] != hash_pw(payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(user["id"], user["username"], user["role"])
    refresh_token = create_refresh_token(user["id"])

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user["id"],
        username=user["username"],
        role=user["role"],
    )


@router.post("/api/v1/auth/refresh", response_model=TokenResponse)
def refresh(payload: RefreshTokenRequest):
    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type. Expected refresh token",
        )
    user_id = data.get("sub")
    user = db.users.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_access = create_access_token(user["id"], user["username"], user["role"])
    new_refresh = create_refresh_token(user["id"])
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        user_id=user["id"],
        username=user["username"],
        role=user["role"],
    )


@router.get("/api/v1/auth/me", response_model=UserProfileResponse)
def get_me(user: dict = Depends(get_current_user)):
    return UserProfileResponse(**user)


@router.post("/api/v1/auth/logout", status_code=status.HTTP_200_OK)
def logout(authorization: Optional[str] = Header(None)):
    if authorization and " " in authorization:
        token = authorization.split()[1]
        db.blacklisted_tokens.add(token)
    return {"message": "Successfully logged out and invalidated session token"}


# ==============================================================================
# Products Endpoints
# ==============================================================================
@router.get("/api/v1/products", response_model=PaginatedProductsResponse)
def list_products(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    items = list(db.products.values())

    # Category filter
    if category:
        items = [p for p in items if p["category"].lower() == category.lower()]

    # Search filter
    if q:
        query_str = q.lower()
        items = [p for p in items if query_str in p["title"].lower() or query_str in p["description"].lower()]

    # Price range
    if min_price is not None:
        items = [p for p in items if p["price"] >= min_price]
    if max_price is not None:
        items = [p for p in items if p["price"] <= max_price]

    # Sorting
    reverse = sort_order == "desc"
    if sort_by in ["price", "title", "created_at"]:
        items.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

    total = len(items)
    paginated = items[offset : offset + limit]
    return PaginatedProductsResponse(
        total=total,
        offset=offset,
        limit=limit,
        items=[ProductResponse(**p) for p in paginated],
    )


@router.get("/api/v1/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: str):
    product = db.products.get(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found",
        )
    return ProductResponse(**product)


@router.post("/api/v1/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreateRequest, admin: dict = Depends(require_admin)):
    sanitized_title = html.escape(payload.title)
    new_id = f"prod_{uuid.uuid4().hex[:6]}"
    new_item = {
        "id": new_id,
        "title": sanitized_title,
        "description": payload.description,
        "price": payload.price,
        "category": payload.category.value,
        "stock": payload.stock,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.products[new_id] = new_item
    return ProductResponse(**new_item)


@router.put("/api/v1/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: str, payload: ProductUpdateRequest, admin: dict = Depends(require_admin)):
    product = db.products.get(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )
    if payload.title is not None:
        product["title"] = html.escape(payload.title)
    if payload.description is not None:
        product["description"] = payload.description
    if payload.price is not None:
        product["price"] = payload.price
    if payload.category is not None:
        product["category"] = payload.category.value
    if payload.stock is not None:
        product["stock"] = payload.stock

    return ProductResponse(**product)


@router.delete("/api/v1/products/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: str, admin: dict = Depends(require_admin)):
    if product_id not in db.products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )
    del db.products[product_id]
    return {"message": f"Product '{product_id}' successfully removed"}


# ==============================================================================
# Orders Endpoints
# ==============================================================================
@router.post("/api/v1/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreateRequest, user: dict = Depends(get_current_user)):
    order_items = []
    subtotal = 0.0

    for item_req in payload.items:
        prod = db.products.get(item_req.product_id)
        if not prod:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product ID '{item_req.product_id}' does not exist",
            )
        if prod["stock"] < item_req.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{prod['title']}'. Requested: {item_req.quantity}, Available: {prod['stock']}",
            )

        line_total = round(prod["price"] * item_req.quantity, 2)
        subtotal += line_total
        order_items.append(
            OrderItemResponse(
                product_id=prod["id"],
                title=prod["title"],
                price=prod["price"],
                quantity=item_req.quantity,
                line_total=line_total,
            )
        )
        # Deduct stock
        prod["stock"] -= item_req.quantity

    subtotal = round(subtotal, 2)
    tax = round(subtotal * 0.08, 2)
    total = round(subtotal + tax, 2)

    order_id = f"ord_{uuid.uuid4().hex[:6]}"
    order = {
        "id": order_id,
        "user_id": user["id"],
        "items": [it.model_dump() for it in order_items],
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "status": OrderStatus.PENDING,
        "shipping_address": payload.shipping_address,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.orders[order_id] = order
    return OrderResponse(**order)


@router.get("/api/v1/orders", response_model=list[OrderResponse])
def list_user_orders(user: dict = Depends(get_current_user)):
    if user["role"] == "admin":
        user_orders = list(db.orders.values())
    else:
        user_orders = [o for o in db.orders.values() if o["user_id"] == user["id"]]
    return [OrderResponse(**o) for o in user_orders]


@router.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, user: dict = Depends(get_current_user)):
    order = db.orders.get(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found",
        )
    if user["role"] != "admin" and order["user_id"] != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot view orders belonging to another user",
        )
    return OrderResponse(**order)


@router.patch("/api/v1/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: str,
    payload: OrderStatusUpdateRequest,
    user: dict = Depends(get_current_user),
):
    order = db.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order '{order_id}' not found")
    if user["role"] != "admin" and order["user_id"] != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to modify this order")

    order["status"] = payload.status
    return OrderResponse(**order)


# ==============================================================================
# Health & Fixture Reset
# ==============================================================================
@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "qa-ecommerce-api",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/api/v1/system/reset")
def reset_database():
    db.reset()
    return {"message": "Database and sessions successfully reset to seed state"}
