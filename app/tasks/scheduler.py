from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import logging

from app.extensions import db
from app.utils.email_service import EmailService
from app.utils.whatsapp_service import WhatsAppService
from app.models import (
    Attendance, State, Region, District, Group, OldGroup
)
from app.models.user import User

logger = logging.getLogger("attendance_scheduler")

CURRENT_YEAR = datetime.utcnow().year
CURRENT_MONTH = datetime.utcnow().strftime("%B")
CURRENT_WEEK = datetime.utcnow().isocalendar().week % 4 or 4


def attendance_notification_job():
    try:
        email_service = EmailService()
        whatsapp_service = WhatsAppService()

        def _send_notifications(
            name,
            email,
            phone,
            entity_filter,
            email_service,
            whatsapp_service
        ):
            last_record = Attendance.query.filter_by(
                year=CURRENT_YEAR,
                month=CURRENT_MONTH,
                **entity_filter
            ).order_by(Attendance.week.desc()).first()

            last_week = last_record.week if last_record else 0
            missing_weeks = CURRENT_WEEK - last_week

            # 🟡 WEEKLY MONDAY REMINDER
            if datetime.utcnow().weekday() == 0:  # Monday
                email_service.send_email(
                    to_email=email,
                    subject="Weekly Church Attendance Reminder",
                    template_name="weekly_attendance_reminder",
                    context={"name": name}
                )

            # 🔴 OVERDUE (4+ WEEKS)
            if missing_weeks >= 4:
                weeks = ", ".join(str(w) for w in range(last_week + 1, CURRENT_WEEK + 1))

                email_service.send_email(
                    to_email=email,
                    subject="URGENT: Attendance Overdue",
                    template_name="attendance_overdue",
                    context={
                        "name": name,
                        "week": weeks
                    }
                )

                if phone:
                    whatsapp_service.send_message(
                        to_phone=phone,
                        message=(
                            f"Hello {name},\n\n"
                            f"You have not submitted attendance for weeks {weeks}.\n"
                            f"Please update immediately.\n\n"
                            f"Thank you."
                        )
                    )

        def _build_entity_filter(entity):
            if isinstance(entity, State):
                return {"state_id": entity.id}
            if isinstance(entity, Region):
                return {"region_id": entity.id}
            if isinstance(entity, District):
                return {"district_id": entity.id}
            if isinstance(entity, Group):
                return {"group_id": entity.id}
            if isinstance(entity, OldGroup):
                return {"old_group_id": entity.id}
            return {}


        # 1️⃣ GROUP ADMINS ONLY
        group_admins = User.query.filter_by(role="group admin").all()

        for admin in group_admins:
            _send_notifications(
                name=admin.name,
                email=admin.email,
                phone=admin.phone,
                entity_filter={"group_id": admin.group_id},
                email_service=email_service,
                whatsapp_service=whatsapp_service
            )

        # 2️⃣ ALL LEADERS ACROSS ENTITIES
        entities = (
            list(State.query.all()) +
            list(Region.query.all()) +
            list(District.query.all()) +
            list(Group.query.all()) +
            list(OldGroup.query.all())
        )

        for entity in entities:
            if not entity.leader_email:
                continue

            entity_filter = _build_entity_filter(entity)

            _send_notifications(
                name=entity.leader or "Leader",
                email=entity.leader_email,
                phone=entity.leader_phone,
                entity_filter=entity_filter,
                email_service=email_service,
                whatsapp_service=whatsapp_service
            )

        logger.info("✅ Attendance notification job completed")

    except Exception:
        logger.error("❌ Attendance notification job failed", exc_info=True)


def run_job_with_context(app):
    with app.app_context():
        attendance_notification_job()


def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=lambda: run_job_with_context(app),
        trigger="cron",
        day_of_week="mon",
        hour=6
    )
    scheduler.start()












# from apscheduler.schedulers.background import BackgroundScheduler
# from app.utils.email_service import EmailService
# from app.models.user import User
# from app.extensions import db
# import logging

# from app.utils.whatsapp_service import WhatsAppService

# logger = logging.getLogger("attendance_scheduler")

# def weekly_email_job():
#     try:
#         email_service = EmailService()
#         whatsapp_service = WhatsAppService()

#          # 🔧 TEST VARIABLES (NO DATABASE YET)
#         test_name = "Edward"
#         test_email = "edward.ndiyo@speedlinkng.com"
#         test_phone = "2347064952367"  # fake/test number

#         # EMAIL TEST
#         email_service.send_email(
#             to_email=test_email,
#             subject="TEST: Attendance Reminder",
#             template_name="attendance_reminder",
#             context={
#                 "name": test_name,
#                 "week": 3  # test value
#             }
#         )

#         # WHATSAPP TEST
#         sent = whatsapp_service.send_message(
#             to_phone=test_phone,
#             message=f"Hello {test_name}, this is a TEST attendance reminder."
#         )

#         # logger.info("✅ TEST notification job executed successfully")
#         logger.info(f"WhatsApp sent result: {sent}")
        

#     except Exception as e:
#         logger.error(f"❌ Notification job failed: {str(e)}", exc_info=True)

# def run_job_with_context(app):
#     with app.app_context():
#         weekly_email_job()


# def start_scheduler(app):
#     scheduler = BackgroundScheduler()
#     # scheduler.add_job(weekly_email_job, "cron", day_of_week="mon", hour=6)
#     scheduler.add_job(
#         func=lambda: run_job_with_context(app),
#         trigger="interval",
#         minutes=10
#     )
#     scheduler.start()
