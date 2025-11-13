from flask import Blueprint, request, jsonify
from ..controllers import youth_attendance_controller
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, YouthAttendance
from ..extensions import db
import csv
from io import StringIO
from flasgger import swag_from


ya_bp = Blueprint("youth_attendance", __name__)


@ya_bp.route("/youth-attendance", methods=["POST"])
@jwt_required()
@swag_from({
    "tags": ["Youth Attendance"],
    "summary": "Create youth attendance record",
    "description": "Create a youth attendance record. Use `attendance_type` to indicate 'weekly' or 'revival'.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "attendance_type": {"type": "string", "example": "weekly"},
                    "state_id": {"type": "integer"},
                    "region_id": {"type": "integer"},
                    "district_id": {"type": "integer"},
                    "group_id": {"type": "integer"},
                    "old_group_id": {"type": "integer"},
                    "year": {"type": "integer"},
                    "month": {"type": "string"},
                    "week": {"type": "integer"},
                    "member_boys": {"type": "integer"},
                    "member_girls": {"type": "integer"},
                    "visitor_boys": {"type": "integer"},
                    "visitor_girls": {"type": "integer"},
                    "male": {"type": "integer"},
                    "female": {"type": "integer"},
                    "testimony": {"type": "string"},
                    "challenges": {"type": "string"},
                    "solutions": {"type": "string"},
                    "remarks": {"type": "string"}
                },
                "required": ["attendance_type", "state_id", "region_id", "district_id", "year", "month"]
            }
        }
    ],
    "responses": {"201": {"description": "Created"}, "400": {"description": "Bad Request"}}
})
def create_youth_attendance():
    data = request.get_json() or {}

    # Validate foreign keys if provided
    if data.get("old_group_id"):
        from ..models import OldGroup
        if not OldGroup.query.get(data["old_group_id"]):
            return jsonify({"error": "old_group not found"}), 400
    if data.get("group_id"):
        from ..models import Group
        if not Group.query.get(data["group_id"]):
            return jsonify({"error": "group not found"}), 400

    ya = youth_attendance_controller.create_youth_attendance(data)
    return jsonify(ya.to_dict()), 201


@ya_bp.route("/youth-attendance/upload", methods=["POST"])
@jwt_required()
@swag_from({
    "tags": ["Youth Attendance"],
    "summary": "Bulk upload youth attendance via CSV",
    "description": "Upload multiple youth attendance rows. Provide `attendance_type` query param to interpret rows (weekly|revival).",
    "consumes": ["multipart/form-data"],
    "parameters": [
        {"name": "attendance_type", "in": "query", "type": "string", "required": True, "description": "weekly or revival"},
        {"name": "file", "in": "formData", "type": "file", "required": True}
    ],
    "responses": {"201": {"description": "Uploaded"}, "400": {"description": "Bad Request"}}
})
def upload_youth_csv():
    attendance_type = request.args.get("attendance_type")
    if attendance_type not in ("weekly", "revival"):
        return jsonify({"error": "attendance_type must be 'weekly' or 'revival'"}), 400

    file = request.files.get("file")
    if not file or not file.filename.endswith(".csv"):
        return jsonify({"error": "Invalid file"}), 400

    stream = StringIO(file.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)

    records = []
    for row in reader:
        try:
            # convert/clean fields
            base = {
                "attendance_type": attendance_type,
                "state_id": int(row["state_id"]),
                "region_id": int(row["region_id"]),
                "district_id": int(row["district_id"]),
                "group_id": int(row["group_id"]) if row.get("group_id") else None,
                "old_group_id": int(row["old_group_id"]) if row.get("old_group_id") else None,
                "year": int(row["year"]),
                "month": row["month"],
            }

            if attendance_type == "weekly":
                base.update({
                    "week": int(row.get("week") or 0),
                    "member_boys": int(row.get("member_boys") or 0),
                    "member_girls": int(row.get("member_girls") or 0),
                    "visitor_boys": int(row.get("visitor_boys") or 0),
                    "visitor_girls": int(row.get("visitor_girls") or 0),
                })
            else:  # revival
                base.update({
                    "male": int(row.get("male") or 0),
                    "female": int(row.get("female") or 0),
                    "testimony": row.get("testimony"),
                    "challenges": row.get("challenges"),
                    "solutions": row.get("solutions"),
                    "remarks": row.get("remarks"),
                })

            records.append(YouthAttendance(**base))
        except KeyError as e:
            return jsonify({"error": f"Missing column: {e}"}), 400
        except ValueError as e:
            return jsonify({"error": f"Invalid value: {e}"}), 400

    db.session.bulk_save_objects(records)
    db.session.commit()
    return jsonify({"message": f"{len(records)} records uploaded"}), 201


