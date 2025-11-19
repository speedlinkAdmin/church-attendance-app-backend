from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.email_service import EmailService
from app.models.user import User
from app.extensions import db
import logging

logger = logging.getLogger("attendance_scheduler")

def weekly_email_job():
    try:
        email_service = EmailService()

        admins = User.query.filter(User.role.in_([
            "super admin", "state admin", "region admin",
            "district admin", "group admin"
        ])).all()

        for admin in admins:
            email_service.send_email(
                to_email=admin.email,
                subject="Weekly Church Attendance Reminder",
                template_name="attendance_reminder",
                context={"name": admin.name}
            )

        logger.info(f"Weekly reminder sent to {len(admins)} admins.")

    except Exception as e:
        logger.error(f"Weekly email job failed: {str(e)}")


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(weekly_email_job, "cron", day_of_week="mon", hour=6)
    scheduler.start()
