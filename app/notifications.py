import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
from app.constants import TIPO_PERMISO_LABELS, JORNADA_LABELS


def _send_email(to: str | list, subject: str, body: str) -> bool:
    """Envía un correo. Retorna True si fue exitoso."""
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD]):
        print("SMTP no configurado. Saltando envío de correo.")
        return False
    try:
        recipients = to if isinstance(to, list) else [to]
        msg = MIMEMultipart()
        msg['From'] = SMTP_FROM
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        # FIXED: #2 — use context manager to guarantee quit() on failure
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, recipients, msg.as_string())
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("No se pudo enviar el correo: %s", e, exc_info=True)
        return False


def send_new_request_email(solicitud, user_profile, admin_emails: list) -> bool:
    """Notifica a los administradores sobre una nueva solicitud."""
    if not admin_emails:
        return False
    tipo_label = TIPO_PERMISO_LABELS.get(solicitud['tipo_permiso'], solicitud['tipo_permiso'])
    jornada_label = JORNADA_LABELS.get(solicitud['jornada'], solicitud['jornada'])
    subject = f"Nueva solicitud de permiso — {user_profile['full_name']}"
    
    admin_nota = solicitud.get('admin_nota', '')
    razon_sistema = f"\nMotivo derivación: {admin_nota.replace('SISTEMA: ', '')}" if admin_nota.startswith("SISTEMA:") else ""

    body = f"""
Nueva solicitud de permiso recibida:

Docente: {user_profile['full_name']} ({user_profile['email']})
Tipo: {tipo_label}
Fecha: {solicitud['fecha_inicio']}
Jornada: {jornada_label}
Motivo Docente: {solicitud.get('motivo') or 'Sin motivo'}{razon_sistema}

Ingresa al sistema para revisarla y aprobarla o rechazarla.

Este es un mensaje automático de Quiero mi Permiso! - Colegio TGS.
    """
    return _send_email(admin_emails, subject, body)



def send_approval_email(solicitud, user_profile) -> bool:
    """Notifica al usuario que su solicitud fue aprobada."""
    tipo_label = TIPO_PERMISO_LABELS.get(solicitud['tipo_permiso'], solicitud['tipo_permiso'])
    jornada_label = JORNADA_LABELS.get(solicitud['jornada'], solicitud['jornada'])
    subject = f"Permiso Aprobado — {solicitud['fecha_inicio']}"
    body = f"""
Estimado/a {user_profile['full_name']},

Tu solicitud de permiso ha sido APROBADA.

Tipo: {tipo_label}
Fecha: {solicitud['fecha_inicio']}
Jornada: {jornada_label}

Este es un mensaje automático de Quiero mi Permiso! - Colegio TGS.
    """
    return _send_email(user_profile['email'], subject, body)


def send_rejection_email(solicitud, user_profile, admin_nota: str = "") -> bool:
    """Notifica al usuario que su solicitud fue rechazada."""
    tipo_label = TIPO_PERMISO_LABELS.get(solicitud['tipo_permiso'], solicitud['tipo_permiso'])
    jornada_label = JORNADA_LABELS.get(solicitud['jornada'], solicitud['jornada'])
    subject = f"Solicitud de Permiso Rechazada — {solicitud['fecha_inicio']}"
    nota_linea = f"\nNota del administrador: {admin_nota}" if admin_nota else ""
    body = f"""
Estimado/a {user_profile['full_name']},

Tu solicitud de permiso ha sido RECHAZADA.

Tipo: {tipo_label}
Fecha: {solicitud['fecha_inicio']}
Jornada: {jornada_label}{nota_linea}

Si tienes dudas, contacta a la dirección del colegio.

Este es un mensaje automático de Quiero mi Permiso! - Colegio TGS.
    """
    return _send_email(user_profile['email'], subject, body)