@ya_bp.route("/youth-attendance", methods=["GET"])
@jwt_required()
@swag_from({
    "tags": ["Youth Attendance"],
    "summary": "List youth attendance records",
    "description": "List records filtered by attendance_type, year, month and user access level.",
    "parameters": [
        {"name": "attendance_type", "in": "query", "type": "string"},
        {"name": "year", "in": "query", "type": "integer"},
        {"name": "month", "in": "query", "type": "string"}
    ],
    "responses": {"200": {"description": "List returned"}, "401": {"description": "Unauthorized"}}
})
def list_youth_attendance():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    attendance_type = request.args.get("attendance_type")
    year = request.args.get("year")
    month = request.args.get("month")

    state_id = region_id = district_id = None
    user_role_names = [role.name for role in user.roles] if user and user.roles else []
    if "State Admin" in user_role_names:
        state_id = user.state_id
    elif "Regional Admin" in user_role_names:
        region_id = user.region_id
    elif "District Admin" in user_role_names:
        district_id = user.district_id

    records = youth_attendance_controller.get_all_youth_attendance(
        attendance_type=attendance_type,
        state_id=state_id,
        region_id=region_id,
        district_id=district_id,
        year=year,
        month=month,
    )

    return jsonify([r.to_dict() for r in records]), 200


@ya_bp.route("/youth-attendance/<int:ya_id>", methods=["GET"])
@jwt_required()
@swag_from({
    "tags": ["Youth Attendance"],
    "summary": "Get youth attendance by id",
    "parameters": [{"name": "ya_id", "in": "path", "type": "integer", "required": True}],
    "responses": {"200": {"description": "Found"}, "404": {"description": "Not found"}}
})
def get_youth_one(ya_id):
    ya = youth_attendance_controller.get_youth_attendance_by_id(ya_id)
    if not ya:
        return jsonify({"error": "not found"}), 404
    return jsonify(ya.to_dict()), 200


@ya_bp.route("/youth-attendance/<int:ya_id>", methods=["PUT"])
@jwt_required()
@swag_from({
    "tags": ["Youth Attendance"],
    "summary": "Update youth attendance",
    "parameters": [
        {"name": "ya_id", "in": "path", "type": "integer", "required": True},
        {"name": "body", "in": "body", "schema": {"type": "object"}}
    ],
    "responses": {"200": {"description": "Updated"}, "404": {"description": "Not found"}}
})
def update_youth(ya_id):
    data = request.get_json() or {}
    ya = youth_attendance_controller.update_youth_attendance(ya_id, data)
    if not ya:
        return jsonify({"error": "not found"}), 404
    return jsonify(ya.to_dict()), 200


@ya_bp.route("/youth-attendance/<int:ya_id>", methods=["DELETE"])
@jwt_required()
@swag_from({
    "tags": ["Youth Attendance"],
    "summary": "Delete youth attendance",
    "parameters": [{"name": "ya_id", "in": "path", "type": "integer", "required": True}],
    "responses": {"200": {"description": "Deleted"}, "404": {"description": "Not found"}}
})
def delete_youth(ya_id):
    ok = youth_attendance_controller.delete_youth_attendance(ya_id)
    if not ok:
        return jsonify({"error": "not found"}), 404
    return jsonify({"message": "deleted"}), 200
from flask import Blueprint, request, jsonify
from ..controllers import youth_attendance_controller
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, YouthAttendance
from ..extensions import db
import csv
from io import StringIO
from flasgger import swag_from


youth_bp = Blueprint("youth_attendance", __name__)


@youth_bp.route("/youth-attendance", methods=["POST"])
@jwt_required()
def create_youth():
    data = request.get_json() or {}

    # basic hierarchy existence checks (group/old_group) if provided
    if data.get("old_group_id"):
        from ..models import OldGroup
        if not OldGroup.query.get(data["old_group_id"]):
            return jsonify({"error": "Old Group does not exist"}), 400
    if data.get("group_id"):
        from ..models import Group
        if not Group.query.get(data["group_id"]):
            return jsonify({"error": "Group does not exist"}), 400

    obj = youth_attendance_controller.create_youth_attendance(data)
    return jsonify(obj.to_dict()), 201


