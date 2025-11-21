from flask import Blueprint, request, jsonify
from ..controllers import attendance_controller
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, Attendance
from ..extensions import db
import csv
from io import StringIO
from ..utils.role_required import role_required
from flasgger import swag_from


attendance_bp = Blueprint("attendance", __name__)

@attendance_bp.route("/attendance", methods=["POST"])
@jwt_required()
@swag_from({
    "tags": ["Attendance"],
    "summary": "Create attendance record",
    "description": "Creates a new attendance record for a specified service type and hierarchy level.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "service_type": {"type": "string", "example": "Sunday Service"},
                    "state_id": {"type": "integer", "example": 1},
                    "region_id": {"type": "integer", "example": 2},
                    "district_id": {"type": "integer", "example": 3},
                    "group_id": {"type": "integer", "example": 4},
                    "old_group_id": {"type": "integer", "example": 5},
                    "month": {"type": "string", "example": "October"},
                    "week": {"type": "integer", "example": 1},
                    "men": {"type": "integer", "example": 45},
                    "women": {"type": "integer", "example": 60},
                    "youth_boys": {"type": "integer", "example": 20},
                    "youth_girls": {"type": "integer", "example": 25},
                    "children_boys": {"type": "integer", "example": 30},
                    "children_girls": {"type": "integer", "example": 28},
                    "year": {"type": "integer", "example": 2025}
                },
                "required": ["service_type", "state_id", "region_id", "month", "week", "year"]
                # CHANGED: district_id is no longer required since it's at the bottom of hierarchy
            }
        }
    ],
    "responses": {
        "201": {
            "description": "Attendance record created successfully",
            "examples": {
                "application/json": {
                    "id": 1,
                    "service_type": "Sunday Service",
                    "month": "October",
                    "week": 1,
                    "year": 2025
                }
            }
        },
        "400": {"description": "Invalid data provided"}
    }
})
def create_attendance():
    data = request.get_json() or {}
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    print(f"🔍 Current user: {current_user.id}, Roles: {[r.name for r in current_user.roles]}")
    print(f"🔍 User hierarchy - State: {current_user.state_id}, Region: {current_user.region_id}, District: {current_user.district_id}")
    print(f"🔍 Received data: {data}")
    
    # Only validate basic required fields for ALL users
    required_fields = ["service_type", "month", "week", "year"]
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
    
    # Check if user is Super Admin
    user_roles = [role.name for role in current_user.roles]
    is_super_admin = "Super Admin" in user_roles
    
    if is_super_admin:
        print("🎯 Super Admin detected - bypassing all hierarchy constraints")
        # Super Admin can create records with any hierarchy values (including null)
        # Use whatever values are provided in the request, no auto-population needed
        # The provided state_id, region_id, district_id can be whatever the Super Admin wants
        
    else:
        # For non-Super Admins, apply hierarchy constraints
        print("👤 Regular admin - applying hierarchy constraints")
        
        if "State Admin" in user_roles:
            if not current_user.state_id:
                return jsonify({"error": "State Admin must have a state assigned"}), 400
            # Auto-populate state_id, allow provided region_id or null
            data['state_id'] = current_user.state_id
            
        elif "Region Admin" in user_roles:
            if not current_user.state_id or not current_user.region_id:
                return jsonify({"error": "Region Admin must have state and region assigned"}), 400
            # Auto-populate both state and region
            data['state_id'] = current_user.state_id
            data['region_id'] = current_user.region_id
            
        elif "District Admin" in user_roles:
            if not all([current_user.state_id, current_user.region_id, current_user.district_id]):
                return jsonify({"error": "District Admin must have complete hierarchy assigned"}), 400
            # Auto-populate all hierarchy levels
            data['state_id'] = current_user.state_id
            data['region_id'] = current_user.region_id
            data['district_id'] = current_user.district_id
            
        else:
            return jsonify({"error": "Insufficient permissions to create attendance records"}), 403
    
    print(f"🔍 Final data being saved: {data}")
    
    try:
        attendance = attendance_controller.create_attendance(data)
        return jsonify(attendance.to_dict()), 201
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
            
# def create_attendance():
#     data = request.get_json() or {}
    
