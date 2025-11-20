from app.utils.email_service import send_email
from app.utils.attendance_monitor import get_last_attendance_week, get_attendance_status
from app.models import User
from app.models.hierarchy import State, Region, District, Group, OldGroup
from app.utils.email_service import EmailService

def send_manual_reminders(entity_type):
    """
    entity_type: state / region / district / group / old_group
    """

    failed_list = []

    

    users = User.query.all()

    for user in users:
        last_week = get_last_attendance_week(entity_type, user.state_id)

        if last_week == 0 or get_attendance_status(last_week) != "green":
            send_email(
                to=user.email,
                subject="Attendance Reminder",
                body=f"Dear {user.name or user.email}, you have not submitted attendance for week {last_week}. Kindly update it."
            )
            failed_list.append(user.email)

    return failed_list

def send_targeted_reminders(entity_type, entity_id):
    model_map = {
        "state": State,
        "region": Region,
        "district": District,
        "group": Group,
        "old_group": OldGroup,
    }

    Model = model_map[entity_type]
    entity = Model.query.get(entity_id)

    if not entity:
        return []

    admin_emails = [user.email for user in entity.admins]  # depends on your relationship
    
    email_service = EmailService()
    for email in admin_emails:
        email_service.send_email(
            to_email=email,
            subject="Attendance Reminder",
            template_name="attendance_reminder",
            context={"name": email}  
        )

    return admin_emails
