import os, hashlib, httpx
from fastapi import FastAPI, Request, HTTPException
from models import PaymentRequest, PaymentResponse
import stripe
import paypalrestsdk
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Payment Service (ZAR)")

# ---- Config ----
PAYFAST_MERCHANT_ID = os.getenv("PAYFAST_MERCHANT_ID")
PAYFAST_MERCHANT_KEY = os.getenv("PAYFAST_MERCHANT_KEY")
PAYFAST_PASSPHRASE = os.getenv("PAYFAST_PASSPHRASE")
PAYFAST_SANDBOX = os.getenv("PAYFAST_SANDBOX", "True").lower() == "true"
PAYFAST_URL = "https://sandbox.payfast.co.za/eng/process" if PAYFAST_SANDBOX else "https://www.payfast.co.za/eng/process"

OZOW_SITE_CODE = os.getenv("OZOW_SITE_CODE")
OZOW_API_KEY = os.getenv("OZOW_API_KEY")

YOCO_PUBLIC_KEY = os.getenv("YOCO_PUBLIC_KEY")
YOCO_SECRET_KEY = os.getenv("YOCO_SECRET_KEY")

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")
paypalrestsdk.configure({
    "mode": PAYPAL_MODE,
    "client_id": PAYPAL_CLIENT_ID,
    "client_secret": PAYPAL_CLIENT_SECRET
})

BANK_ACCOUNT_NUMBER = os.getenv("BANK_ACCOUNT_NUMBER")
BANK_BRANCH_CODE = os.getenv("BANK_BRANCH_CODE")

# ---- Helper ----
def generate_payfast_signature(data: dict) -> str:
    pf_string = "&".join([f"{k}={v}" for k, v in sorted(data.items()) if v])
    if PAYFAST_PASSPHRASE:
        pf_string += f"&passphrase={PAYFAST_PASSPHRASE}"
    return hashlib.md5(pf_string.encode()).hexdigest()

# ---- Endpoints ----
@app.post("/api/payment/initiate", response_model=PaymentResponse)
async def initiate_payment(pay_req: PaymentRequest):
    gateway = pay_req.gateway.lower()
    
    if gateway == "payfast":
        pf_data = {
            "merchant_id": PAYFAST_MERCHANT_ID,
            "merchant_key": PAYFAST_MERCHANT_KEY,
            "return_url": "http://localhost/api/payment/success",
            "cancel_url": "http://localhost/api/payment/cancel",
            "notify_url": "http://payment-service:8001/api/payment/webhook",
            "amount": f"{pay_req.amount:.2f}",
            "item_name": pay_req.item_name,
            "email_address": pay_req.email,
            "payment_method": "instant_eft"
        }
        pf_data["signature"] = generate_payfast_signature(pf_data)
        return PaymentResponse(
            status="redirect",
            redirect_url=PAYFAST_URL,
            transaction_id=pf_data.get("m_payment_id", ""),
            message="Redirect to PayFast"
        )
    
    elif gateway == "ozow":
        ozow_url = "https://sandbox.ozow.co.za/ProcessRequest"
        return PaymentResponse(
            status="redirect",
            redirect_url=ozow_url,
            message="Redirect to Ozow (additional params needed)"
        )
    
    elif gateway == "yoco":
        return PaymentResponse(
            status="redirect",
            redirect_url="https://pay.yoco.com/your-checkout",
            message="Redirect to Yoco (configure your checkout)"
        )
    
    elif gateway == "paystack":
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.paystack.co/transaction/initialize",
                headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"},
                json={
                    "email": pay_req.email,
                    "amount": int(pay_req.amount * 100),
                    "currency": "ZAR",
                    "callback_url": "http://localhost/api/payment/success"
                }
            )
            data = resp.json()
            if data["status"]:
                return PaymentResponse(
                    status="redirect",
                    redirect_url=data["data"]["authorization_url"],
                    transaction_id=data["data"]["reference"],
                    message="Redirect to Paystack"
                )
            else:
                raise HTTPException(400, detail=data["message"])
    
    elif gateway == "stripe":
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "zar",
                        "product_data": {"name": pay_req.item_name},
                        "unit_amount": int(pay_req.amount * 100),
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url="http://localhost/api/payment/success",
                cancel_url="http://localhost/api/payment/cancel",
            )
            return PaymentResponse(
                status="redirect",
                redirect_url=session.url,
                transaction_id=session.id,
                message="Redirect to Stripe"
            )
        except Exception as e:
            raise HTTPException(400, detail=str(e))
    
    elif gateway == "paypal":
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {"total": f"{pay_req.amount:.2f}", "currency": "ZAR"},
                "description": pay_req.item_name
            }],
            "redirect_urls": {
                "return_url": "http://localhost/api/payment/success",
                "cancel_url": "http://localhost/api/payment/cancel"
            }
        })
        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    return PaymentResponse(
                        status="redirect",
                        redirect_url=link.href,
                        transaction_id=payment.id,
                        message="Redirect to PayPal"
                    )
        raise HTTPException(400, detail=payment.error)
    
    elif gateway == "eft":
        ref = f"EFT-{hash(pay_req.email)}"
        return PaymentResponse(
            status="awaiting_payment",
            message=f"Pay {pay_req.amount} ZAR to FNB account {BANK_ACCOUNT_NUMBER} (Ref: {ref})",
            transaction_id=ref
        )
    else:
        raise HTTPException(400, detail="Unsupported gateway")

@app.post("/api/payment/webhook")
async def webhook(request: Request):
    # Placeholder – implement gateway-specific verification
    return {"status": "ok"}

@app.get("/api/payout/calculate")
async def calculate_payout():
    # Replace with actual DB query
    today_revenue = 0.0
    return {
        "total_revenue": today_revenue,
        "owner_share": today_revenue * 0.5,
        "system_fund": today_revenue * 0.5
    }
