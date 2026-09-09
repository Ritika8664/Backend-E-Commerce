from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Product, User, UserRole


SAMPLE_PRODUCTS = (
    {
        "name": "Classic T-Shirt",
        "description": "A soft everyday cotton T-shirt.",
        "price": Decimal("24.99"),
        "stock": 50,
        "image_url": "https://images.unsplash.com/photo-1759572095384-1a7e646d0d4f?q=80&w=627&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
    {
        "name": "Canvas Backpack",
        "description": "A durable backpack for daily essentials.",
        "price": Decimal("59.00"),
        "stock": 25,
        "image_url": "https://images.unsplash.com/photo-1577733966973-d680bffd2e80?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
    {
        "name": "Ceramic Mug",
        "description": "A simple 350 ml ceramic mug.",
        "price": Decimal("14.50"),
        "stock": 80,
        "image_url": "https://images.unsplash.com/photo-1590422749897-47036da0b0ff?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
    {
        "name": "Wireless Earbuds",
        "description": "High-quality wireless earbuds with noise cancellation.",
        "price": Decimal("89.99"),
        "stock": 150,
        "image_url": "https://images.unsplash.com/photo-1606741965326-cb990ae01bb2?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
    {
        "name": "Smartphone Stand",
        "description": "Adjustable aluminum smartphone stand.",
        "price": Decimal("12.99"),
        "stock": 200,
        "image_url": "https://images.unsplash.com/photo-1783909091141-62d17146da2d?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
    {
        "name": "Leather Wallet",
        "description": "Genuine leather minimalist wallet.",
        "price": Decimal("35.00"),
        "stock": 60,
        "image_url": "https://plus.unsplash.com/premium_photo-1676999224991-8f3d35dbde54?q=80&w=677&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
    {
        "name": "Stainless Steel Water Bottle",
        "description": "Insulated water bottle that keeps drinks cold for 24 hours.",
        "price": Decimal("22.50"),
        "stock": 120,
        "image_url": "https://images.unsplash.com/photo-1568395216634-ab1b1e848751?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
    {
        "name": "Mechanical Keyboard",
        "description": "RGB mechanical keyboard with tactile switches.",
        "price": Decimal("110.00"),
        "stock": 45,
        "image_url": "https://images.unsplash.com/photo-1595044426077-d36d9236d54a?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
    {
        "name": "Gaming Mouse",
        "description": "Ergonomic gaming mouse with programmable buttons.",
        "price": Decimal("45.99"),
        "stock": 85,
        "image_url": "https://images.unsplash.com/photo-1629429408209-1f912961dbd8?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
    {
        "name": "Yoga Mat",
        "description": "Eco-friendly non-slip yoga mat.",
        "price": Decimal("29.99"),
        "stock": 100,
        "image_url": "https://images.unsplash.com/photo-1637157216470-d92cd2edb2e8?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
    {
        "name": "Fitness Tracker",
        "description": "Waterproof fitness tracker with heart rate monitor.",
        "price": Decimal("49.50"),
        "stock": 75,
        "image_url": "https://images.unsplash.com/photo-1731341400860-c07e0baaa0c9?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
    {
        "name": "Portable Charger",
        "description": "10000mAh portable charger with fast charging.",
        "price": Decimal("30.00"),
        "stock": 110,
        "image_url": "https://images.unsplash.com/photo-1736516434209-51ece1006788?q=80&w=1469&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
    {
        "name": "Noise-Cancelling Headphones",
        "description": "Over-ear active noise-cancelling headphones.",
        "price": Decimal("199.99"),
        "stock": 30,
        "image_url": "https://images.unsplash.com/photo-1641048930621-ab5d225ae5b0?q=80&w=627&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
)


def seed() -> None:
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == "admin@example.com")) is None:
            db.add(User(email="admin@example.com", name="Store Admin", role=UserRole.ADMIN))

        existing_names = set(db.scalars(select(Product.name).where(Product.name.in_(p["name"] for p in SAMPLE_PRODUCTS))))
        db.add_all(Product(**product) for product in SAMPLE_PRODUCTS if product["name"] not in existing_names)
        db.commit()


if __name__ == "__main__":
    seed()
    print("Seeded one admin user and 13 sample products.")
