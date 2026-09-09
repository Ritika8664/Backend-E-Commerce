from pydantic import BaseModel


class CheckoutSessionResponse(BaseModel):
    razorpay_order_id: str
    amount: int
    currency: str
    key_id: str


class PaymentVerificationRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
