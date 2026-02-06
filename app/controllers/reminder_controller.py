from app.utils.notification_service import notification_service
from app.utils.attendance_monitor import get_last_attendance_week, get_attendance_status, get_notification_recipients
from app.models import User
from app.models.hierarchy import State, Region, District, Group, OldGroup


def send_manual_reminders(entity_type, methods=['email', 'whatsapp']):
    failed_list = []
    notification_results = []

    # Get ALL entities of this type
    model_map = {
        "state": State, "region": Region, "district": District,
        "group": Group, "old_group": OldGroup
    }
    Model = model_map.get(entity_type)
    if not Model:
        return {"error": "Invalid entity_type"}

    all_entities = Model.query.all()

    for entity in all_entities:
        recipients = get_notification_recipients(entity_type, entity)
        
        last_week = get_last_attendance_week(entity_type, entity.id)

        for user in recipients:
            if get_attendance_status(last_week) != "green":
                results = notification_service.send_attendance_reminder(
                    user=user,
                    week=last_week,
                    methods=methods
                )

                notification_results.append({
                    'entity': entity.name,
                    'user': user.email,
                    'results': results
                })

                if not results['email_sent'] and not results['whatsapp_sent']:
                    failed_list.append(f"{entity.name} → {user.email}")

    return {
        'failed_list': failed_list,
        'notification_results': notification_results,
        'total_notifications_attempted': len(notification_results)
    }


# new implementation to include the leaders across the hierarchy levels
def send_targeted_reminders(entity_type, entity_id, methods=['email', 'whatsapp']):
    model_map = {
        "state": State,
        "region": Region,
        "district": District,
        "group": Group,
        "old_group": OldGroup,
    }
    
    Model = model_map.get(entity_type)
    if not Model:
        return {"error": "Invalid entity_type"}

    entity = Model.query.get(entity_id)
    if not entity:
        return {"error": "Entity not found"}

    # ── Main change here ────────────────────────────────
    recipients = get_notification_recipients(entity_type, entity)
    # ─────────────────────────────────────────────────────

    notification_results = []
    
    last_week = get_last_attendance_week(entity_type, entity.id)  # ← note: entity.id, not user.state_id

    for user in recipients:
        results = notification_service.send_attendance_reminder(
            user=user,
            week=last_week,
            methods=methods
        )
        
        notification_results.append({
            'user': user.email,
            'name': user.name,
            'is_leader': user.id == 0,  # heuristic — real users have real ids
            'results': results
        })

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity.name,
        "notification_results": notification_results,
        "total_sent_to": len(recipients)
    }

