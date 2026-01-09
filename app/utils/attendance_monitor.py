from datetime import datetime
from app.models import Attendance, State, Region, District, Group, OldGroup
from app.models import User
from typing import List, Optional

CURRENT_YEAR = datetime.utcnow().year
CURRENT_MONTH = datetime.utcnow().strftime("%B")  # e.g. January
CURRENT_WEEK = datetime.utcnow().isocalendar().week % 4 or 4

def get_last_attendance_week(entity_type: str, entity_id: int):
    """Return the last week for which the entity submitted attendance."""
    query = Attendance.query.filter_by(
        year=CURRENT_YEAR,
        month=CURRENT_MONTH
    )

    if entity_type == "state":
        query = query.filter_by(state_id=entity_id)
    elif entity_type == "region":
        query = query.filter_by(region_id=entity_id)
    elif entity_type == "district":
        query = query.filter_by(district_id=entity_id)
    elif entity_type == "group":
        query = query.filter_by(group_id=entity_id)
    elif entity_type == "old_group":
        query = query.filter_by(old_group_id=entity_id)

    last_record = query.order_by(Attendance.week.desc()).first()
    return last_record.week if last_record else 0
   

def get_attendance_status(last_filled_week):
    """Return status type: red/yellow/green"""
    if last_filled_week == 0:
        return "red"

    missing = CURRENT_WEEK - last_filled_week

    if missing >= 5:
        return "red"
    elif missing >= 1:
        return "yellow"
    else:
        return "green"


def get_notification_recipients(entity_type: str, entity) -> List[User]:
    """
    Returns list of User objects that should receive notifications for this entity.
    Includes: all .admins + the entity's own leader (if exists)
    """
    recipients = []

    # Add all admins (they are real User objects)
    if hasattr(entity, 'admins') and entity.admins:
        recipients.extend(entity.admins)

    # Add the dedicated leader — create a temporary "fake" User object
    if entity.leader_email:
        leader_user = User(
            id=0,                     # dummy id - not persisted
            name=entity.leader or "Leader",
            email=entity.leader_email,
            phone=entity.leader_phone
        )
        # Prevent duplicate if leader is already an admin (same email)
        if not any(u.email == leader_user.email for u in recipients):
            recipients.append(leader_user)

    return recipients