#     # Validate hierarchy relationships according to new structure
#     if data.get('old_group_id'):
#         from ..models import OldGroup
#         old_group = OldGroup.query.get(data['old_group_id'])
#         if not old_group:
#             return jsonify({"error": f"Old Group with ID {data['old_group_id']} does not exist"}), 400
#         # Ensure old_group belongs to the specified region and state
#         if old_group.region_id != data.get('region_id') or old_group.state_id != data.get('state_id'):
#             return jsonify({"error": "Old Group does not belong to the specified region/state"}), 400
    
#     if data.get('group_id'):
#         from ..models import Group
#         group = Group.query.get(data['group_id'])
#         if not group:
#             return jsonify({"error": f"Group with ID {data['group_id']} does not exist"}), 400
#         # Ensure group belongs to the specified old_group, region and state
#         if (group.old_group_id != data.get('old_group_id') or 
#             group.region_id != data.get('region_id') or 
#             group.state_id != data.get('state_id')):
#             return jsonify({"error": "Group does not belong to the specified hierarchy"}), 400
    
#     if data.get('district_id'):
#         from ..models import District
#         district = District.query.get(data['district_id'])
#         if not district:
#             return jsonify({"error": f"District with ID {data['district_id']} does not exist"}), 400
#         # Ensure district belongs to the specified group, old_group, region and state
#         if (district.group_id != data.get('group_id') or
#             district.old_group_id != data.get('old_group_id') or
#             district.region_id != data.get('region_id') or
#             district.state_id != data.get('state_id')):
#             return jsonify({"error": "District does not belong to the specified hierarchy"}), 400
    
#     attendance = attendance_controller.create_attendance(data)
#     return jsonify(attendance.to_dict()), 201





@attendance_bp.route("/attendance/upload", methods=["POST"])
@jwt_required()
@swag_from({
    "tags": ["Attendance"],
    "summary": "Bulk upload attendance via CSV",
    "description": "Allows admins to upload multiple attendance records from a CSV file. The CSV must include headers matching the Attendance model fields.",
    "consumes": ["multipart/form-data"],
    "parameters": [
        {
            "name": "file",
            "in": "formData",
            "type": "file",
            "required": True,
            "description": "CSV file containing attendance data"
        }
    ],
    "responses": {
        "201": {
            "description": "Attendance records uploaded successfully",
            "examples": {"application/json": {"message": "45 attendance records uploaded successfully"}}
        },
        "400": {"description": "Invalid file format or missing CSV column"}
    }
})
def upload_attendance_csv():
    file = request.files.get("file")
    if not file or not file.filename.endswith(".csv"):
        return jsonify({"error": "Invalid file format. Please upload a .csv file."}), 400

    stream = StringIO(file.stream.read().decode("utf-8"))
    csv_reader = csv.DictReader(stream)

    records = []
    for row in csv_reader:
        try:
            # Validate old_group_id exists if provided
            if row.get("old_group_id") and row["old_group_id"].strip():
                from ..models import OldGroup
                old_group = OldGroup.query.get(int(row["old_group_id"]))
                if not old_group:
                    return jsonify({"error": f"Old Group with ID {row['old_group_id']} does not exist"}), 400
            
            # Validate group_id exists if provided
            if row.get("group_id") and row["group_id"].strip():
                from ..models import Group
                group = Group.query.get(int(row["group_id"]))
                if not group:
                    return jsonify({"error": f"Group with ID {row['group_id']} does not exist"}), 400

            attendance = Attendance(
                service_type=row["service_type"],
                state_id=int(row["state_id"]),
                region_id=int(row["region_id"]),
                # district_id=int(row["district_id"]),
                district_id=int(row["district_id"]) if row.get("district_id") and row["district_id"].strip() else None,
                group_id=int(row["group_id"]) if row.get("group_id") and row["group_id"].strip() else None,
                old_group_id=int(row["old_group_id"]) if row.get("old_group_id") and row["old_group_id"].strip() else None,
                month=row["month"],
                week=int(row["week"]),
                men=int(row["men"]),
                women=int(row["women"]),
                youth_boys=int(row["youth_boys"]),
                youth_girls=int(row["youth_girls"]),
                children_boys=int(row["children_boys"]),
                children_girls=int(row["children_girls"]),
                year=int(row["year"]),
            )
            records.append(attendance)
        except KeyError as e:
            return jsonify({"error": f"Missing column in CSV: {e}"}), 400
        except ValueError as e:
            return jsonify({"error": f"Invalid data format in row: {e}"}), 400

    db.session.bulk_save_objects(records)
    db.session.commit()

    return jsonify({"message": f"{len(records)} attendance records uploaded successfully"}), 201


