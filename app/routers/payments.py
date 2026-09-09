from typing import Annotated

import razorpay
from fastapi import APIRouter, Depends, HTTPException, status
from razorpay.errors import SignatureVerificationError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.db.session import get_db
from app.deps import require_role
from app.models import Order, OrderStatus, User
from app.schemas import OrderRead, PaymentVerificationRequest


router = APIRouter(prefix="/payments", tags=["payments"])
DbSession = Annotated[Session, Depends(get_db)]
Customer = Annotated[User, Depends(require_role(["customer"]))]


@router.post("/verify", response_model=OrderRead)
def verify_payment(
    payload: PaymentVerificationRequest,
    db: DbSession,
    current_user: Customer,
) -> Order:
    order = db.scalar(
        select(Order)
        .where(Order.payment_reference_id == payload.razorpay_order_id)
        .options(selectinload(Order.items))
        .with_for_update()
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    client = razorpay.Client(
        auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
    )
    try:
        client.utility.verify_payment_signature(payload.model_dump())
    except SignatureVerificationError:
        if order.status != OrderStatus.PAID:
            order.status = OrderStatus.FAILED
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Razorpay payment signature",
        ) from None

    order.status = OrderStatus.PAID
    db.commit()
    db.refresh(order)
    return order
