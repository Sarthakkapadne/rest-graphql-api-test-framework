"""
In-memory mock database for the REST & GraphQL Test Framework.
Contains seed users (admin/standard), products, and orders with reset capability.
"""
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
import hashlib

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

class Database:
    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        with self._lock:
            self.users: Dict[str, dict] = {
                "usr_admin": {
                    "id": "usr_admin",
                    "username": "admin",
                    "email": "admin@qa-suite.io",
                    "password_hash": hash_pw("admin123!"),
                    "role": "admin",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                "usr_standard": {
                    "id": "usr_standard",
                    "username": "qa_tester",
                    "email": "tester@qa-suite.io",
                    "password_hash": hash_pw("tester123!"),
                    "role": "user",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            }

            self.products: Dict[str, dict] = {
                "prod_01": {
                    "id": "prod_01",
                    "title": "Ergonomic Mechanical Keyboard",
                    "description": "Custom mechanical keyboard with hot-swappable tactile switches.",
                    "price": 149.99,
                    "category": "electronics",
                    "stock": 45,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                "prod_02": {
                    "id": "prod_02",
                    "title": "Ultra-Wide Gaming Monitor 34-inch",
                    "description": "144Hz 1ms IPS curved display with HDR600.",
                    "price": 499.50,
                    "category": "electronics",
                    "stock": 20,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                "prod_03": {
                    "id": "prod_03",
                    "title": "Organic Cotton Developer Hoodie",
                    "description": "Comfortable charcoal pullover with embroidered terminal syntax.",
                    "price": 65.00,
                    "category": "apparel",
                    "stock": 100,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                "prod_04": {
                    "id": "prod_04",
                    "title": "Minimalist Water Bottle",
                    "description": "Double-wall insulated stainless steel flask 750ml.",
                    "price": 28.00,
                    "category": "accessories",
                    "stock": 150,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                "prod_05": {
                    "id": "prod_05",
                    "title": "Software Architecture Patterns Book",
                    "description": "Hardcover guide on microservices, CQRS, and distributed systems.",
                    "price": 54.95,
                    "category": "books",
                    "stock": 35,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                "prod_06": {
                    "id": "prod_06",
                    "title": "Noise-Cancelling Wireless Headphones",
                    "description": "Over-ear active noise cancelling with 40h battery life.",
                    "price": 299.99,
                    "category": "electronics",
                    "stock": 15,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            }

            self.orders: Dict[str, dict] = {
                "ord_101": {
                    "id": "ord_101",
                    "user_id": "usr_standard",
                    "items": [
                        {
                            "product_id": "prod_01",
                            "title": "Ergonomic Mechanical Keyboard",
                            "price": 149.99,
                            "quantity": 1,
                            "line_total": 149.99,
                        }
                    ],
                    "subtotal": 149.99,
                    "tax": 12.00,
                    "total": 161.99,
                    "status": "CONFIRMED",
                    "shipping_address": "456 QA Boulevard, Tech City, 411001",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            }

            self.blacklisted_tokens: set = set()

db = Database()
