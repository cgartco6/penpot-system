# Payment Service API

## POST /api/payment/initiate
Initiate a payment with a chosen gateway.

**Request Body:**
```json
{
  "amount": 299.99,
  "currency": "ZAR",
  "email": "buyer@example.com",
  "item_name": "Logo Design",
  "gateway": "payfast"  // or ozow, yoco, paystack, stripe, paypal, eft
}