@youth_bp.route("/youth-attendance/upload", methods=["POST"])
@jwt_required()
def upload_youth_csv():
    file = request.files.get("file")
    if not file or not file.filename.endswith(".csv"):
        return jsonify({"error": "Invalid file format. Please upload a .csv file."}), 400

    stream = StringIO(file.stream.read().decode("utf-8"))
    csv_reader = csv.DictReader(stream)

    records = []
    for row in csv_reader:
        try:
            # minimal validation for required hierarchy columns
            required = ["attendance_type", "state_id", "region_id", "district_id"]
            for r in required:
                if r not in row or not row[r].strip():
                    return jsonify({"error": f"Missing required column: {r}"}), 400

            attendance_type = row["attendance_type"].strip().lower()

            common = dict(
                attendance_type=attendance_type,
                state_id=int(row["state_id"]),
                region_id=int(row["region_id"]),
                district_id=int(row["district_id"]),
                group_id=int(row["group_id"]) if row.get("group_id") and row["group_id"].strip() else None,
                old_group_id=int(row["old_group_id"]) if row.get("old_group_id") and row["old_group_id"].strip() else None,
                year=int(row["year"]) if row.get("year") and row["year"].strip() else None,
                month=row.get("month") or None,
                week=int(row["week"]) if row.get("week") and row["week"].strip() else None,
            )

            if attendance_type == "weekly":
                obj = YouthAttendance(
                    **common,
                    member_boys=int(row.get("member_boys") or 0),
                    member_girls=int(row.get("member_girls") or 0),
                    visitor_boys=int(row.get("visitor_boys") or 0),
                    visitor_girls=int(row.get("visitor_girls") or 0),
                )
            elif attendance_type == "revival":
                obj = YouthAttendance(
                    **common,
                    period=row.get("period"),
                    male=int(row.get("male") or 0),
                    female=int(row.get("female") or 0),
                    testimony=row.get("testimony"),
                    challenges=row.get("challenges"),
                    solutions=row.get("solutions"),
                    remarks=row.get("remarks"),
                )
            else:
                # generic record
                obj = YouthAttendance(**common)

            records.append(obj)
        except KeyError as e:
            return jsonify({"error": f"Missing column in CSV: {e}"}), 400
        except ValueError as e:
            return jsonify({"error": f"Invalid data format in row: {e}"}), 400

    db.session.bulk_save_objects(records)
    db.session.commit()

    return jsonify({"message": f"{len(records)} youth attendance records uploaded successfully"}), 201


@youth_bp.route("/youth-attendance", methods=["GET"])
@jwt_required()
def list_youth():
    # mimic access control from attendance routes: filter by user role level
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    attendance_type = request.args.get("attendance_type")
    year = request.args.get("year")
    month = request.args.get("month")

    state_id = region_id = district_id = None
    user_role_names = [role.name for role in user.roles] if user and user.roles else []
    if "State Admin" in user_role_names:
        state_id = user.state_id
    elif "Regional Admin" in user_role_names:
        region_id = user.region_id
    elif "District Admin" in user_role_names:
        district_id = user.district_id

    records = youth_attendance_controller.get_all_youth_attendance(
        attendance_type=attendance_type,
        state_id=state_id,
        region_id=region_id,
        district_id=district_id,
        year=year,
        month=month,
    )

    return jsonify([r.to_dict() for r in records]), 200


@youth_bp.route("/youth-attendance/<int:record_id>", methods=["GET"])
@jwt_required()
def get_one(record_id):
    obj = youth_attendance_controller.get_youth_attendance_by_id(record_id)
    if not obj:
        return jsonify({"error": "not found"}), 404
    return jsonify(obj.to_dict()), 200


@youth_bp.route("/youth-attendance/<int:record_id>", methods=["PUT"])
@jwt_required()
def update(record_id):
    data = request.get_json() or {}
    obj = youth_attendance_controller.update_youth_attendance(record_id, data)
    if not obj:
        return jsonify({"error": "not found"}), 404
    return jsonify(obj.to_dict()), 200


@youth_bp.route("/youth-attendance/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete(record_id):
    deleted = youth_attendance_controller.delete_youth_attendance(record_id)
    if not deleted:
        return jsonify({"error": "not found"}), 404
    return jsonify({"message": "deleted"}), 200
