import json
import uuid
from dataclasses import dataclass

from langchain.tools import ToolRuntime, tool
from sqlalchemy import case, func, select

from app.db.session import SessionLocal
from app.models import Order, Product


@dataclass(frozen=True)
class AgentContext:
    user_id: str


def _escaped_match(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return "%" + escaped + "%"


@tool
def get_product_price(product_name: str) -> str:
    """Look up the current price and stock for an active product by fuzzy name."""
    search_name = product_name.strip()
    if not search_name:
        return json.dumps({"found": False, "message": "No product name was provided."})

    with SessionLocal() as db:
        product = db.scalar(
            select(Product)
            .where(
                Product.is_active.is_(True),
                Product.name.ilike(_escaped_match(search_name), escape="\\"),
            )
            .order_by(
                case((func.lower(Product.name) == search_name.lower(), 0), else_=1),
                func.length(Product.name),
            )
            .limit(1)
        )
    if product is None:
        return json.dumps({"found": False, "message": f"No active product matched '{search_name}'."})
    return json.dumps(
        {
            "found": True,
            "name": product.name,
            "price": str(product.price),
            "stock": product.stock,
        }
    )


@tool
def list_available_products() -> str:
    """List all active products with their current price and stock."""
    with SessionLocal() as db:
        products = list(
            db.scalars(
                select(Product)
                .where(Product.is_active.is_(True))
                .order_by(Product.name)
            )
        )
    return json.dumps(
        {
            "products": [
                {"name": product.name, "price": str(product.price), "stock": product.stock}
                for product in products
            ]
        }
    )


@tool
def get_order_status(order_id: str, runtime: ToolRuntime[AgentContext]) -> str:
    """Get an order status for the authenticated customer only."""
    try:
        parsed_order_id = uuid.UUID(order_id)
        authenticated_user_id = uuid.UUID(runtime.context.user_id)
    except ValueError:
        return json.dumps({"found": False, "message": "The order ID is invalid."})

    with SessionLocal() as db:
        order = db.scalar(
            select(Order).where(
                Order.id == parsed_order_id,
                Order.user_id == authenticated_user_id,
            )
        )
    if order is None:
        return json.dumps(
            {
                "found": False,
                "message": "No order with that ID was found for this account.",
            }
        )
    return json.dumps(
        {
            "found": True,
            "order_id": str(order.id),
            "status": order.status.value,
        }
    )


SUPPORT_TOOLS = [get_product_price, list_available_products, get_order_status]
