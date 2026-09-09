import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Product
from app.schemas import ProductRead


router = APIRouter(prefix="/products", tags=["products"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[ProductRead])
def list_products(db: DbSession) -> list[Product]:
    return list(db.scalars(select(Product).where(Product.is_active.is_(True)).order_by(Product.created_at)))


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: uuid.UUID, db: DbSession) -> Product:
    product = db.scalar(select(Product).where(Product.id == product_id, Product.is_active.is_(True)))
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product
