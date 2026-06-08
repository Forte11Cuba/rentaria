import logging
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def _config_from_shop(tienda):
    if not tienda or not tienda.smtp_configured():
        return None
    return {
        'host': tienda.smtp_host,
        'port': tienda.smtp_port,
        'user': tienda.smtp_user,
        'password': tienda.smtp_password,
        'use_tls': tienda.smtp_use_tls,
        'from_email': tienda.smtp_from_email,
        'from_name': tienda.smtp_from_name or tienda.nombre,
    }


def _config_from_platform():
    from apps.shops.models import PlatformSMTPConfig
    platform = PlatformSMTPConfig.get()
    if not platform.is_configured():
        return None
    return {
        'host': platform.smtp_host,
        'port': platform.smtp_port,
        'user': platform.smtp_user,
        'password': platform.smtp_password,
        'use_tls': platform.smtp_use_tls,
        'from_email': platform.smtp_from_email,
        'from_name': platform.smtp_from_name,
    }


def _send_smtp(config, *, to, subject, html, attachments=None):
    from_addr = f'{config["from_name"]} <{config["from_email"]}>'
    recipients = to if isinstance(to, list) else [to]

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = recipients[0]
    msg.attach(MIMEText(html, 'html'))

    if attachments:
        for att in attachments:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(bytes(att['content']))
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{att["filename"]}"')
            msg.attach(part)

    try:
        if config['use_tls']:
            server = smtplib.SMTP(config['host'], config['port'])
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(config['host'], config['port'])
        server.login(config['user'], config['password'])
        server.sendmail(config['from_email'], recipients, msg.as_string())
        server.quit()
        return True
    except Exception:
        logger.exception('Error enviando email SMTP a %s', to)
        return False


def _send_resend(*, to, subject, html, from_addr, attachments=None):
    import resend
    api_key = os.environ.get('RESEND_API_KEY', '')
    if not api_key:
        logger.info('[EMAIL — sin API key Resend, no enviado] To: %s Subject: %s', to, subject)
        return False
    resend.api_key = api_key
    params = {
        'from': from_addr,
        'to': to if isinstance(to, list) else [to],
        'subject': subject,
        'html': html,
    }
    if attachments:
        params['attachments'] = attachments
    try:
        resend.Emails.send(params)
        return True
    except Exception:
        logger.exception('Error enviando email Resend a %s', to)
        return False


def send(*, to, subject, html, tienda=None, from_addr=None, attachments=None):
    """
    Prioridad: SMTP tienda → SMTP plataforma → Resend fallback.
    """
    config = _config_from_shop(tienda) or _config_from_platform()
    if config:
        return _send_smtp(config, to=to, subject=subject, html=html, attachments=attachments)
    return _send_resend(to=to, subject=subject, html=html, from_addr=from_addr, attachments=attachments)
