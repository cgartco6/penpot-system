from pydantic import BaseModel
from typing import Optional

class PaymentRequest(BaseModel):
    amount: float
    currency: str = "ZAR"
    email: str
    item_name: str
    gateway: str  # payfast, ozow, yoco, paystack, stripe, paypal, eft

class PaymentResponse(BaseModel):
    status: str
    redirect_url: Optional[str] = None
    transaction_id: Optional[str] = None
    message: str
