import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")


def check_email_configuration() -> bool:
    """Check if email service is properly configured"""
    return bool(EMAIL_HOST_USER and EMAIL_HOST_PASSWORD)


def send_verification_email(to_email: str, verification_code: str, username: str) -> bool:
    """Send the registration verification code by email.

    Returns False (without raising) if email isn't configured or sending fails,
    so callers can decide how to handle that rather than crash the request.
    """
    if not check_email_configuration():
        logger.warning(
            f"Email service not configured (EMAIL_HOST_USER/EMAIL_HOST_PASSWORD missing). "
            f"Skipping send to {to_email}; verification code was: {verification_code}"
        )
        return False

    subject = "Votre code de vérification pour SothemaAI"

    html_content = f"""
    <html>
        <body>
            <p>Bonjour {username},</p>
            <p>Merci de vous être inscrit sur SothemaAI.</p>
            <p>Votre code de vérification est : <strong>{verification_code}</strong></p>
            <p>Ce code expirera dans 15 minutes.</p>
            <p>Si vous n'avez pas demandé cette inscription, veuillez ignorer cet e-mail.</p>
            <p>Cordialement,<br>L'équipe SothemaAI</p>
        </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["From"] = EMAIL_HOST_USER
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(html_content, "html"))

    try:
        logger.info(f"Tentative d'envoi de l'e-mail de vérification à {to_email} via {EMAIL_HOST}:{EMAIL_PORT}")
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.sendmail(EMAIL_HOST_USER, to_email, message.as_string())
        logger.info(f"E-mail de vérification envoyé avec succès à {to_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Erreur d'authentification SMTP lors de l'envoi de l'e-mail à {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'e-mail de vérification à {to_email}: {e}", exc_info=True)
        return False
