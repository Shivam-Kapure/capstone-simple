"""Payment & Notification Engine - minimal FastAPI backend (demo data only)."""
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app = FastAPI(title="Payment & Notification Engine", version=APP_VERSION)

# The frontend reaches the API through its own nginx proxy (same origin), so CORS is
# only needed when someone calls the API directly from another origin.
if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )


class PaymentIn(BaseModel):
    payer: str = Field(min_length=1, max_length=60)
    payee: str = Field(min_length=1, max_length=60)
    amount: Decimal = Field(gt=0, le=1_000_000, decimal_places=2)
    currency: Literal["INR", "USD", "EUR"] = "INR"


class Payment(PaymentIn):
    id: int
    status: Literal["COMPLETED", "PENDING", "FAILED"]
    created_at: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


PAYMENTS: dict[int, Payment] = {}
NOTIFICATIONS: list[dict] = []


def reset_data() -> None:
    """Load the demo records. Also used by the tests to start from a known state."""
    PAYMENTS.clear()
    NOTIFICATIONS.clear()
    seed = [
        ("Acme Corp", "Globex Ltd", "12500.00", "INR", "COMPLETED"),
        ("Initech", "Umbrella Inc", "830.50", "USD", "PENDING"),
        ("Stark Ind", "Wayne Ent", "99.99", "EUR", "FAILED"),
    ]
    for payer, payee, amount, currency, status in seed:
        _store(PaymentIn(payer=payer, payee=payee, amount=Decimal(amount), currency=currency), status)


def _store(data: PaymentIn, status: str) -> Payment:
    payment = Payment(id=len(PAYMENTS) + 1, status=status, created_at=_now(), **data.model_dump())
    PAYMENTS[payment.id] = payment
    NOTIFICATIONS.append({
        "id": len(NOTIFICATIONS) + 1,
        "payment_id": payment.id,
        "message": f"Payment #{payment.id} of {payment.amount} {payment.currency} "
                   f"from {payment.payer} to {payment.payee} is {payment.status}",
        "created_at": payment.created_at,
    })
    return payment


reset_data()


@app.get("/")
def root():
    return {"service": "payment-backend", "version": APP_VERSION, "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy", "version": APP_VERSION}


@app.get("/api/payments", response_model=list[Payment])
def list_payments():
    return list(PAYMENTS.values())


@app.get("/api/payments/{payment_id}", response_model=Payment)
def get_payment(payment_id: int):
    if payment_id not in PAYMENTS:
        raise HTTPException(status_code=404, detail=f"Payment {payment_id} not found")
    return PAYMENTS[payment_id]


@app.post("/api/payments", response_model=Payment, status_code=201)
def create_payment(data: PaymentIn):
    return _store(data, "COMPLETED")


@app.get("/api/notifications")
def list_notifications():
    return list(reversed(NOTIFICATIONS))
