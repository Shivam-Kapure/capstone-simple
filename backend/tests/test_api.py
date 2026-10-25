import pytest
from fastapi.testclient import TestClient

from app.main import app, reset_data

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_data():
    reset_data()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_list_payments():
    r = client.get("/api/payments")
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_get_payment_and_missing():
    assert client.get("/api/payments/1").json()["payer"] == "Acme Corp"
    r = client.get("/api/payments/999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"]


def test_create_payment_adds_notification():
    r = client.post("/api/payments", json={"payer": "A", "payee": "B", "amount": "10.50", "currency": "USD"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 4 and body["status"] == "COMPLETED"
    latest = client.get("/api/notifications").json()[0]
    assert latest["payment_id"] == 4


@pytest.mark.parametrize("payload", [
    {"payer": "A", "payee": "B", "amount": "-5"},
    {"payer": "", "payee": "B", "amount": "5"},
    {"payer": "A", "payee": "B", "amount": "5", "currency": "BTC"},
    {"payer": "A", "payee": "B"},
])
def test_create_payment_invalid(payload):
    assert client.post("/api/payments", json=payload).status_code == 422


def test_notifications():
    r = client.get("/api/notifications")
    assert r.status_code == 200
    assert len(r.json()) == 3