@attendance_bp.route("/attendance", methods=["GET"])
@jwt_required()
@swag_from({
    "tags": ["Attendance"],
    "summary": "Retrieve attendance records",
    "description": "Fetch attendance records based on service type, month, year, and user access level (State Admin, Regional Admin, District Admin).",
    "parameters": [
        {"name": "service_type", "in": "query", "type": "string", "required": False, "description": "Filter by service type"},
        {"name": "year", "in": "query", "type": "integer", "required": False, "description": "Filter by year"},
        {"name": "month", "in": "query", "type": "string", "required": False, "description": "Filter by month"}
    ],
    "responses": {
        "200": {
            "description": "List of attendance records",
            "examples": {
                "application/json": [
                    {"id": 1, "service_type": "Sunday Service", "men": 45, "women": 60, "year": 2025}
                ]
            }
        },
        "401": {"description": "Unauthorized access"}
    }
})
def get_attendance():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    service_type = request.args.get("service_type")
    year = request.args.get("year")
    month = request.args.get("month")
    group_id = request.args.get("group_id")
    old_group_id = request.args.get("old_group_id")

    # Apply filters based on user role
    state_id = region_id = district_id = None
    
    user_role_names = [role.name for role in user.roles] if user.roles else []
    
    if "State Admin" in user_role_names:
        state_id = user.state_id
    elif "Regional Admin" in user_role_names:
        region_id = user.region_id
    elif "District Admin" in user_role_names:
        district_id = user.district_id

    records = attendance_controller.get_all_attendance(
        service_type=service_type,
        state_id=state_id,
        region_id=region_id,
        district_id=district_id,
        group_id=group_id,
        old_group_id=old_group_id,
        year=year,
        month=month
    )

    return jsonify([a.to_dict() for a in records]), 200

@attendance_bp.route("/attendance/<int:attendance_id>", methods=["GET"])
@jwt_required()
@swag_from({
    "tags": ["Attendance"],
    "summary": "Get attendance record by ID",
    "description": "Retrieve a specific attendance record by its unique ID.",
    "parameters": [
        {"name": "attendance_id", "in": "path", "type": "integer", "required": True, "description": "Attendance record ID"}
    ],
    "responses": {
        "200": {"description": "Attendance record found"},
        "404": {"description": "Attendance record not found"}
    }
})
def get_one(attendance_id):
    attendance = attendance_controller.get_attendance_by_id(attendance_id)
    if not attendance:
        return jsonify({"error": "not found"}), 404
    return jsonify(attendance.to_dict()), 200

@attendance_bp.route("/attendance/<int:attendance_id>", methods=["PUT"])
@jwt_required()
@swag_from({
    "tags": ["Attendance"],
    "summary": "Update attendance record",
    "description": "Update an existing attendance record using its ID. Only fields provided in the body will be updated.",
    "parameters": [
        {"name": "attendance_id", "in": "path", "type": "integer", "required": True},
        {
            "name": "body",
            "in": "body",
            "schema": {
                "properties": {
                    "men": {"type": "integer", "example": 50},
                    "women": {"type": "integer", "example": 65},
                    "week": {"type": "integer", "example": 2}
                }
            }
        }
    ],
    "responses": {
        "200": {"description": "Attendance record updated successfully"},
        "404": {"description": "Attendance record not found"}
    }
})
def update_attendance(attendance_id):
    data = request.get_json() or {}
    attendance = attendance_controller.update_attendance(attendance_id, data)
    if not attendance:
        return jsonify({"error": "not found"}), 404
    return jsonify(attendance.to_dict()), 200

@attendance_bp.route("/attendance/<int:attendance_id>", methods=["DELETE"])
@jwt_required()
@swag_from({
    "tags": ["Attendance"],
    "summary": "Delete attendance record",
    "description": "Delete an existing attendance record using its unique ID.",
    "parameters": [
        {"name": "attendance_id", "in": "path", "type": "integer", "required": True}
    ],
    "responses": {
        "200": {"description": "Attendance deleted successfully"},
        "404": {"description": "Attendance record not found"}
    }
})
def delete_attendance(attendance_id):
    deleted = attendance_controller.delete_attendance(attendance_id)
    if not deleted:
        return jsonify({"error": "not found"}), 404
    return jsonify({"message": "deleted"}), 200
