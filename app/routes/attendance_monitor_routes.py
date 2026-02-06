from flask import Blueprint, jsonify, request
from app.controllers.attendance_monitor_controller import get_attendance_monitor_summary
from app.controllers.reminder_controller import send_manual_reminders, send_targeted_reminders
from app.models.hierarchy import Group, OldGroup, District, Region, State
from app.models.user import User    
from app.utils.access_control import require_role
from flasgger import swag_from
from flask_jwt_extended import get_jwt_identity, jwt_required

monitor_bp = Blueprint("monitor_bp", __name__)


@monitor_bp.get("/monitor/attendance")
@jwt_required()
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
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    print(f"🔍 Attendance Monitor - Current user: {current_user.id}, Roles: {[r.name for r in current_user.roles]}")
    print(f"🔍 User hierarchy - State: {current_user.state_id}, Region: {current_user.region_id}, District: {current_user.district_id}, Group: {current_user.group_id}, OldGroup: {current_user.old_group_id}")


    def build_submission_index(summary):
        index = {
            "submitted": {
                "states": [],
                "regions": [],
                "districts": [],
                "groups": []
            },
            "pending": {
                "states": [],
                "regions": [],
                "districts": [],
                "groups": []
            }
        }

        STATUS_TO_BUCKET = {
            "green": "submitted",
            "yellow": "pending",
            "red": "pending"
        }

        for state in summary.get("states", []):
            bucket = STATUS_TO_BUCKET.get(state["status"])
            if not bucket:
                continue  # safety guard

            index[bucket]["states"].append({
                "id": state["id"],
                "name": state["name"],
                "last_filled_week": state["last_filled_week"]
            })

        for region in summary.get("regions", []):
            bucket = STATUS_TO_BUCKET.get(region["status"])
            if not bucket:
                continue

            index[bucket]["regions"].append({
                "id": region["id"],
                "name": region["name"],
                "last_filled_week": region["last_filled_week"]
            })

        for district in summary.get("districts", []):
            bucket = STATUS_TO_BUCKET.get(district["status"])
            if not bucket:
                continue

            index[bucket]["districts"].append({
                "id": district["id"],
                "name": district["name"],
                "last_filled_week": district["last_filled_week"]
            })

        for group in summary.get("groups", []):
            bucket = STATUS_TO_BUCKET.get(group["status"])
            if not bucket:
                continue

            index[bucket]["groups"].append({
                "id": group["id"],
                "name": group["name"],
                "last_filled_week": group["last_filled_week"]
            })

        return index


    # def format_submission_summary(summary):
    #     result = {
    #         "submitted": {
    #             "states": [],
    #             "regions": [],
    #             "districts": [],
    #             "groups": []
    #         },
    #         "pending": {
    #             "states": [],
    #             "regions": [],
    #             "districts": [],
    #             "groups": []
    #         }
    #     }

    #     for state in summary.get("states", []):
    #         key = "submitted" if state["status"] == "submitted" else "pending"
    #         result[key]["states"].append(state["name"])

    #     for region in summary.get("regions", []):
    #         key = "submitted" if region["status"] == "submitted" else "pending"
    #         result[key]["regions"].append(region["name"])

    #     for district in summary.get("districts", []):
    #         key = "submitted" if district["status"] == "submitted" else "pending"
    #         result[key]["districts"].append(district["name"])

    #     for group in summary.get("groups", []):
    #         key = "submitted" if group["status"] == "submitted" else "pending"
    #         result[key]["groups"].append(group["name"])

    #     return result
    
    # Get the full summary first
    full_summary = get_attendance_monitor_summary()
    
    # Check if user is Super Admin
    user_roles = [role.name for role in current_user.roles]
    is_super_admin = "Super Admin" in user_roles
    
    # if is_super_admin:
    #     print("🎯 Super Admin detected - returning full summary")
    #     return jsonify(full_summary), 200

    if is_super_admin:
        return jsonify({
            "data": full_summary,
            "summary": build_submission_index(full_summary)
        }), 200

        # return jsonify(format_submission_summary(full_summary)), 200
    
    # For non-Super Admins, filter based on hierarchy
    print("👤 Regular admin - filtering summary based on hierarchy")
    
    filtered_summary = {
        "states": [],
        "regions": [],
        "districts": [],
        "groups": [],
        "old_groups": []
    }
    
    if "State Admin" in user_roles:
        if not current_user.state_id:
            return jsonify({"error": "State Admin must have a state assigned"}), 400
        
        print(f"🔐 State Admin - filtering for state_id: {current_user.state_id}")
        
        # Filter states - only show user's state
        filtered_summary["states"] = [
            state for state in full_summary["states"] 
            if state["id"] == current_user.state_id
        ]
        
        # Filter regions - only show regions in user's state
        user_state_regions = Region.query.filter_by(state_id=current_user.state_id).all()
        region_ids = [region.id for region in user_state_regions]
        filtered_summary["regions"] = [
            region for region in full_summary["regions"]
            if region["id"] in region_ids
        ]
        
        # Filter districts - only show districts in user's state
        user_state_districts = District.query.filter_by(state_id=current_user.state_id).all()
        district_ids = [district.id for district in user_state_districts]
        filtered_summary["districts"] = [
            district for district in full_summary["districts"]
            if district["id"] in district_ids
        ]
        
        # Filter groups - only show groups in user's state
        user_state_groups = Group.query.filter_by(state_id=current_user.state_id).all()
        group_ids = [group.id for group in user_state_groups]
        filtered_summary["groups"] = [
            group for group in full_summary["groups"]
            if group["id"] in group_ids
        ]
        
        # Filter old_groups - only show old_groups in user's state
        user_state_old_groups = OldGroup.query.filter_by(state_id=current_user.state_id).all()
        old_group_ids = [old_group.id for old_group in user_state_old_groups]
        filtered_summary["old_groups"] = [
            old_group for old_group in full_summary["old_groups"]
            if old_group["id"] in old_group_ids
        ]
        
    elif "Region Admin" in user_roles:
        if not current_user.state_id or not current_user.region_id:
            return jsonify({"error": "Region Admin must have state and region assigned"}), 400
        
        print(f"🔐 Region Admin - filtering for region_id: {current_user.region_id}")
        
        # Filter regions - only show user's region
        filtered_summary["regions"] = [
            region for region in full_summary["regions"]
            if region["id"] == current_user.region_id
        ]
        
        # Filter districts - only show districts in user's region
        user_region_districts = District.query.filter_by(region_id=current_user.region_id).all()
        district_ids = [district.id for district in user_region_districts]
        filtered_summary["districts"] = [
            district for district in full_summary["districts"]
            if district["id"] in district_ids
        ]
        
        # Filter groups - only show groups in user's region
        user_region_groups = Group.query.filter_by(region_id=current_user.region_id).all()
        group_ids = [group.id for group in user_region_groups]
        filtered_summary["groups"] = [
            group for group in full_summary["groups"]
            if group["id"] in group_ids
        ]
        
        # Filter old_groups - only show old_groups in user's region
        user_region_old_groups = OldGroup.query.filter_by(region_id=current_user.region_id).all()
        old_group_ids = [old_group.id for old_group in user_region_old_groups]
        filtered_summary["old_groups"] = [
            old_group for old_group in full_summary["old_groups"]
            if old_group["id"] in old_group_ids
        ]
        
    elif "District Admin" in user_roles:
        if not all([current_user.state_id, current_user.region_id, current_user.district_id]):
            return jsonify({"error": "District Admin must have complete hierarchy assigned"}), 400
        
        print(f"🔐 District Admin - filtering for district_id: {current_user.district_id}")
        
        # Filter districts - only show user's district
        filtered_summary["districts"] = [
            district for district in full_summary["districts"]
            if district["id"] == current_user.district_id
        ]
        
        # Filter groups - only show groups in user's district
        user_district_groups = Group.query.filter_by(district_id=current_user.district_id).all()
        group_ids = [group.id for group in user_district_groups]
        filtered_summary["groups"] = [
            group for group in full_summary["groups"]
            if group["id"] in group_ids
        ]
        
    elif "Group Admin" in user_roles:
        if not all([current_user.state_id, current_user.region_id, current_user.old_group_id, current_user.group_id]):
            return jsonify({"error": "Group Admin must have complete hierarchy assigned (state, region, old_group, group)"}), 400
        
        print(f"🔐 Group Admin - filtering for group_id: {current_user.group_id}")
        
        # Filter groups - only show user's group
        filtered_summary["groups"] = [
            group for group in full_summary["groups"]
            if group["id"] == current_user.group_id
        ]
        
    elif "Old Group Admin" in user_roles:
        if not all([current_user.state_id, current_user.region_id, current_user.old_group_id]):
            return jsonify({"error": "Old Group Admin must have state, region, and old_group assigned"}), 400
        
        print(f"🔐 Old Group Admin - filtering for old_group_id: {current_user.old_group_id}")
        
        # Filter old_groups - only show user's old_group
        filtered_summary["old_groups"] = [
            old_group for old_group in full_summary["old_groups"]
            if old_group["id"] == current_user.old_group_id
        ]
        
        # Filter groups - only show groups in user's old_group
        user_old_group_groups = Group.query.filter_by(old_group_id=current_user.old_group_id).all()
        group_ids = [group.id for group in user_old_group_groups]
        filtered_summary["groups"] = [
            group for group in full_summary["groups"]
            if group["id"] in group_ids
        ]
        
    else:
        return jsonify({"error": "Insufficient permissions to view attendance monitor"}), 403
    
    print(f"🔍 Returning filtered summary with counts - States: {len(filtered_summary['states'])}, Regions: {len(filtered_summary['regions'])}, Districts: {len(filtered_summary['districts'])}, Groups: {len(filtered_summary['groups'])}, Old Groups: {len(filtered_summary['old_groups'])}")


    # return jsonify(filtered_summary), 200
    return jsonify({
        "data": filtered_summary,
        "summary": build_submission_index(filtered_summary)
    }), 200




@monitor_bp.post("/monitor/remind/<entity_type>")
@jwt_required()
# @require_role(["super admin"])
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

    # Get methods from request body (default to both)
    data = request.get_json() or {}
    methods = data.get('methods', ['email', 'whatsapp'])
    
    result = send_manual_reminders(entity_type, methods=methods)
    return jsonify({
        "sent_via": methods,
        "failed_list": result['failed_list'],
        "detailed_results": result['notification_results']
    }), 200
# def manual_remind(entity_type):
#     valid = ["state", "region", "district", "group", "old_group"]
#     if entity_type not in valid:
#         return jsonify({"error": "Invalid entity type"}), 400

#     emails = send_manual_reminders(entity_type)
#     return jsonify({"sent_to": emails}), 200



# NEW: Target-specific reminder
@monitor_bp.post("/monitor/remind/<entity_type>/<entity_id>")
@jwt_required()
# @require_role(["super admin"])
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

    # Get methods from request body (default to both)
    data = request.get_json() or {}
    methods = data.get('methods', ['email', 'whatsapp'])
    
    results = send_targeted_reminders(entity_type, entity_id, methods=methods)
    return jsonify({
        "sent_via": methods,
        "detailed_results": results
    }), 200
