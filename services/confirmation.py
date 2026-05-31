from services.contract import generate_contract_pdf
from services.email import send_customer_confirmation, send_order_confirmed_owner


def confirm_order(orden):
    """
    Confirma una orden: cambia estado, genera PDF del contrato, envía emails.
    Llamar desde: pago_status (BTCPay settle) y panel admin (acción manual).
    """
    orden.estado = 'confirmed'
    orden.save(update_fields=['estado'])

    try:
        generate_contract_pdf(orden)
    except Exception:
        pass

    try:
        send_customer_confirmation(orden)
    except Exception:
        pass

    try:
        send_order_confirmed_owner(orden)
    except Exception:
        pass
