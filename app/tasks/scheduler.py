from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.email_service import EmailService
from app.models.user import User
from app.extensions import db
import logging

from app.utils.whatsapp_service import WhatsAppService

logger = logging.getLogger("attendance_scheduler")

def weekly_email_job():
    try:
        email_service = EmailService()
        whatsapp_service = WhatsAppService()

         # 🔧 TEST VARIABLES (NO DATABASE YET)
        test_name = "Edward"
        test_email = "edward.ndiyo@speedlinkng.com"
        test_phone = "2347064952367"  # fake/test number

        # EMAIL TEST
        email_service.send_email(
            to_email=test_email,
            subject="TEST: Attendance Reminder",
            template_name="attendance_reminder",
            context={
                "name": test_name,
                "week": 3  # test value
            }
        )

        # WHATSAPP TEST
        sent = whatsapp_service.send_message(
            to_phone=test_phone,
            message=f"Hello {test_name}, this is a TEST attendance reminder."
        )

        # logger.info("✅ TEST notification job executed successfully")
        logger.info(f"WhatsApp sent result: {sent}")
        

    except Exception as e:
        logger.error(f"❌ Notification job failed: {str(e)}", exc_info=True)

def run_job_with_context(app):
    with app.app_context():
        weekly_email_job()


def start_scheduler(app):
    scheduler = BackgroundScheduler()
    # scheduler.add_job(weekly_email_job, "cron", day_of_week="mon", hour=6)
    scheduler.add_job(
        func=lambda: run_job_with_context(app),
        trigger="interval",
        minutes=10
    )
    scheduler.start()
