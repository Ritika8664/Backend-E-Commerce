from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import admin, ai, auth, order, payments, product, webhooks


app = FastAPI(title="Mini E-Commerce API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(product.router)
app.include_router(order.router)
app.include_router(payments.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(webhooks.router)
app.include_router(ai.router)
