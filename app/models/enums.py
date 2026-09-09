from enum import Enum


class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
