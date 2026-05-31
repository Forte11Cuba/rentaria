import hashlib
import hmac

import httpx


def create_invoice(tienda, monto, orden_id, redirect_url=None):
    payload = {
        "amount": str(monto),
        "currency": "USD",
        "metadata": {"orderId": orden_id},
        "checkout": {
            "redirectURL": redirect_url,
            "expirationMinutes": 30,
        },
    }

    res = httpx.post(
        f"{tienda.btcpay_url.rstrip('/')}/api/v1/stores/{tienda.btcpay_store_id}/invoices",
        headers={"Authorization": f"token {tienda.btcpay_api_key}"},
        json=payload,
        timeout=15,
    )
    res.raise_for_status()
    return res.json()


def verify_payment(tienda, invoice_id):
    res = httpx.get(
        f"{tienda.btcpay_url.rstrip('/')}/api/v1/stores/{tienda.btcpay_store_id}/invoices/{invoice_id}",
        headers={"Authorization": f"token {tienda.btcpay_api_key}"},
        timeout=10,
    )
    res.raise_for_status()
    return res.json()["status"]  # 'New' | 'Processing' | 'Settled' | 'Expired'


def verify_webhook_signature(secret, body_bytes, sig_header):
    """Validate BTCPay-Sig: sha256=<hmac> header."""
    if not secret or not sig_header:
        return False
    mac = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(expected, sig_header)
