import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from pathlib import Path

# Setup logging
logger = logging.getLogger("email_service")
logger.setLevel(logging.INFO)

# Log file
file_handler = logging.FileHandler("logs/email_errors.log")
file_handler.setLevel(logging.ERROR)
logger.addHandler(file_handler)


class EmailService:
    def __init__(self, smtp_server, smtp_port, smtp_user, smtp_password, use_tls=True):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.use_tls = use_tls

    def send_email(self, to_email, subject, template_name, context={}):
        try:
            html_content = self._load_template(template_name, context)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_user
            msg["To"] = to_email

            part2 = MIMEText(html_content, "html")
            msg.attach(part2)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, to_email, msg.as_string())

            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False


    def _load_template(self, template_name, context):
        """
        Load HTML template & replace {{variables}} with actual values
        """
        template_path = Path(f"app/email_templates/{template_name}.html")

        if not template_path.exists():
            raise FileNotFoundError(f"Email template '{template_name}' not found.")

        content = template_path.read_text()

        for key, value in context.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))

        return content

# Add this at the bottom of your email_service.py file
def send_email(to_email, subject, template_name, context={}):
    """
    Standalone function for easy importing
    """
    from flask import current_app
    
    email_service = EmailService(
        smtp_server=current_app.config.get('SMTP_SERVER'),
        smtp_port=current_app.config.get('SMTP_PORT', 587),
        smtp_user=current_app.config.get('EMAIL_USER'),
        smtp_password=current_app.config.get('EMAIL_PASSWORD'),
        use_tls=True
    )
    
    return email_service.send_email(to_email, subject, template_name, context)