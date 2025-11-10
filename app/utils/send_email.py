import smtplib
from email.message import EmailMessage
import os


def send_email(to_email: str, reset_url: str):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_tls = os.getenv("SMTP_TLS", "1").lower() in ("1", "true", "yes")
    smtp_ssl = os.getenv("SMTP_SSL", "0").lower() in ("1", "true", "yes")

    msg = EmailMessage()
    msg["Subject"] = "Recuperación de contraseña"
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.set_content(
        "Para restablecer tu contraseña, haz clic en el siguiente enlace:\n" + reset_url
    )

    html_content = f"""
    <html>
        <body>
            <p>Para restablecer tu contraseña, haz clic en el siguiente enlace:</p>
            <p><a href="{reset_url}">Restablecer contraseña</a></p>
            <p>Este enlace es válido por 1 hora.</p>
        </body>
    </html>
    """
    msg.add_alternative(html_content, subtype="html")

    if smtp_ssl:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_tls:
                server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
