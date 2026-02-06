from app.utils.email_service import EmailService
from app.utils.whatsapp_service import whatsapp_service
import os

class NotificationService:
    def __init__(self):
        # Get email configuration from environment variables or config
        smtp_server = os.getenv('EMAIL_SERVER')
        smtp_port = int(os.getenv('EMAIL_PORT', 587))
        smtp_user = os.getenv('EMAIL_USERNAME')
        smtp_password = os.getenv('EMAIL_PASSWORD')
        
        # Initialize EmailService with required parameters
        self.email_service = EmailService()
    
    def send_attendance_reminder(self, user, week, methods=['email', 'whatsapp']):
        """
        Send attendance reminder via multiple channels
        """
        results = {
            'email_sent': False,
            'whatsapp_sent': False,
            'email_error': None,
            'whatsapp_error': None
        }
        
        context = {
            "name": user.name or user.email,
            "week": week
        }
        
        # Send email
        if 'email' in methods and user.email:
            try:
                # Use the email_service instance with send_email method
                self.email_service.send_email(
                    to_email=user.email,
                    subject="Attendance Reminder",
                    template_name="attendance_reminder",
                    context=context
                )
                results['email_sent'] = True
            except Exception as e:
                results['email_error'] = str(e)
        
        # Send WhatsApp
        if 'whatsapp' in methods and user.phone:
            try:
                whatsapp_service.send_attendance_reminder(
                    to_phone=user.phone,
                    name=context["name"],
                    week=week
                )
                results['whatsapp_sent'] = True
            except Exception as e:
                results['whatsapp_error'] = str(e)
        
        return results

# Global instance
notification_service = NotificationService()