from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, Attendance, State, Region, District, Group, OldGroup
from ..extensions import db
from flasgger import swag_from
from sqlalchemy import func


dashboard_bp = Blueprint("dashboard", __name__)

def get_user_access_scope(user):
    """Determine what data the user can access based on their role"""
    user_roles = [role.name for role in user.roles]
    
    if "Super Admin" in user_roles:
        return {"scope": "global"}  # Access to everything
    
    elif "State Admin" in user_roles:
        return {
            "scope": "state",
            "state_id": user.state_id,
            "filters": {"state_id": user.state_id}
        }
    
    elif "Regional Admin" in user_roles:
        return {
            "scope": "region", 
            "state_id": user.state_id,
            "region_id": user.region_id,
            "filters": {"state_id": user.state_id, "region_id": user.region_id}
        }
    
    elif "District Admin" in user_roles:
        return {
            "scope": "district",
            "state_id": user.state_id,
            "region_id": user.region_id, 
            "district_id": user.district_id,
            "filters": {"state_id": user.state_id, "region_id": user.region_id, "district_id": user.district_id}
        }
    
    else:
        return {"scope": "limited"}  # Basic users with limited access

@dashboard_bp.route("/dashboard/summary", methods=["GET"])
@jwt_required()
@swag_from({
    "tags": ["Dashboard"],
    "summary": "Get dashboard summary",
    "description": "Returns summary data based on user's access level (Super Admin sees all, State Admin sees only their state, etc.)",
    "responses": {
        "200": {
            "description": "Dashboard summary data",
            "examples": {
                "application/json": {
                    "total_users": 150,
                    "total_attendance": 5000,
                    "states_count": 5,
                    "recent_activity": "."
                }
            }
        }
    }
})
def get_dashboard_summary():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    access_scope = get_user_access_scope(user)
    
    # Build queries based on access scope
    users_query = User.query
    attendance_query = Attendance.query

    attendance_totals = attendance_query.with_entities(
    func.sum(
        Attendance.men +
        Attendance.women +
        Attendance.youth_boys +
        Attendance.youth_girls +
        Attendance.children_boys +
        Attendance.children_girls
    ).label("total_attendance"),
    func.sum(Attendance.new_comers).label("total_new_comers"),
    func.coalesce(func.sum(Attendance.tithe_offering), 0).label("total_tithe_offering")
).first()

    
    if access_scope["scope"] == "state":
        users_query = users_query.filter_by(state_id=user.state_id)
        attendance_query = attendance_query.filter_by(state_id=user.state_id)
    elif access_scope["scope"] == "region":
        users_query = users_query.filter_by(state_id=user.state_id, region_id=user.region_id)
        attendance_query = attendance_query.filter_by(state_id=user.state_id, region_id=user.region_id)
    elif access_scope["scope"] == "district":
        users_query = users_query.filter_by(state_id=user.state_id, region_id=user.region_id, district_id=user.district_id)
        attendance_query = attendance_query.filter_by(state_id=user.state_id, region_id=user.region_id, district_id=user.district_id)
    
    summary = {
        "total_users": users_query.count(),
        "total_attendance_records": attendance_query.count(),
        "total_attendance": int(attendance_totals.total_attendance or 0),
        "total_new_comers": int(attendance_totals.total_new_comers or 0),
        "total_tithe_offering": float(attendance_totals.total_tithe_offering or 0),
        "access_level": user.access_level(),
        "user_scope": access_scope["scope"]
    }
    
    # Add hierarchy counts based on scope
    if access_scope["scope"] == "global":
        summary.update({
            "states_count": State.query.count(),
            "regions_count": Region.query.count(),
            "districts_count": District.query.count(),
            "groups_count": Group.query.count()
        })
    elif access_scope["scope"] == "state":
        summary.update({
            "regions_count": Region.query.filter_by(state_id=user.state_id).count(),
            "districts_count": District.query.filter_by(state_id=user.state_id).count(),
            "groups_count": Group.query.filter_by(state_id=user.state_id).count()
        })
    elif access_scope["scope"] == "region":
        summary.update({
            "districts_count": District.query.filter_by(region_id=user.region_id).count(),
            "groups_count": Group.query.filter_by(region_id=user.region_id).count()
        })
    
    return jsonify(summary), 200

