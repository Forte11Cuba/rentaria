from services.contrato import generar_pdf_contrato
from services.email import enviar_confirmacion_cliente, enviar_orden_confirmada_dueno


def confirmar_orden(orden):
    """
    Confirma una orden: cambia estado, genera PDF del contrato, envía emails.
    Llamar desde: pago_status (BTCPay settle) y panel admin (acción manual).
    """
    orden.estado = 'confirmada'
    orden.save(update_fields=['estado'])

    try:
        generar_pdf_contrato(orden)
    except Exception:
        pass

    try:
        enviar_confirmacion_cliente(orden)
    except Exception:
        pass

    try:
        enviar_orden_confirmada_dueno(orden)
    except Exception:
        pass
