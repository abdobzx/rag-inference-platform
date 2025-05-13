import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)

# Récupérer les configurations d'email depuis les variables d'environnement
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587  # Port pour TLS
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER") # Votre adresse email Gmail
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD") # Votre mot de passe d'application Gmail

def send_verification_email(to_email: str, verification_code: str, username: str):
    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        logger.error("Les variables d'environnement EMAIL_HOST_USER ou EMAIL_HOST_PASSWORD ne sont pas définies. Impossible d'envoyer l'e-mail.")
        logger.warning(f"SIMULATION D'ENVOI D'EMAIL (car identifiants non configurés) à {to_email} avec le code {verification_code}")
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
            server.starttls()  # Activer le chiffrement TLS
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.sendmail(EMAIL_HOST_USER, to_email, message.as_string())
        logger.info(f"E-mail de vérification envoyé avec succès à {to_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Erreur d'authentification SMTP lors de l'envoi de l'e-mail à {to_email}: {e}")
        logger.error("Veuillez vérifier que EMAIL_HOST_USER et EMAIL_HOST_PASSWORD sont corrects et que l'accès pour les applications moins sécurisées est activé ou qu'un mot de passe d'application est utilisé pour Gmail.")
        return False
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'e-mail de vérification à {to_email}: {e}", exc_info=True)
        return False