@dashboard_bp.route("/dashboard/users", methods=["GET"])
@jwt_required()
@swag_from({
    "tags": ["Dashboard"],
    "summary": "Get users in my scope",
    "description": "Returns users that the current user has permission to view",
    "responses": {
        "200": {
            "description": "List of users in scope",
            "examples": {
                "application/json": [
                    {"id": 1, "name": "John Doe", "email": "john@example.com", "role": "State Admin"}
                ]
            }
        }
    }
})
def get_users_in_scope():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    access_scope = get_user_access_scope(current_user)
    
    query = User.query
    
    # Apply filters based on user's access level
    if access_scope["scope"] == "state":
        query = query.filter(User.state_id == current_user.state_id)
    elif access_scope["scope"] == "region":
        query = query.filter(
            User.state_id == current_user.state_id,
            User.region_id == current_user.region_id
        )
    elif access_scope["scope"] == "district":
        query = query.filter(
            User.state_id == current_user.state_id,
            User.region_id == current_user.region_id,
            User.district_id == current_user.district_id
        )
    
    users = query.all()
    return jsonify([u.to_dict() for u in users]), 200

@dashboard_bp.route("/dashboard/attendance", methods=["GET"])
@jwt_required()
@swag_from({
    "tags": ["Dashboard"],
    "summary": "Get attendance in my scope",
    "description": "Returns attendance records that the current user has permission to view",
    "parameters": [
        {"name": "year", "in": "query", "type": "integer", "required": False},
        {"name": "month", "in": "query", "type": "string", "required": False}
    ],
    "responses": {
        "200": {
            "description": "List of attendance records in scope",
            "examples": {
                "application/json": [
                    {"id": 1, "service_type": "Sunday Service", "men": 45, "women": 60}
                ]
            }
        }
    }
})
def get_attendance_in_scope():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    access_scope = get_user_access_scope(current_user)
    
    year = request.args.get("year")
    month = request.args.get("month")
    
    query = Attendance.query
    
    # Apply scope filters
    if access_scope["scope"] == "state":
        query = query.filter_by(state_id=current_user.state_id)
    elif access_scope["scope"] == "region":
        query = query.filter_by(state_id=current_user.state_id, region_id=current_user.region_id)
    elif access_scope["scope"] == "district":
        query = query.filter_by(
            state_id=current_user.state_id, 
            region_id=current_user.region_id,
            district_id=current_user.district_id
        )
    
    # Apply additional filters
    if year:
        query = query.filter_by(year=year)
    if month:
        query = query.filter_by(month=month)
    
    attendance_records = query.limit(100).all()  # Limit for performance
    return jsonify([a.to_dict() for a in attendance_records]), 200

@dashboard_bp.route("/dashboard/hierarchy", methods=["GET"])
@jwt_required()
@swag_from({
    "tags": ["Dashboard"],
    "summary": "Get hierarchy data in my scope",
    "description": "Returns hierarchy information (states, regions, districts) that the user can access",
    "responses": {
        "200": {
            "description": "Hierarchy data",
            "examples": {
                "application/json": {
                    "states": "",
                    "regions": "",
                    "districts": ""
                }
            }
        }
    }
})
def get_hierarchy_in_scope():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    access_scope = get_user_access_scope(current_user)
    
    hierarchy_data = {}
    
    if access_scope["scope"] == "global":
        hierarchy_data["states"] = [s.to_dict() for s in State.query.all()]
        hierarchy_data["regions"] = [r.to_dict() for r in Region.query.all()]
        hierarchy_data["districts"] = [d.to_dict() for d in District.query.all()]
    
    elif access_scope["scope"] == "state":
        hierarchy_data["state"] = State.query.get(current_user.state_id).to_dict()
        hierarchy_data["regions"] = [r.to_dict() for r in Region.query.filter_by(state_id=current_user.state_id).all()]
        hierarchy_data["districts"] = [d.to_dict() for d in District.query.filter_by(state_id=current_user.state_id).all()]
    
    elif access_scope["scope"] == "region":
        hierarchy_data["state"] = State.query.get(current_user.state_id).to_dict()
        hierarchy_data["region"] = Region.query.get(current_user.region_id).to_dict()
        hierarchy_data["districts"] = [d.to_dict() for d in District.query.filter_by(region_id=current_user.region_id).all()]
    
    elif access_scope["scope"] == "district":
        hierarchy_data["state"] = State.query.get(current_user.state_id).to_dict()
        hierarchy_data["region"] = Region.query.get(current_user.region_id).to_dict()
        hierarchy_data["district"] = District.query.get(current_user.district_id).to_dict()
    
    return jsonify(hierarchy_data), 200