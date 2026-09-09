import json
import logging
from typing import Annotated, Any

import razorpay
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from razorpay.errors import SignatureVerificationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import Order, OrderStatus


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    db: DbSession,
    razorpay_signature: Annotated[
        str | None, Header(alias="X-Razorpay-Signature")
    ] = None,
) -> dict[str, bool]:
    if razorpay_signature is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Razorpay signature",
        )

    raw_body = await request.body()
    client = razorpay.Client(
        auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
    )
    try:
        body = raw_body.decode("utf-8")
        client.utility.verify_webhook_signature(
            body,
            razorpay_signature,
            settings.razorpay_webhook_secret,
        )
        event: dict[str, Any] = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError, SignatureVerificationError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Razorpay webhook signature",
        ) from None

    event_type = event.get("event")
    if event_type not in {"payment.captured", "payment.failed"}:
        logger.info("Ignoring unhandled Razorpay event type: %s", event_type)
        return {"received": True}

    payment = event.get("payload", {}).get("payment", {}).get("entity", {})
    razorpay_order_id = payment.get("order_id")
    if not isinstance(razorpay_order_id, str):
        logger.warning("Razorpay event is missing an order ID")
        return {"received": True}

    order = db.scalar(
        select(Order)
        .where(Order.payment_reference_id == razorpay_order_id)
        .with_for_update()
    )
    if order is None:
        logger.warning("No order found for Razorpay event %s", event.get("event_id"))
        return {"received": True}

    if event_type == "payment.captured":
        order.status = OrderStatus.PAID
    elif order.status != OrderStatus.PAID:
        order.status = OrderStatus.FAILED
    db.commit()
    return {"received": True}
