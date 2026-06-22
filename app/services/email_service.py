import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import aiosmtplib
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    async def send_html_email(to_email: str, subject: str, html_content: str) -> bool:
        """
        Sends an HTML email asynchronously using SMTP settings from config.
        """
        # Validate SMTP configuration
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning("SMTP credentials are not configured. Cannot send email.")
            raise ValueError("El servidor de correo (SMTP) no está configurado en el sistema.")

        try:
            # Create message container
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = settings.SMTP_FROM
            message["To"] = to_email

            # Record the MIME type html
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

            # Determine connection type based on port
            use_tls = settings.SMTP_PORT == 465
            
            smtp_client = aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                use_tls=use_tls
            )

            # Connect and send
            async with smtp_client:
                # Login (Gmail App Passwords are displayed with spaces, so we strip them)
                smtp_password = settings.SMTP_PASSWORD
                if "gmail" in settings.SMTP_HOST.lower():
                    smtp_password = smtp_password.replace(" ", "")
                
                await smtp_client.login(settings.SMTP_USER, smtp_password)


                
                # Send email
                await smtp_client.send_message(message)
                
            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise RuntimeError(f"Error al enviar correo electrónico: {str(e)}")
