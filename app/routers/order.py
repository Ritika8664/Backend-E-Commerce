import uuid
from collections import defaultdict
from decimal import Decimal
from typing import Annotated

import razorpay
from razorpay.errors import BadRequestError, GatewayError, ServerError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.db.session import get_db
from app.deps import get_current_user, require_role
from app.models import Order, OrderItem, OrderStatus, Product, User, UserRole
from app.schemas import CheckoutSessionResponse, OrderCreate, OrderRead


router = APIRouter(prefix="/orders", tags=["orders"])
DbSession = Annotated[Session, Depends(get_db)]
Customer = Annotated[User, Depends(require_role(["customer"]))]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: DbSession, current_user: Customer) -> Order:
    if not payload.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart cannot be empty")

    quantities: dict[uuid.UUID, int] = defaultdict(int)
    for item in payload.items:
        if item.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item quantity must be greater than zero",
            )
        quantities[item.product_id] += item.quantity

    try:
        products = list(
            db.scalars(
                select(Product)
                .where(Product.id.in_(quantities))
                .order_by(Product.id)
                .with_for_update()
            )
        )
        products_by_id = {product.id: product for product in products}

        for product_id, quantity in quantities.items():
            product = products_by_id.get(product_id)
            if product is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product {product_id} is unavailable",
                )
            if not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product {product.name} is unavailable",
                )
            if product.stock < quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for {product.name}",
                )

        order = Order(
            user_id=current_user.id,
            status=OrderStatus.PENDING,
            total_amount=Decimal("0.00"),
        )
        total = Decimal("0.00")
        for product_id, quantity in quantities.items():
            product = products_by_id[product_id]
            product.stock -= quantity
            total += product.price * quantity
            order.items.append(OrderItem(product_id=product.id, quantity=quantity, unit_price=product.price))

        order.total_amount = total
        db.add(order)
        db.commit()
        db.refresh(order)
        return order
    except Exception:
        db.rollback()
        raise


@router.get("/me", response_model=list[OrderRead])
def list_my_orders(db: DbSession, current_user: Customer) -> list[Order]:
    statement = (
        select(Order)
        .where(Order.user_id == current_user.id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    return list(db.scalars(statement))


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> Order:
    order = db.scalar(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return order


@router.post("/{order_id}/checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(
    order_id: uuid.UUID,
    db: DbSession,
    current_user: Customer,
) -> CheckoutSessionResponse:
    order = db.scalar(
        select(Order)
        .where(Order.id == order_id)
        .with_for_update()
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be paid",
        )

    amount = int(order.total_amount * Decimal("100"))
    if order.payment_reference_id:
        return CheckoutSessionResponse(
            razorpay_order_id=order.payment_reference_id,
            amount=amount,
            currency="INR",
            key_id=settings.razorpay_key_id,
        )

    client = razorpay.Client(
        auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
    )

    try:
        razorpay_order = client.order.create(
            data={
                "amount": amount,
                "currency": "INR",
                "receipt": str(order.id),
                "notes": {"order_id": str(order.id)},
            }
        )
    except (BadRequestError, GatewayError, ServerError):
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to start Razorpay checkout",
        ) from None

    razorpay_order_id = razorpay_order.get("id")
    if not isinstance(razorpay_order_id, str):
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Razorpay did not return an order ID",
        )

    order.payment_reference_id = razorpay_order_id
    db.commit()
    return CheckoutSessionResponse(
        razorpay_order_id=razorpay_order_id,
        amount=amount,
        currency="INR",
        key_id=settings.razorpay_key_id,
    )
