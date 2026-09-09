import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.deps import require_role
from app.models import Order, Product, User
from app.schemas import OrderRead, OrderStatusUpdate, ProductCreate, ProductRead, ProductUpdate


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(["admin"]))],
)
DbSession = Annotated[Session, Depends(get_db)]


def _get_product_or_404(product_id: uuid.UUID, db: Session) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: DbSession) -> Product:
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: uuid.UUID, payload: ProductUpdate, db: DbSession) -> Product:
    product = _get_product_or_404(product_id, db)
    for field, value in payload.model_dump().items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: uuid.UUID, db: DbSession) -> Response:
    product = _get_product_or_404(product_id, db)
    db.delete(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is referenced by an order and cannot be deleted",
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/orders", response_model=list[OrderRead])
def list_orders(db: DbSession) -> list[Order]:
    statement = select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc())
    return list(db.scalars(statement))


@router.patch("/orders/{order_id}/status", response_model=OrderRead)
def update_order_status(order_id: uuid.UUID, payload: OrderStatusUpdate, db: DbSession) -> Order:
    order = db.scalar(select(Order).where(Order.id == order_id).options(selectinload(Order.items)))
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order
