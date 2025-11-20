from flask import Blueprint, jsonify
from app.controllers.attendance_monitor_controller import get_attendance_monitor_summary
from app.controllers.reminder_controller import send_manual_reminders, send_targeted_reminders
from app.utils.access_control import require_role
from flasgger import swag_from
from flask_jwt_extended import jwt_required

monitor_bp = Blueprint("monitor_bp", __name__)

@monitor_bp.get("/monitor/attendance")
@jwt_required()
@require_role(["super admin", "state admin"])
@swag_from({
    "tags": ["Attendance Monitoring"],
    "summary": "Get attendance submission summary",
    "description": "Returns a summary of which states, regions, districts, groups, and old groups have submitted or not submitted attendance.",
    "security": [{"BearerAuth": []}],
    "responses": {
        200: {
            "description": "Attendance summary data",
            "examples": {
                "application/json": {
                    "submitted": {
                        "states": ["Lagos", "Rivers"],
                        "regions": ["Region 1"],
                        "districts": ["District 4"],
                        "groups": ["Group A"]
                    },
                    "pending": {
                        "states": ["Abuja"],
                        "regions": ["Region 3"],
                        "districts": ["District 6"],
                        "groups": ["Group B"]
                    }
                }
            }
        },
        403: {"description": "Unauthorized — role not allowed"},
    }
})
def attendance_monitor():
    return jsonify(get_attendance_monitor_summary()), 200


@monitor_bp.post("/monitor/remind/<entity_type>")
@jwt_required()
@require_role(["super admin"])
@swag_from({
    "tags": ["Reminders"],
    "summary": "Send manual attendance reminders",
    "description": "Triggers manual reminder emails to all admins under the specified entity type (state, region, district, group, old_group).",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "entity_type",
            "in": "path",
            "required": True,
            "schema": {"type": "string", "enum": ["state", "region", "district", "group", "old_group"]},
            "description": "Hierarchy level to send reminders to."
        }
    ],
    "responses": {
        200: {
            "description": "Emails sent successfully",
            "examples": {"application/json": {"sent_to": ["admin1@gmail.com", "admin2@gmail.com"]}}
        },
        400: {"description": "Invalid entity type"},
    }
})
def manual_remind(entity_type):
    valid = ["state", "region", "district", "group", "old_group"]
    if entity_type not in valid:
        return jsonify({"error": "Invalid entity type"}), 400

    emails = send_manual_reminders(entity_type)
    return jsonify({"sent_to": emails}), 200

# NEW: Target-specific reminder
@monitor_bp.post("/monitor/remind/<entity_type>/<entity_id>")
@jwt_required()
@require_role(["super admin"])
@swag_from({
    "tags": ["Attendance Reminders"],
    "summary": "Send attendance reminder to a specific entity",
    "description": "Sends a reminder email to all admins belonging to a specific entity (state, region, district, group, or old_group).",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "entity_type",
            "in": "path",
            "required": True,
            "type": "string",
            "enum": ["state", "region", "district", "group", "old_group"],
            "description": "The entity level to target."
        },
        {
            "name": "entity_id",
            "in": "path",
            "required": True,
            "type": "integer",
            "description": "ID of the specific entity."
        }
    ],
    "responses": {
        200: {
            "description": "Reminder emails sent successfully",
            "examples": {
                "application/json": {
                    "sent_to": ["admin1@gmail.com", "admin2@gmail.com"]
                }
            }
        },
        400: {"description": "Invalid entity type or entity not found"},
    }
})
def targeted_remind(entity_type, entity_id):
    valid = ["state", "region", "district", "group", "old_group"]
    if entity_type not in valid:
        return jsonify({"error": "Invalid entity type"}), 400

    emails = send_targeted_reminders(entity_type, entity_id)
    return jsonify({"sent_to": emails}), 200