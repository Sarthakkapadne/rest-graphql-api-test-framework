"""
Strawberry GraphQL Schema definition with Queries and Mutations.
"""
from typing import List, Optional
import uuid
import strawberry
from datetime import datetime, timezone
from server.db import db, hash_pw
from server.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
)


@strawberry.type
class UserType:
    id: str
    username: str
    email: str
    role: str
    created_at: str


@strawberry.type
class ProductType:
    id: str
    title: str
    description: str
    price: float
    category: str
    stock: int
    created_at: str


@strawberry.type
class OrderItemType:
    product_id: str
    title: str
    price: float
    quantity: int
    line_total: float


@strawberry.type
class OrderType:
    id: str
    user_id: str
    items: List[OrderItemType]
    subtotal: float
    tax: float
    total: float
    status: str
    shipping_address: str
    created_at: str


@strawberry.type
class AuthPayloadType:
    access_token: str
    refresh_token: str
    user_id: str
    username: str
    role: str


@strawberry.type
class Query:
    @strawberry.field
    def product(self, id: str) -> Optional[ProductType]:
        item = db.products.get(id)
        if not item:
            return None
        return ProductType(**item)

    @strawberry.field
    def products(
        self,
        category: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        search: Optional[str] = None,
    ) -> List[ProductType]:
        items = list(db.products.values())
        if category:
            items = [p for p in items if p["category"].lower() == category.lower()]
        if search:
            q = search.lower()
            items = [p for p in items if q in p["title"].lower() or q in p["description"].lower()]
        return [ProductType(**p) for p in items[offset : offset + limit]]

    @strawberry.field
    def me(self, token: str) -> Optional[UserType]:
        try:
            data = decode_token(token)
            user = db.users.get(data.get("sub"))
            if user:
                return UserType(
                    id=user["id"],
                    username=user["username"],
                    email=user["email"],
                    role=user["role"],
                    created_at=user["created_at"],
                )
        except Exception:
            return None
        return None

    @strawberry.field
    def order(self, id: str, token: str) -> Optional[OrderType]:
        try:
            data = decode_token(token)
            user_id = data.get("sub")
            order = db.orders.get(id)
            if not order:
                return None
            if data.get("role") != "admin" and order["user_id"] != user_id:
                raise Exception("Unauthorized to view this order")
            items = [OrderItemType(**it) for it in order["items"]]
            return OrderType(
                id=order["id"],
                user_id=order["user_id"],
                items=items,
                subtotal=order["subtotal"],
                tax=order["tax"],
                total=order["total"],
                status=order["status"],
                shipping_address=order["shipping_address"],
                created_at=order["created_at"],
            )
        except Exception:
            return None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def login(self, username: str, password: str) -> Optional[AuthPayloadType]:
        for u in db.users.values():
            if u["username"] == username and u["password_hash"] == hash_pw(password):
                access = create_access_token(u["id"], u["username"], u["role"])
                refresh = create_refresh_token(u["id"])
                return AuthPayloadType(
                    access_token=access,
                    refresh_token=refresh,
                    user_id=u["id"],
                    username=u["username"],
                    role=u["role"],
                )
        raise Exception("Invalid username or password")

    @strawberry.mutation
    def create_product(
        self,
        title: str,
        description: str,
        price: float,
        category: str,
        stock: int,
        token: str,
    ) -> ProductType:
        data = decode_token(token)
        if data.get("role") != "admin":
            raise Exception("Admin privileges required to create product")
        if price <= 0:
            raise Exception("Price must be strictly positive")
        if stock < 0:
            raise Exception("Stock cannot be negative")

        new_id = f"prod_{uuid.uuid4().hex[:6]}"
        new_prod = {
            "id": new_id,
            "title": title,
            "description": description,
            "price": price,
            "category": category,
            "stock": stock,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        db.products[new_id] = new_prod
        return ProductType(**new_prod)

    @strawberry.mutation
    def create_order(
        self,
        product_id: str,
        quantity: int,
        shipping_address: str,
        token: str,
    ) -> OrderType:
        data = decode_token(token)
        user_id = data.get("sub")
        if not user_id:
            raise Exception("Unauthorized")

        prod = db.products.get(product_id)
        if not prod:
            raise Exception(f"Product '{product_id}' not found")
        if prod["stock"] < quantity:
            raise Exception("Insufficient inventory")

        line_total = round(prod["price"] * quantity, 2)
        prod["stock"] -= quantity

        subtotal = line_total
        tax = round(subtotal * 0.08, 2)
        total = round(subtotal + tax, 2)

        order_id = f"ord_{uuid.uuid4().hex[:6]}"
        order_item = OrderItemType(
            product_id=prod["id"],
            title=prod["title"],
            price=prod["price"],
            quantity=quantity,
            line_total=line_total,
        )
        order = {
            "id": order_id,
            "user_id": user_id,
            "items": [
                {
                    "product_id": prod["id"],
                    "title": prod["title"],
                    "price": prod["price"],
                    "quantity": quantity,
                    "line_total": line_total,
                }
            ],
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "status": "PENDING",
            "shipping_address": shipping_address,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        db.orders[order_id] = order
        return OrderType(
            id=order_id,
            user_id=user_id,
            items=[order_item],
            subtotal=subtotal,
            tax=tax,
            total=total,
            status="PENDING",
            shipping_address=shipping_address,
            created_at=order["created_at"],
        )

    @strawberry.mutation
    def cancel_order(self, order_id: str, token: str) -> OrderType:
        data = decode_token(token)
        user_id = data.get("sub")
        order = db.orders.get(order_id)
        if not order:
            raise Exception(f"Order '{order_id}' not found")
        if data.get("role") != "admin" and order["user_id"] != user_id:
            raise Exception("Unauthorized to modify this order")

        order["status"] = "CANCELLED"
        items = [OrderItemType(**it) for it in order["items"]]
        return OrderType(
            id=order["id"],
            user_id=order["user_id"],
            items=items,
            subtotal=order["subtotal"],
            tax=order["tax"],
            total=order["total"],
            status="CANCELLED",
            shipping_address=order["shipping_address"],
            created_at=order["created_at"],
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)
