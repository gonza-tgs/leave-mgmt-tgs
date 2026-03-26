import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
from app.constants import TIPO_PERMISO_LABELS, JORNADA_LABELS

def send_approval_email(solicitud, user_profile):
    """Envía un correo de aprobación al usuario."""
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD]):
        print("SMTP no configurado. Saltando envío de correo.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_FROM
        msg['To'] = user_profile['email']
        msg['Subject'] = f"Permiso Aprobado — {solicitud['fecha_inicio']}"

        tipo_label = TIPO_PERMISO_LABELS.get(solicitud['tipo_permiso'], solicitud['tipo_permiso'])
        jornada_label = JORNADA_LABELS.get(solicitud['jornada'], solicitud['jornada'])

        body = f"""
        Estimado/a {user_profile['full_name']},

        Te informamos que tu solicitud de permiso de tipo "{tipo_label}" 
        para el día {solicitud['fecha_inicio']} ({jornada_label}) ha sido APROBADA.

        Este es un mensaje automático del Sistema de Gestión de Permisos del Colegio TGS.
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_FROM, user_profile['email'], text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False
