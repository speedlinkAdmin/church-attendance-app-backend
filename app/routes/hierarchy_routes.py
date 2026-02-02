# app/routes/hierarchy_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.attendance import Attendance
from app.models.hierarchy import State, Region, District, Group, OldGroup
import pandas as pd
from io import BytesIO
from flasgger import swag_from
from app.models.user import User
from app.models.youth_attendance import YouthAttendance
from app.utils.access_control import require_role ##,restrict_by_access

# def restrict_by_access(query, user):
#     """
#     COMPLETE ACCESS CONTROL - Handles all user roles in the hierarchy
#     Hierarchy: Super Admin → State Admin → Region Admin → District Admin → Group Admin → Old Group Admin
#     """
#     print(f"🎯 ACCESS CONTROL for user {user.id} with roles: {[r.name for r in.user.roles]}")
    
#     if not user or not user.roles:
#         print("❌ No user or roles - no access")
#         return query.filter_by(id=None)
    
#     # Get normalized role names
#     role_names = [r.name.lower() for r in user.roles]
#     print(f"🎯 Normalized roles: {role_names}")
    
#     # Detect model type from query
#     query_str = str(query)
    
#     # 🎯 SUPER ADMIN - NO RESTRICTIONS
#     if "super admin" in role_names:
#         print("🔓 SUPER ADMIN - Full access granted")
#         return query
    
#     # 🎯 STATE ADMIN - Access to everything in their state
#     elif "state admin" in role_names and user.state_id:
#         print(f"🔐 STATE ADMIN - Filtering by state_id: {user.state_id}")
#         if "FROM groups" in query_str:
#             return query.filter(Group.state_id == user.state_id)
#         elif "FROM districts" in query_str:
#             return query.filter(District.state_id == user.state_id)
#         elif "FROM regions" in query_str:
#             return query.filter(Region.state_id == user.state_id)
#         elif "FROM old_groups" in query_str:
#             return query.filter(OldGroup.state_id == user.state_id)
#         elif "FROM states" in query_str:
#             return query.filter(State.id == user.state_id)
#         else:
#             return query.filter_by(id=None)
    
#     # 🎯 REGION ADMIN - Access to everything in their region
#     elif "region admin" in role_names and user.region_id:
#         print(f"🔐 REGION ADMIN - Filtering by region_id: {user.region_id}")
#         if "FROM groups" in query_str:
#             return query.filter(Group.region_id == user.region_id)
#         elif "FROM districts" in query_str:
#             return query.filter(District.region_id == user.region_id)
#         elif "FROM old_groups" in query_str:
#             return query.filter(OldGroup.region_id == user.region_id)
#         elif "FROM regions" in query_str:
#             return query.filter(Region.id == user.region_id)
#         else:
#             return query.filter_by(id=None)
    
#     # 🎯 DISTRICT ADMIN - Access to everything in their district
#     elif "district admin" in role_names and user.district_id:
#         print(f"🔐 DISTRICT ADMIN - Filtering by district_id: {user.district_id}")
#         if "FROM groups" in query_str:
#             return query.filter(Group.district_id == user.district_id)
#         elif "FROM districts" in query_str:
#             return query.filter(District.id == user.district_id)
#         else:
#             return query.filter_by(id=None)
    
#     # 🎯 GROUP ADMIN - Access to everything in their group (CURRENTLY WORKING)
#     elif "group admin" in role_names and user.group_id:
#         print(f"🔐 GROUP ADMIN - Filtering by group_id: {user.group_id}")
#         if "FROM groups" in query_str:
#             return query.filter(Group.id == user.group_id)
#         elif "FROM districts" in query_str:
#             return query.filter(District.group_id == user.group_id)
#         else:
#             return query.filter_by(id=None)
    
#     # 🎯 OLD GROUP ADMIN - Access to everything in their old group
#     elif "old group admin" in role_names and user.old_group_id:
#         print(f"🔐 OLD GROUP ADMIN - Filtering by old_group_id: {user.old_group_id}")
#         if "FROM groups" in query_str:
#             return query.filter(Group.old_group_id == user.old_group_id)
#         elif "FROM districts" in query_str:
#             return query.filter(District.old_group_id == user.old_group_id)
#         elif "FROM old_groups" in query_str:
#             return query.filter(OldGroup.id == user.old_group_id)
#         else:
#             return query.filter_by(id=None)
    
#     # 🚫 NO VALID ROLE OR MISSING HIERARCHY DATA
#     print(f"🚫 No valid access - User has roles: {role_names} but missing hierarchy data")
#     return query.filter_by(id=None)

def restrict_by_access(query, user):
    """
    ENHANCED ACCESS CONTROL - Better model detection and role handling
    """
    print(f"🎯 ACCESS CONTROL for user {user.id}")
    
    if not user or not user.roles:
        return query.filter_by(id=None)
    
    role_names = [r.name.lower() for r in user.roles]
    print(f"🎯 User roles: {role_names}")
    print(f"🎯 User hierarchy - state: {user.state_id}, region: {user.region_id}, district: {user.district_id}, group: {user.group_id}, old_group: {user.old_group_id}")
    
    # Try to detect model more reliably
    query_str = str(query).lower()
    
    # 🎯 SUPER ADMIN - NO RESTRICTIONS
    if "super admin" or "admin" in role_names:
        print("🔓 SUPER ADMIN - Full access to all data")
        return query
    
    # 🎯 STATE ADMIN
    if "state admin" in role_names and user.state_id:
        print(f"🔐 STATE ADMIN - Access to state_id: {user.state_id}")
        if "from groups" in query_str:
            return query.filter(Group.state_id == user.state_id)
        elif "from districts" in query_str:
            return query.filter(District.state_id == user.state_id)
        elif "from regions" in query_str:
            return query.filter(Region.state_id == user.state_id)
        elif "from old_groups" in query_str:
            return query.filter(OldGroup.state_id == user.state_id)
        elif "from states" in query_str:
            return query.filter(State.id == user.state_id)
    
    # 🎯 REGION ADMIN
    elif "region admin" in role_names and user.region_id:
        print(f"🔐 REGION ADMIN - Access to region_id: {user.region_id}")
        if "from groups" in query_str:
            return query.filter(Group.region_id == user.region_id)
        elif "from districts" in query_str:
            return query.filter(District.region_id == user.region_id)
        elif "from old_groups" in query_str:
            return query.filter(OldGroup.region_id == user.region_id)
        elif "from regions" in query_str:
            return query.filter(Region.id == user.region_id)
    
    # 🎯 DISTRICT ADMIN
    elif "district admin" in role_names and user.district_id:
        print(f"🔐 DISTRICT ADMIN - Access to district_id: {user.district_id}")
        if "from groups" in query_str:
            return query.filter(Group.district_id == user.district_id)
        elif "from districts" in query_str:
            return query.filter(District.id == user.district_id)
    
    # 🎯 GROUP ADMIN (WORKING)
    elif "group admin" in role_names and user.group_id:
        print(f"🔐 GROUP ADMIN - Access to group_id: {user.group_id}")
        if "from groups" in query_str:
            return query.filter(Group.id == user.group_id)
        elif "from districts" in query_str:
            return query.filter(District.group_id == user.group_id)
    
    # 🎯 OLD GROUP ADMIN
    elif "old group admin" in role_names and user.old_group_id:
        print(f"🔐 OLD GROUP ADMIN - Access to old_group_id: {user.old_group_id}")
        if "from groups" in query_str:
            return query.filter(Group.old_group_id == user.old_group_id)
        elif "from districts" in query_str:
            return query.filter(District.old_group_id == user.old_group_id)
        elif "from old_groups" in query_str:
            return query.filter(OldGroup.id == user.old_group_id)
    
    print(f"🚫 No access granted for user {user.id}")
    return query.filter_by(id=None)


hierarchy_bp = Blueprint('hierarchy_bp', __name__)


@hierarchy_bp.route('/test-all-roles', methods=['GET'])
@jwt_required()
def test_all_roles():
    """Test access control for current user across all models"""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    test_results = {}
    models = [
        ("States", State.query),
        ("Regions", Region.query), 
        ("OldGroups", OldGroup.query),
        ("Groups", Group.query),
        ("Districts", District.query)
    ]
    
    for model_name, model_query in models:
        restricted_query = restrict_by_access(model_query, current_user)
        test_results[model_name] = {
            "access_granted": restricted_query.count() > 0,
            "count": restricted_query.count(),
            "query": str(restricted_query),
            "sample_data": [{"id": item.id, "name": getattr(item, 'name', 'N/A')} 
                           for item in restricted_query.limit(3).all()]
        }
    
    return jsonify({
        "user_info": {
            "id": current_user.id,
            "email": current_user.email,
            "roles": [r.name for r in current_user.roles],
            "hierarchy": {
                "state_id": current_user.state_id,
                "region_id": current_user.region_id, 
                "district_id": current_user.district_id,
                "group_id": current_user.group_id,
                "old_group_id": current_user.old_group_id
            }
        },
        "access_test_results": test_results
    })

@hierarchy_bp.route('/test-simple-access', methods=['GET'])
@jwt_required()
def test_simple_access():
    """Test the simple access control"""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    print("🧪 TESTING SIMPLE ACCESS CONTROL")
    
    # Test groups
    groups_query = Group.query
    restricted_groups = restrict_by_access(groups_query, current_user)
    
    # Test districts
    districts_query = District.query
    restricted_districts = restrict_by_access(districts_query, current_user)
    
    return jsonify({
        "groups": {
            "query": str(restricted_groups),
            "count": restricted_groups.count(),
            "data": [{"id": g.id, "name": g.name} for g in restricted_groups.all()]
        },
        "districts": {
            "query": str(restricted_districts),
            "count": restricted_districts.count(),
            "data": [{"id": d.id, "name": d.name} for d in restricted_districts.all()]
        }
    })


### ---------- STATES ----------
@hierarchy_bp.route('/states', methods=['GET'])
@jwt_required()
def get_states():
    """
    Get All States
    ---
    tags:
      - States
    description: Retrieve a list of all states in the system.
    responses:
      200:
        description: List of states
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              name:
                type: string
              code:
                type: string
              leader:
                type: string
    """

    user_id = get_jwt_identity()  # ADD THIS
    current_user = User.query.get(user_id)  # ADD THIS
    # current_user = User.query.get(get_jwt_identity())
    # states = State.query.all()
    states = restrict_by_access(State.query, current_user).all()
    # return jsonify([s.to_dict() for s in states])

    return jsonify([{
        "id": s.id,
        "name": s.name,
        "code": s.code,
        "leader": s.leader,
        "leader_email": s.leader_email,
        "leader_phone": s.leader_phone
    } for s in states])

@hierarchy_bp.route('/states', methods=['POST'])
@jwt_required()
@require_role(["super-admin"])
def create_state():

    """
    Create a New State
    ---
    tags:
      - States
    description: Add a new state to the hierarchy.
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: CreateState
          required:
            - name
            - code
          properties:
            name:
              type: string
              example: Lagos
            code:
              type: string
              example: LG
            leader:
              type: string
              example: John Doe
    responses:
      201:
        description: State created successfully
      400:
        description: Invalid or missing fields
    """
    data = request.get_json()
    new_state = State(name=data['name'], code=data['code'], leader=data.get('leader'), leader_email=data.get('leader_email'), leader_phone=data.get('leader_phone'))
    db.session.add(new_state)
    db.session.commit()
    return jsonify({"message": "State created successfully"}), 201

### CSV upload for states
@hierarchy_bp.route('/states/upload', methods=['POST'])
@jwt_required()
@require_role(["super-admin"])
def upload_states():
    """
    Upload States (CSV or Excel)
    ---
    tags:
      - States
    description: Bulk upload states via CSV or Excel file.
    consumes:
      - multipart/form-data
    security:
      - Bearer: []
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: CSV or Excel file containing 'name', 'code', and optional 'leader' columns.
    responses:
      201:
        description: States uploaded successfully
      400:
        description: File upload failed or invalid format
    """
    file = request.files['file']
    df = pd.read_excel(BytesIO(file.read())) if file.filename.endswith('.xlsx') else pd.read_csv(file)
    for _, row in df.iterrows():
        # state = State(name=row['name'], code=row['code'], leader=row.get('leader'))
        # db.session.add(state)

        name = str(row['name']).strip()
        code = str(row['code']).strip()
        leader = row.get('leader')
        leader_email = row.get('leader_email')
        leader_phone = row.get('leader_phone')
        existing_state = State.query.filter(
        (State.name == name) | (State.code == code)
        ).first()

        if existing_state:
            return jsonify({
                "error": f"State '{name}' already exists"
                }), 409

            continue  # or update instead

        state = State(name=name, code=code, leader=leader, leader_email=leader_email, leader_phone=leader_phone)
        db.session.add(state)
    db.session.commit()
    return jsonify({"message": "States uploaded successfully"}), 201

@hierarchy_bp.route("/state/<int:id>", methods=["PUT"])
@jwt_required()
@require_role(["super-admin"])
def update_state(id):
    """
    Update State
    ---
    tags:
      - States
    description: Update an existing state's details.
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        required: true
        type: integer
      - in: body
        name: body
        schema:
          id: UpdateState
          properties:
            name:
              type: string
            code:
              type: string
            leader:
              type: string
    responses:
      200:
        description: Updated state details
      404:
        description: State not found
    """
    data = request.get_json() or {}
    state = State.query.get_or_404(id)
    state.name = data.get("name", state.name)
    state.code = data.get("code", state.code)
    state.leader = data.get("leader", state.leader)
    state.leader_email = data.get("leader_email", state.leader_email)
    state.leader_phone = data.get("leader_phone", state.leader_phone)
    db.session.commit()
    return jsonify(state.to_dict()), 200


@hierarchy_bp.route("/state/<int:id>", methods=["DELETE"])
# @jwt_required()
@jwt_required()
@require_role(["super-admin"])
def delete_state(id):
    """
    Delete State
    ---
    tags:
      - States
    description: Permanently remove a state record.
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        required: true
        type: integer
    responses:
      200:
        description: State deleted successfully
      404:
        description: State not found
    """
    state = State.query.get_or_404(id)
    db.session.delete(state)
    db.session.commit()
    return jsonify({"message": "State deleted"}), 200


### ---------- REGIONS ----------
@hierarchy_bp.route('/regions', methods=['POST'])
@jwt_required()
@require_role(["super-admin", "state-admin"])
def create_region():
    """
    Create Region
    ---
    tags:
      - Regions
    description: Create a new region under a specific state.
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: CreateRegion
          required:
            - name
            - code
            - state_id
          properties:
            name:
              type: string
            code:
              type: string
            leader:
              type: string
            state_id:
              type: integer
    responses:
      201:
        description: Region created successfully
      400:
        description: Invalid input data
    """

    data = request.get_json()
    current_user = User.query.get(get_jwt_identity())

    # Validate required fields
    required_fields = ["name", "code", "state_id"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Missing required field '{field}'"}), 400

    # 🎯 FIX: Only restrict State Admin, NOT Super Admin
    if current_user.has_role("State Admin") and data["state_id"] != current_user.state_id:
        return jsonify({"error": "You cannot create a region in another state"}), 403
    # Super Admin can create regions in ANY state - no restrictions

    region = Region(
        name=data['name'],
        code=data['code'],
        leader=data.get('leader'),
        leader_email=data.get('leader_email'),
        leader_phone=data.get('leader_phone'),
        state_id=data['state_id']
    )
    db.session.add(region)
    db.session.commit()
    return jsonify({"message": "Region created"}), 201


    # data = request.get_json()  # ✅ Move this FIRST
    # current_user = User.query.get(get_jwt_identity())

    # # Validate required fields
    # required_fields = ["name", "code", "state_id"]
    # for field in required_fields:
    #     if not data.get(field):
    #         return jsonify({"error": f"Missing required field '{field}'"}), 400

    # # Fix the logic: State Admin (NOT Super Admin) should be restricted
    # if current_user.has_role("State Admin") and data["state_id"] != current_user.state_id:
    #     return jsonify({"error": "You cannot create a region in another state"}), 403

    # region = Region(
    #     name=data['name'],
    #     code=data['code'],
    #     leader=data.get('leader'),
    #     state_id=data['state_id']
    # )
    # db.session.add(region)
    # db.session.commit()
    # return jsonify({"message": "Region created"}), 201


@hierarchy_bp.route('/regions', methods=['GET'])
@jwt_required()
def get_regions():
    """
    Get All Regions
    ---
    tags:
      - Regions
    description: Retrieve all regions across states.
    responses:
      200:
        description: List of regions
    """

    # current_user = User.query.get(get_jwt_identity())
    user_id = get_jwt_identity()  # ADD THIS
    current_user = User.query.get(user_id)  # ADD THIS
    regions = restrict_by_access(Region.query, current_user).all()

    # return jsonify([r.to_dict() for r in regions])
    
    # regions = Region.query.all()
    return jsonify([{
        "id": r.id,
        "name": r.name,
        "code": r.code,
        "leader": r.leader,
        "leader_email": r.leader_email,
        "leader_phone": r.leader_phone,
        "state": r.state.name
    } for r in regions])


@hierarchy_bp.route("/region/<int:id>", methods=["PUT"])
@jwt_required()
# @require_role(["super-admin", "state-admin"])
def update_region(id):
    """
    Update Region
    ---
    tags:
      - Regions
    description: Modify existing region details.
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          id: UpdateRegion
          properties:
            name:
              type: string
            code:
              type: string
            leader:
              type: string
    responses:
      200:
        description: Region updated successfully
    """
    data = request.get_json() or {}
    current_user = User.query.get(get_jwt_identity())
    region = Region.query.get_or_404(id)

    # 🎯 ADD ACCESS CONTROL
    if not current_user.has_role("Super Admin"):
        # State Admin can only update regions in their state
        if current_user.has_role("State Admin") and region.state_id != current_user.state_id:
            return jsonify({"error": "You cannot update regions outside your state"}), 403
            
        # Region Admin shouldn't be able to update regions at all
        elif current_user.has_role("Region Admin"):
            return jsonify({"error": "You do not have permission to update regions"}), 403

    region.name = data.get("name", region.name)
    region.code = data.get("code", region.code)
    region.leader = data.get("leader", region.leader)
    region.leader_email = data.get("leader_email", region.leader_email)
    region.leader_phone = data.get("leader_phone", region.leader_phone)
    db.session.commit()
    return jsonify(region.to_dict()), 200


    # data = request.get_json() or {}
    # region = Region.query.get_or_404(id)
    # region.name = data.get("name", region.name)
    # region.code = data.get("code", region.code)
    # region.leader = data.get("leader", region.leader)
    # db.session.commit()
    # return jsonify(region.to_dict()), 200


@hierarchy_bp.route("/region/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_region(id):
    """
    Delete Region
    ---
    tags:
      - Regions
    description: Delete a region record by ID.
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Region deleted successfully
    """
    current_user = User.query.get(get_jwt_identity())
    region = Region.query.get_or_404(id)

    # 🎯 ADD ACCESS CONTROL
    if not current_user.has_role("Super Admin"):
        # State Admin can only delete regions in their state
        if current_user.has_role("State Admin") and region.state_id != current_user.state_id:
            return jsonify({"error": "You cannot delete regions outside your state"}), 403
            
        # Region Admin shouldn't be able to delete regions at all
        elif current_user.has_role("Region Admin"):
            return jsonify({"error": "You do not have permission to delete regions"}), 403

    db.session.delete(region)
    db.session.commit()
    return jsonify({"message": "Region deleted"}), 200

    # region = Region.query.get_or_404(id)
    # db.session.delete(region)
    # db.session.commit()
    # return jsonify({"message": "Region deleted"}), 200



### ---------- DISTRICTS ----------
@hierarchy_bp.route('/districts', methods=['POST'])
@jwt_required()
@require_role(["super-admin", "state-admin", "region-admin"])
def create_district():
    """
    Create a New District
    ---
    tags:
      - Districts
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          properties:
            name:
              type: string
            code:
              type: string
            leader:
              type: string
            state_id:
              type: integer
            region_id:
              type: integer
            old_group_id:
                type: integer
            group_id:
                type: integer


    responses:
      201:
        description: District created successfully
    """

    data = request.get_json()
    current_user = User.query.get(get_jwt_identity())

    # 🎯 FIX: Only restrict non-Super Admin users
    # Check if user is NOT Super Admin before applying restrictions
    if not current_user.has_role("Super Admin"):
        # State Admin restriction - only for State Admin (not Super Admin)
        if current_user.has_role("State Admin") and current_user.state_id != data.get("state_id"):
            return jsonify({"error": "You cannot create a district outside your state"}), 403

        # Region Admin restriction - only for Region Admin (not Super Admin)  
        if current_user.has_role("Region Admin") and current_user.region_id not in (None, data.get("region_id")):
            return jsonify({"error": "You cannot create a district outside your region"}), 403

    # Validate required fields
    required_fields = ["name", "code", "state_id", "region_id"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Missing required field '{field}'"}), 400

    district = District(
        name=data['name'],
        code=data['code'],
        leader=data.get('leader'),
        leader_email=data.get('leader_email'),
        leader_phone=data.get('leader_phone'),
        state_id=data['state_id'],
        region_id=data['region_id'],
        old_group_id=data.get('old_group_id'),
        group_id=data.get('group_id')
    )
    
    db.session.add(district)
    db.session.commit()
    
    return jsonify({"message": "District created"}), 201


    # data = request.get_json()
    # current_user = User.query.get(get_jwt_identity())

    # # State Admin restriction
    # if current_user.has_role("state admin") and current_user.state_id != data.get("state_id"):
    #     return jsonify({"error": "You cannot create a district outside your state"}), 403

    # # Region Admin restriction  
    # if current_user.has_role("region admin") and current_user.region_id not in (None, data.get("region_id")):
    #     return jsonify({"error": "You cannot create a district outside your region"}), 403

    # # Validate required fields
    # required_fields = ["name", "code", "state_id", "region_id"]
    # for field in required_fields:
    #     if not data.get(field):
    #         return jsonify({"error": f"Missing required field '{field}'"}), 400

    # district = District(
    #     name=data['name'],
    #     code=data['code'],
    #     leader=data.get('leader'),
    #     state_id=data['state_id'],
    #     region_id=data['region_id'],
    #     old_group_id=data.get('old_group_id'),
    #     group_id=data.get('group_id')
    # )
    
    # db.session.add(district)
    # db.session.commit()
    
    # return jsonify({"message": "District created"}), 201


@hierarchy_bp.route('/districts', methods=['GET'])
@jwt_required()
def get_districts():
    """
    Get All Districts
    ---
    tags:
      - Districts
    responses:
      200:
        description: List of all districts
    """

    # current_user = User.query.get(get_jwt_identity())
    user_id = get_jwt_identity()  # ADD THIS
    current_user = User.query.get(user_id)  # ADD THIS
    districts = restrict_by_access(District.query, current_user).all()

    # return jsonify([d.to_dict() for d in districts])
    # districts = District.query.all()
    return jsonify([{
        "id": d.id,
        "name": d.name,
        "code": d.code,
        "leader": d.leader,
        "leader_email": d.leader_email,
        "leader_phone": d.leader_phone,
        "region": d.region.name if d.region else None,
        "state": d.state.name if d.state else None,
        "old_group": d.old_group.name if d.old_group else None,
        "group": d.group.name if d.group else None,
        # Optional: Include IDs for reference
        "region_id": d.region_id,
        "state_id": d.state_id,
        "old_group_id": d.old_group_id,
        "group_id": d.group_id
    } for d in districts])

    # return jsonify([{
    #     "id": d.id,
    #     "name": d.name,
    #     "code": d.code,
    #     "leader": d.leader,
    #     "region": d.region.name,
    #     "state": d.region.state.name,
    #     "old_group": d.region
    # } for d in districts])


@hierarchy_bp.route('/debug-group-admin', methods=['GET'])
@jwt_required()
def debug_group_admin():
    """Debug route to check Group Admin access"""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    debug_info = {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "roles": [r.name for r in current_user.roles],
            "state_id": current_user.state_id,
            "region_id": current_user.region_id,
            "district_id": current_user.district_id,
            "group_id": current_user.group_id,
            "old_group_id": current_user.old_group_id
        },
        "access_tests": {}
    }
    
    # Test what groups they can see
    groups_query = restrict_by_access(Group.query, current_user)
    debug_info["access_tests"]["groups"] = {
        "query_sql": str(groups_query),
        "count": groups_query.count(),
        "groups": [{"id": g.id, "name": g.name} for g in groups_query.limit(5).all()]
    }
    
    # Test what districts they can see
    districts_query = restrict_by_access(District.query, current_user)
    debug_info["access_tests"]["districts"] = {
        "query_sql": str(districts_query),
        "count": districts_query.count(),
        "districts": [{"id": d.id, "name": d.name, "group_id": d.group_id} for d in districts_query.limit(5).all()]
    }
    
    # Check their actual group details
    if current_user.group_id:
        user_group = Group.query.get(current_user.group_id)
        debug_info["user_group_details"] = {
            "id": user_group.id if user_group else None,
            "name": user_group.name if user_group else None,
            "state_id": user_group.state_id if user_group else None,
            "region_id": user_group.region_id if user_group else None,
            "old_group_id": user_group.old_group_id if user_group else None
        }
        
        # Check districts in their group
        if user_group:
            group_districts = District.query.filter_by(group_id=user_group.id).all()
            debug_info["districts_in_user_group"] = [
                {"id": d.id, "name": d.name} for d in group_districts
            ]
    
    return jsonify(debug_info)

@hierarchy_bp.route('/test-group-access', methods=['GET'])
@jwt_required()
def test_group_access():
    """Simple test to verify Group Admin access"""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    # Direct query - bypass access control to see what SHOULD be visible
    if current_user.group_id:
        user_group = Group.query.get(current_user.group_id)
        districts_in_group = District.query.filter_by(group_id=current_user.group_id).all()
        
        return jsonify({
            "user_group": {
                "id": user_group.id,
                "name": user_group.name,
                "state_id": user_group.state_id,
                "region_id": user_group.region_id
            } if user_group else None,
            "districts_in_group": [
                {"id": d.id, "name": d.name} for d in districts_in_group
            ],
            "districts_count": len(districts_in_group),
            "user_info": {
                "group_id": current_user.group_id,
                "roles": [r.name for r in current_user.roles]
            }
        })
    else:
        return jsonify({"error": "User has no group_id assigned"})

@hierarchy_bp.route('/test-direct-groups', methods=['GET'])
@jwt_required()
def test_direct_groups():
    """Test groups without access control"""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    # Direct query - no access control
    if current_user.group_id:
        groups = Group.query.filter(Group.id == current_user.group_id).all()
        districts = District.query.filter(District.group_id == current_user.group_id).all()
        
        return jsonify({
            "direct_groups": [{"id": g.id, "name": g.name} for g in groups],
            "direct_districts": [{"id": d.id, "name": d.name} for d in districts],
            "user_info": {
                "group_id": current_user.group_id,
                "roles": [r.name for r in current_user.roles]
            }
        })
    
    return jsonify({"error": "No group_id"})

@hierarchy_bp.route('/test-restrict-function', methods=['GET'])
@jwt_required()
def test_restrict_function():
    """Test the restrict_by_access function directly"""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    # Test the function directly
    print("🧪 TESTING restrict_by_access FUNCTION DIRECTLY")
    
    # Test with Group query
    group_query = Group.query
    restricted_group_query = restrict_by_access(group_query, current_user)
    
    # Test with District query  
    district_query = District.query
    restricted_district_query = restrict_by_access(district_query, current_user)
    
    return jsonify({
        "user": {
            "id": current_user.id,
            "group_id": current_user.group_id,
            "roles": [r.name for r in current_user.roles]
        },
        "group_test": {
            "original_query": str(group_query),
            "restricted_query": str(restricted_group_query),
            "result_count": restricted_group_query.count()
        },
        "district_test": {
            "original_query": str(district_query),
            "restricted_query": str(restricted_district_query),
            "result_count": restricted_district_query.count()
        }
    })



@hierarchy_bp.route('/debug-access', methods=['GET'])
@jwt_required()
def debug_access():
    """
    Debug access control endpoint, pass JWT access token of logged in user
    ---
    tags:
      - Debug Access
    responses:
      200:
        description: response with detailed access data of logged in user
    """
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    # Test with different models
    models_to_test = [Group, District, State, Region, OldGroup]
    results = {}
    
    for model in models_to_test:
        try:
            query = restrict_by_access(model.query, current_user)
            results[model.__name__] = {
                "query_type": type(query).__name__,
                "is_none": query is None,
                "count": query.count() if query is not None else "NONE"
            }
        except Exception as e:
            results[model.__name__] = {
                "error": str(e),
                "query_type": "ERROR",
                "is_none": True
            }
    
    return jsonify({
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "roles": [r.name for r in current_user.roles],
            "state_id": current_user.state_id,
            "region_id": current_user.region_id,
            "district_id": current_user.district_id,
            "group_id": current_user.group_id,
            "old_group_id": current_user.old_group_id
        },
        "access_test_results": results
    })


@hierarchy_bp.route("/district/<int:id>", methods=["PUT"])
@jwt_required()
def update_district(id):
    """
    Update District
    ---
    tags:
      - Districts
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          properties:
            name:
              type: string
            code:
              type: string
            leader:
              type: string
    responses:
      200:
        description: District updated successfully
    """
    current_user = User.query.get(get_jwt_identity())
    data = request.get_json() or {}
    district = District.query.get_or_404(id)

    print(f"🔍 User: {current_user.id}, Roles: {[r.name for r in current_user.roles]}")
    print(f"🔍 Updating district: {district.id} in state: {district.state_id}, region: {district.region_id}")

    # 🎯 ADD ACCESS CONTROL
    if not current_user.has_role("Super Admin"):
        # State Admin can only update districts in their state
        if current_user.has_role("State Admin") and current_user.state_id != district.state_id:
            return jsonify({"error": "You cannot update districts outside your state"}), 403
            
        # Region Admin can only update districts in their region
        if current_user.has_role("Region Admin") and current_user.region_id != district.region_id:
            return jsonify({"error": "You cannot update districts outside your region"}), 403
            
        # District Admin can only update their own district
        if current_user.has_role("District Admin") and current_user.district_id != id:
            return jsonify({"error": "You cannot update districts outside your assigned district"}), 403
    else:
        print("🎯 Super Admin - updating district without restrictions")

    # Update basic fields (allowed for all authorized users)
    district.name = data.get("name", district.name)
    district.code = data.get("code", district.code)
    district.leader = data.get("leader", district.leader)
    district.leader_email = data.get("leader_email", district.leader_email)
    district.leader_phone = data.get("leader_phone", district.leader_phone)

    # 🎯 Only Super Admin should be able to change hierarchy relationships
    if current_user.has_role("Super Admin"):
        if 'state_id' in data:
            district.state_id = data['state_id']
        if 'region_id' in data:
            district.region_id = data['region_id']
        if 'old_group_id' in data:
            district.old_group_id = data['old_group_id']
        if 'group_id' in data:
            district.group_id = data['group_id']
    else:
        # Non-Super Admins cannot change hierarchy
        hierarchy_fields = ['state_id', 'region_id', 'old_group_id', 'group_id']
        changed_hierarchy_fields = [field for field in hierarchy_fields if field in data and getattr(district, field) != data[field]]
        if changed_hierarchy_fields:
            return jsonify({"error": f"You cannot change hierarchy fields: {', '.join(changed_hierarchy_fields)}"}), 403

    db.session.commit()
    return jsonify(district.to_dict()), 200


    # data = request.get_json() or {}
    # district = District.query.get_or_404(id)
    # district.name = data.get("name", district.name)
    # district.code = data.get("code", district.code)
    # district.leader = data.get("leader", district.leader)
    # db.session.commit()
    # return jsonify(district.to_dict()), 200


@hierarchy_bp.route("/district/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_district(id):
    """
    Delete District
    ---
    tags:
      - Districts
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: District deleted successfully
    """
    current_user = User.query.get(get_jwt_identity())
    district = District.query.get_or_404(id)

    print(f"🔍 User: {current_user.id}, Roles: {[r.name for r in current_user.roles]}")
    print(f"🔍 Deleting district: {district.id} in state: {district.state_id}, region: {district.region_id}")

    # 🎯 ADD ACCESS CONTROL
    if not current_user.has_role("Super Admin"):
        # State Admin can only delete districts in their state
        if current_user.has_role("State Admin") and current_user.state_id != district.state_id:
            return jsonify({"error": "You cannot delete districts outside your state"}), 403
            
        # Region Admin can only delete districts in their region
        if current_user.has_role("Region Admin") and current_user.region_id != district.region_id:
            return jsonify({"error": "You cannot delete districts outside your region"}), 403
            
        # District Admin cannot delete districts at all (including their own)
        if current_user.has_role("District Admin"):
            return jsonify({"error": "You do not have permission to delete districts"}), 403
    else:
        print("🎯 Super Admin - deleting district without restrictions")

    # 🎯 Optional: Check if district has dependent records before deletion
    # For example, check if there are users, attendance records, etc. associated with this district
    has_users = User.query.filter_by(district_id=id).first()
    has_attendance = Attendance.query.filter_by(district_id=id).first()
    has_youth_attendance = YouthAttendance.query.filter_by(district_id=id).first()
    
    if any([has_users, has_attendance, has_youth_attendance]):
        dependent_records = []
        if has_users: dependent_records.append("users")
        if has_attendance: dependent_records.append("attendance records")
        if has_youth_attendance: dependent_records.append("youth attendance records")
        
        return jsonify({
            "error": f"Cannot delete district. It has dependent {', '.join(dependent_records)}. Please reassign or delete those records first."
        }), 400

    db.session.delete(district)
    db.session.commit()
    
    return jsonify({"message": "District deleted successfully"}), 200


    
    # district = District.query.get_or_404(id)
    # db.session.delete(district)
    # db.session.commit()
    # return jsonify({"message": "District deleted"}), 200


### ---------- GROUPS ----------
@hierarchy_bp.route('/groups', methods=['POST'])
@jwt_required()
@require_role(["super-admin", "state-admin", "region-admin"])
@swag_from({
    "tags": ["Groups"],
    "summary": "Create a new group",
    "description": "Creates a new group by specifying group name, state, region, district, and access level. The group code is autogenerated.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "group_name": {"type": "string", "example": "Calabar Admins"},
                    "state_id": {"type": "integer", "example": 1},
                    "region_id": {"type": "integer", "example": 2},
                    "leader": {"type": "string", "example": "John Doe"},
                    "access_level": {"type": "string", "example": "state-admin"},
                    "old_group_id": {"type": "integer", "example": 1, "required": False}
                },
                "required": ["group_name", "state_id", "region_id"]  # Fixed required fields
            },
        }
    ],
    "responses": {
        "201": {
            "description": "Group successfully created",
            "examples": {
                "application/json": {
                    "status": "success",
                    "data": {
                        "id": 1,
                        "group_name": "Calabar Admins",
                        "group_code": "GRP-CA",
                        "state_id": 1,
                        "region_id": 2,
                        # "district_id": 3,
                        "leader": "John Doe",
                        # "access_level": "state-admin"
                    }
                }
            },
        },
        "400": {"description": "Invalid input data"},
    },
})
def create_group():
    data = request.get_json() or {}
    current_user = User.query.get(get_jwt_identity())

    print(f"🔍 User: {current_user.id}, Roles: {[r.name for r in current_user.roles]}")
    print(f"🔍 Received data: {data}")

    # 🎯 FIX: Only apply restrictions to non-Super Admin users
    if not current_user.has_role("Super Admin"):
        # STATE ADMIN cannot create group in another state
        if current_user.has_role("State Admin") and data.get("state_id") != current_user.state_id:
            return jsonify({"error": "You are not allowed to create groups in another state"}), 403

        # REGION ADMIN cannot create group in another region
        if current_user.has_role("Region Admin") and data.get("region_id") != current_user.region_id:
            return jsonify({"error": "You cannot create groups in another region"}), 403
    else:
        print("🎯 Super Admin - creating group without hierarchy restrictions")

    # Validate required fields
    required_fields = ["group_name", "state_id", "region_id"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Missing required field '{field}'"}), 400

    # Auto-generate code
    name = data["group_name"]
    code = f"GRP-{''.join([word[0].upper() for word in name.split()[:2]])}"

    group = Group(
        name=name,
        code=code,
        leader=data.get("leader"),
        leader_email=data.get("leader_email"),
        leader_phone=data.get("leader_phone"),
        state_id=data["state_id"],
        region_id=data["region_id"],
        old_group_id=data.get("old_group_id")
    )

    db.session.add(group)
    db.session.commit()

    return jsonify({
        "message": "Group created",
        "data": group.to_dict()
    }), 201


    # data = request.get_json() or {}
    # current_user = User.query.get(get_jwt_identity())

    # # Debug: Print received data
    # print(f"Received data: {data}")

    # # Fix 1: Use the correct method call with parentheses
    # # STATE ADMIN cannot create group in another state
    # if current_user.has_role("state admin") and data.get("state_id") != current_user.state_id:
    #     return jsonify({"error": "You are not allowed to create groups in another state"}), 403

    # # REGION ADMIN cannot create group in another region
    # if current_user.has_role("region admin") and data.get("region_id") != current_user.region_id:
    #     return jsonify({"error": "You cannot create groups in another region"}), 403

    # # Fix 2: Use correct field names that match the frontend payload
    # required_fields = ["group_name", "state_id", "region_id"]  # Removed old_group_id if not required
    # for field in required_fields:
    #     if not data.get(field):
    #         return jsonify({"error": f"Missing required field '{field}'"}), 400

    # # Fix 3: Use group_name instead of name
    # name = data["group_name"]
    # code = f"GRP-{''.join([word[0].upper() for word in name.split()[:2]])}"

    # # Fix 4: Create group with correct fields
    # group = Group(
    #     name=name,  # Use the group_name as name
    #     code=code,
    #     leader=data.get("leader"),
    #     state_id=data["state_id"],
    #     region_id=data["region_id"],
    #     old_group_id=data.get("old_group_id")  # Use .get() since it might not be provided
    # )

    # db.session.add(group)
    # db.session.commit()

    # return jsonify({
    #     "message": "Group created",
    #     "data": group.to_dict()
    # }), 201

@hierarchy_bp.route('/groups', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Groups"],
    "summary": "List all groups",
    "description": "Fetch all groups with optional filters like state_id or access_level.",
    "parameters": [
        {"name": "state_id", "in": "query", "type": "integer", "required": False, "description": "Filter by state ID"},
        {"name": "access_level", "in": "query", "type": "string", "required": False, "description": "Filter by access level"}
    ],
    "responses": {
        "200": {
            "description": "List of groups retrieved successfully",
            "examples": {
                "application/json": {
                    "status": "success",
                    "data": [
                        {"id": 1, "group_name": "Abuja Supervisors", "state_id": 1, "access_level": "state-admin"},
                        {"id": 2, "group_name": "Lagos Supervisors", "state_id": 2, "access_level": "group-admin"}
                    ]
                }
            }
        }
    }
})
def get_groups():

    # current_user = User.query.get(get_jwt_identity())
    user_id = get_jwt_identity()  # ADD THIS
    current_user = User.query.get(user_id)  # ADD THIS

    groups = restrict_by_access(Group.query, current_user).all()

    # return jsonify([g.to_dict() for g in groups])
    # groups = Group.query.all()
    return jsonify([{
        "id": g.id,
        "name": g.name,
        "code": g.code,
        "leader": g.leader,
        "leader_email": g.leader_email,
        "leader_phone": g.leader_phone,
        # "district": g.district.name if g.district else None,
        "region": g.region.name if g.region else None,
        "state": g.state.name if g.state else None,
        "old_group": g.old_group.name if g.old_group else None
    } for g in groups])


# ---------------------------
# DELETE GROUP
# ---------------------------
@hierarchy_bp.route("/groups/<int:group_id>", methods=["DELETE"])
@jwt_required()
@swag_from({
    "tags": ["Groups"],
    "summary": "Delete a group",
    "description": "Deletes a group by ID.",
    "parameters": [
        {"name": "group_id", "in": "path", "type": "integer", "required": True, "description": "Group ID"}
    ],
    "responses": {
        "200": {"description": "Group deleted successfully"},
        "404": {"description": "Group not found"}
    },
})
def delete_group(group_id):
    current_user = User.query.get(get_jwt_identity())
    group = Group.query.get_or_404(group_id)

    # 🎯 ADD ACCESS CONTROL
    if not current_user.has_role("Super Admin"):
        # State Admin can only delete groups in their state
        if current_user.has_role("State Admin") and current_user.state_id != group.state_id:
            return jsonify({"error": "You cannot delete groups outside your state"}), 403
            
        # Region Admin can only delete groups in their region
        if current_user.has_role("Region Admin") and current_user.region_id != group.region_id:
            return jsonify({"error": "You cannot delete groups outside your region"}), 403
            
        # District Admin cannot delete groups at all
        if current_user.has_role("District Admin"):
            return jsonify({"error": "You do not have permission to delete groups"}), 403

    db.session.delete(group)
    db.session.commit()
    
    return jsonify({"status": "success", "message": f"Group {group_id} deleted"}), 200


# def delete_group(group_id):
#     return jsonify({"status": "success", "message": f"Group {group_id} deleted"}), 200


### ---------- OLD GROUPS ----------
### ---------- OLD GROUPS ----------
@hierarchy_bp.route('/oldgroups', methods=['POST'])
@jwt_required()
@require_role(["super-admin", "state-admin", "region-admin"])
@swag_from({
    "tags": ["Old Groups"],
    "summary": "Create a new Old Group (autogenerated code)",
    "description": "Creates a new record for an old or archived group. The `code` field is autogenerated from the group name.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "example": "Calabar Admins"},
                    "leader": {"type": "string", "example": "Jane Doe"},
                    "state_id": {"type": "integer", "example": 1},
                    "region_id": {"type": "integer", "example": 2}
                },
                "required": ["name", "state_id", "region_id"]
            }
        }
    ],
    "responses": {
        "201": {
            "description": "Old Group successfully created",
            "examples": {
                "application/json": {
                    "message": "Old Group created",
                    "data": {
                        "id": 1,
                        "name": "Calabar Admins",
                        "code": "GRP-CA",
                        "leader": "Jane Doe",
                        "state_id": 1,
                        "region_id": 2
                    }
                }
            }
        },
        "400": {"description": "Invalid request or missing required fields"}
    }
})
def create_oldgroup():
    data = request.get_json() or {}
    current_user = User.query.get(get_jwt_identity())

    print(f"🔍 User: {current_user.id}, Roles: {[r.name for r in current_user.roles]}")

    # 🎯 ADD ACCESS CONTROL
    if not current_user.has_role("Super Admin"):
        # State Admin can only create old groups in their state
        if current_user.has_role("State Admin") and data.get("state_id") != current_user.state_id:
            return jsonify({"error": "You cannot create old groups outside your state"}), 403

        # Region Admin can only create old groups in their region
        if current_user.has_role("Region Admin") and data.get("region_id") != current_user.region_id:
            return jsonify({"error": "You cannot create old groups outside your region"}), 403
            
        # District Admin cannot create old groups at all
        if current_user.has_role("District Admin"):
            return jsonify({"error": "You do not have permission to create old groups"}), 403
    else:
        print("🎯 Super Admin - creating old group without hierarchy restrictions")

    # Validate required fields
    required_fields = ["name", "state_id", "region_id"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Missing required field '{field}'"}), 400

    # Autogenerate code from first two letters of name
    name = data["name"]
    code = f"GRP-{''.join([word[0].upper() for word in name.split()[:2]])}"

    old_group = OldGroup(
        name=name,
        code=code,
        leader=data.get("leader"),
        leader_email=data.get("leader_email"),
        leader_phone=data.get("leader_phone"),
        state_id=data["state_id"],
        region_id=data["region_id"]
    )

    db.session.add(old_group)
    db.session.commit()

    return jsonify({
        "message": "Old Group created",
        "data": {
            "id": old_group.id,
            "name": old_group.name,
            "code": old_group.code,
            "leader": old_group.leader,
            "leader_email": old_group.leader_email,
            "leader_phone": old_group.leader_phone,
            "state_id": old_group.state_id,
            "region_id": old_group.region_id
        }
    }), 201

    # data = request.get_json() or {}

    # # Validate required fields - REMOVED district_id and group_id
    # required_fields = ["name", "state_id", "region_id"]
    # for field in required_fields:
    #     if not data.get(field):
    #         return jsonify({"error": f"Missing required field '{field}'"}), 400

    # # Autogenerate code from first two letters of name
    # name = data["name"]
    # code = f"GRP-{''.join([word[0].upper() for word in name.split()[:2]])}"

    # old_group = OldGroup(
    #     name=name,
    #     code=code,
    #     leader=data.get("leader"),
    #     state_id=data["state_id"],
    #     region_id=data["region_id"]
    #     # REMOVED: district_id and group_id
    # )

    # db.session.add(old_group)
    # db.session.commit()

    # return jsonify({
    #     "message": "Old Group created",
    #     "data": {
    #         "id": old_group.id,
    #         "name": old_group.name,
    #         "code": old_group.code,
    #         "leader": old_group.leader,
    #         "state_id": old_group.state_id,
    #         "region_id": old_group.region_id
    #         # REMOVED: district_id and group_id
    #     }
    # }), 201


@hierarchy_bp.route('/oldgroups/<int:id>', methods=['PUT'])
@jwt_required()
@require_role(["super-admin", "state-admin", "region-admin"])
@swag_from({
    "tags": ["Old Groups"],
    "summary": "Update an Old Group",
    "description": "Updates an existing old group record. The code can be regenerated if the name changes.",
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "ID of the old group to update"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "example": "Calabar Admins Updated"},
                    "leader": {"type": "string", "example": "John Doe"},
                    "state_id": {"type": "integer", "example": 1},
                    "region_id": {"type": "integer", "example": 2},
                    "regenerate_code": {"type": "boolean", "example": True, "description": "Whether to regenerate code from name"}
                }
            }
        }
    ],
    "responses": {
        "200": {
            "description": "Old Group successfully updated",
            "examples": {
                "application/json": {
                    "message": "Old Group updated",
                    "data": {
                        "id": 1,
                        "name": "Calabar Admins Updated",
                        "code": "GRP-CA",
                        "leader": "John Doe",
                        "state_id": 1,
                        "region_id": 2
                    }
                }
            }
        },
        "400": {"description": "Invalid request data"},
        "404": {"description": "Old Group not found"}
    }
})
def update_oldgroup(id):
    current_user = User.query.get(get_jwt_identity())
    data = request.get_json() or {}
    
    old_group = OldGroup.query.get(id)
    if not old_group:
        return jsonify({"error": "Old Group not found"}), 404

    # 🎯 ADD ACCESS CONTROL
    if not current_user.has_role("Super Admin"):
        # State Admin can only update old groups in their state
        if current_user.has_role("State Admin") and current_user.state_id != old_group.state_id:
            return jsonify({"error": "You cannot update old groups outside your state"}), 403
            
        # Region Admin can only update old groups in their region
        if current_user.has_role("Region Admin") and current_user.region_id != old_group.region_id:
            return jsonify({"error": "You cannot update old groups outside your region"}), 403
            
        # District Admin cannot update old groups at all (they're at a lower hierarchy level)
        if current_user.has_role("District Admin"):
            return jsonify({"error": "You do not have permission to update old groups"}), 403

    # Update fields if provided
    if 'name' in data:
        old_group.name = data['name']
        # Regenerate code if name changed and regenerate_code is True or not specified
        if data.get('regenerate_code', True):
            code = f"GRP-{''.join([word[0].upper() for word in data['name'].split()[:2]])}"
            old_group.code = code

    if 'leader' in data:
        old_group.leader = data['leader']

    if 'leader_email' in data:
        old_group.leader_email = data['leader_email']

    if 'leader_phone' in data:
        old_group.leader_phone = data['leader_phone']
    
    # 🎯 Only Super Admin should be able to change hierarchy
    if current_user.has_role("Super Admin"):
        if 'state_id' in data:
            old_group.state_id = data['state_id']
        
        if 'region_id' in data:
            old_group.region_id = data['region_id']
    else:
        # Non-Super Admins cannot change hierarchy
        if 'state_id' in data or 'region_id' in data:
            return jsonify({"error": "You cannot change the hierarchy location of old groups"}), 403
    
    db.session.commit()

    return jsonify({
        "message": "Old Group updated",
        "data": {
            "id": old_group.id,
            "name": old_group.name,
            "code": old_group.code,
            "leader": old_group.leader,
            "leader_email": old_group.leader_email,
            "leader_phone": old_group.leader_phone,
            "state_id": old_group.state_id,
            "region_id": old_group.region_id
        }
    }), 200

    # data = request.get_json() or {}
    
    # old_group = OldGroup.query.get(id)
    # if not old_group:
    #     return jsonify({"error": "Old Group not found"}), 404

    # # Update fields if provided
    # if 'name' in data:
    #     old_group.name = data['name']
    #     # Regenerate code if name changed and regenerate_code is True or not specified
    #     if data.get('regenerate_code', True):
    #         code = f"GRP-{''.join([word[0].upper() for word in data['name'].split()[:2]])}"
    #         old_group.code = code

    # if 'leader' in data:
    #     old_group.leader = data['leader']
    
    # if 'state_id' in data:
    #     old_group.state_id = data['state_id']
    
    # if 'region_id' in data:
    #     old_group.region_id = data['region_id']
    
    # # REMOVED: district_id and group_id updates

    # db.session.commit()

    # return jsonify({
    #     "message": "Old Group updated",
    #     "data": {
    #         "id": old_group.id,
    #         "name": old_group.name,
    #         "code": old_group.code,
    #         "leader": old_group.leader,
    #         "state_id": old_group.state_id,
    #         "region_id": old_group.region_id
    #         # REMOVED: district_id and group_id
    #     }
    # }), 200


@hierarchy_bp.route('/oldgroups/<int:id>', methods=['DELETE'])
@jwt_required()
@swag_from({
    "tags": ["Old Groups"],
    "summary": "Delete an Old Group",
    "description": "Permanently deletes an old group record from the system.",
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "ID of the old group to delete"
        }
    ],
    "responses": {
        "200": {
            "description": "Old Group successfully deleted",
            "examples": {
                "application/json": {
                    "message": "Old Group deleted successfully"
                }
            }
        },
        "404": {"description": "Old Group not found"}
    }
})
def delete_oldgroup(id):
    current_user = User.query.get(get_jwt_identity())
    
    old_group = OldGroup.query.get(id)
    if not old_group:
        return jsonify({"error": "Old Group not found"}), 404

    # 🎯 ADD ACCESS CONTROL
    if not current_user.has_role("Super Admin"):
        # State Admin can only delete old groups in their state
        if current_user.has_role("State Admin") and current_user.state_id != old_group.state_id:
            return jsonify({"error": "You cannot delete old groups outside your state"}), 403
            
        # Region Admin can only delete old groups in their region
        if current_user.has_role("Region Admin") and current_user.region_id != old_group.region_id:
            return jsonify({"error": "You cannot delete old groups outside your region"}), 403
            
        # District Admin cannot delete old groups at all
        if current_user.has_role("District Admin"):
            return jsonify({"error": "You do not have permission to delete old groups"}), 403

    db.session.delete(old_group)
    db.session.commit()

    return jsonify({"message": "Old Group deleted successfully"}), 200


    # old_group = OldGroup.query.get(id)
    # if not old_group:
    #     return jsonify({"error": "Old Group not found"}), 404

    # db.session.delete(old_group)
    # db.session.commit()

    # return jsonify({"message": "Old Group deleted successfully"}), 200


@hierarchy_bp.route('/oldgroups/<int:id>', methods=['GET'])
# @jwt_required()
@swag_from({
    "tags": ["Old Groups"],
    "summary": "Get a single Old Group",
    "description": "Fetch details of a specific old group by ID.",
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "ID of the old group"
        }
    ],
    "responses": {
        "200": {
            "description": "Old Group details retrieved successfully",
            "examples": {
                "application/json": {
                    "id": 1,
                    "name": "Calabar Admins",
                    "code": "GRP-CA",
                    "leader": "Jane Doe",
                    "state": "Cross River",
                    "region": "South Region"
                }
            }
        },
        "404": {"description": "Old Group not found"}
    }
})
def get_oldgroup(id):
    old_group = OldGroup.query.get(id)
    if not old_group:
        return jsonify({"error": "Old Group not found"}), 404

    return jsonify({
        "id": old_group.id,
        "name": old_group.name,
        "code": old_group.code,
        "leader": old_group.leader,
        "leader_email": old_group.leader_email,
        "leader_phone": old_group.leader_phone,
        "state": old_group.state.name if old_group.state else None,
        "region": old_group.region.name if old_group.region else None
        # REMOVED: group, district references
    }), 200


@hierarchy_bp.route('/oldgroups', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Old Groups"],
    "summary": "Get old groups",
    "description": "Fetch all previously deactivated or archived groups with optional filters.",
    "parameters": [
        {"name": "state_id", "in": "query", "type": "integer", "required": False},
        {"name": "region_id", "in": "query", "type": "integer", "required": False}
    ],
    "responses": {
        "200": {
            "description": "Archived groups retrieved successfully",
            "examples": {
                "application/json": {
                    "status": "success",
                    "data": [
                        {"id": 3, "name": "North Central Admins", "state": "Plateau", "region": "North Central"}
                    ]
                }
            }
        }
    },
})
def get_oldgroups():

    user_id = get_jwt_identity()  # ADD THIS
    current_user = User.query.get(user_id)  # ADD THIS

    oldgroups = restrict_by_access(OldGroup.query, current_user).all()
    # oldgroups = OldGroup.query.all()
    return jsonify([{
        "id": o.id,
        "name": o.name,
        "code": o.code,
        "leader": o.leader,
        "leader_email": o.leader_email,
        "leader_phone": o.leader_phone,
        "state": o.state.name if o.state else None,
        "region": o.region.name if o.region else None
        # REMOVED: group, district references
    } for o in oldgroups])


@hierarchy_bp.route("/oldgroups/by_region/<int:region_id>", methods=['GET'])
@swag_from({
    "tags": ["Old Groups"],
    "summary": "Get Old Groups by Region",
    "description": "Fetch all old groups under a specific region.",
    "parameters": [
        {"name": "region_id", "in": "path", "type": "integer", "required": True, "description": "Region ID"}
    ],
    "responses": {
        "200": {
            "description": "Old groups retrieved successfully",
            "examples": {
                "application/json": [
                    {"id": 1, "name": "Old Group Alpha"},
                    {"id": 2, "name": "Old Group Beta"}
                ]
            }
        }
    },
})
def oldgroups_by_region(region_id):
    old_groups = OldGroup.query.filter_by(region_id=region_id).all()
    return jsonify([og.to_dict() for og in old_groups])

@hierarchy_bp.route("/groups/by_oldgroup/<int:old_group_id>", methods=['GET'])
@swag_from({
    "tags": ["Groups"],
    "summary": "Get Groups by Old Group",
    "description": "Retrieve all groups under a specific old group.",
    "parameters": [
        {"name": "old_group_id", "in": "path", "type": "integer", "required": True, "description": "Old Group ID"}
    ],
    "responses": {
        "200": {
            "description": "Groups retrieved successfully",
            "examples": {
                "application/json": [
                    {"id": 1, "name": "Group Alpha"},
                    {"id": 2, "name": "Group Beta"}
                ]
            }
        }
    },
})
def groups_by_oldgroup(old_group_id):
    groups = Group.query.filter_by(old_group_id=old_group_id).all()
    return jsonify([g.to_dict() for g in groups])

@hierarchy_bp.route("/districts/by_group/<int:group_id>", methods=['GET'])
@swag_from({
    "tags": ["Districts"],
    "summary": "Get Districts by Group",
    "description": "Retrieve all districts under a specific group.",
    "parameters": [
        {"name": "group_id", "in": "path", "type": "integer", "required": True, "description": "Group ID"}
    ],
    "responses": {
        "200": {
            "description": "Districts retrieved successfully",
            "examples": {
                "application/json": [
                    {"id": 1, "name": "District East"},
                    {"id": 2, "name": "District West"}
                ]
            }
        }
    },
})
def districts_by_group(group_id):
    districts = District.query.filter_by(group_id=group_id).all()
    return jsonify([d.to_dict() for d in districts])


@hierarchy_bp.route("/regions/by_state/<int:state_id>", methods=["GET"])
@swag_from({
    "tags": ["Regions"],
    "summary": "Get Regions by State",
    "description": "Fetch all regions under a specific state.",
    "parameters": [
        {"name": "state_id", "in": "path", "type": "integer", "required": True, "description": "State ID"}
    ],
    "responses": {
        "200": {
            "description": "Regions retrieved successfully",
            "examples": {
                "application/json": [
                    {"id": 1, "name": "Region North"},
                    {"id": 2, "name": "Region South"}
                ]
            }
        },
        "404": {"description": "State not found or no regions"}
    },
})
def regions_by_state(state_id):
    regions = Region.query.filter_by(state_id=state_id).all()
    return jsonify([r.to_dict() for r in regions])

@hierarchy_bp.route("/districts/by_region/<int:region_id>", methods=["GET"])
@swag_from({
    "tags": ["Districts"],
    "summary": "Get Districts by Region",
    "description": "Retrieve all districts belonging to a given region.",
    "parameters": [
        {"name": "region_id", "in": "path", "type": "integer", "required": True, "description": "Region ID"}
    ],
    "responses": {
        "200": {
            "description": "Districts retrieved successfully",
            "examples": {
                "application/json": [
                    {"id": 1, "name": "District East"},
                    {"id": 2, "name": "District West"}
                ]
            }
        }
    },
})
def districts_by_region(region_id):
    districts = District.query.filter_by(region_id=region_id).all()
    return jsonify([d.to_dict() for d in districts])

@hierarchy_bp.route("/groups/by_district/<int:district_id>", methods=["GET"])
@swag_from({
    "tags": ["Groups"],
    "summary": "Get Groups by District",
    "description": "Retrieve all groups under a specific district.",
    "parameters": [
        {"name": "district_id", "in": "path", "type": "integer", "required": True, "description": "District ID"}
    ],
    "responses": {
        "200": {
            "description": "Groups retrieved successfully",
            "examples": {
                "application/json": [
                    {"id": 1, "name": "Group Alpha"},
                    {"id": 2, "name": "Group Beta"}
                ]
            }
        }
    },
})
def groups_by_district(district_id):
    groups = Group.query.filter_by(district_id=district_id).all()
    return jsonify([g.to_dict() for g in groups])

@hierarchy_bp.route("/oldgroups/by_group/<int:group_id>", methods=["GET"])
@swag_from({
    "tags": ["Old Groups"],
    "summary": "Get Old Groups by Group",
    "description": "Fetch all old group entries linked to a specific active group.",
    "parameters": [
        {"name": "group_id", "in": "path", "type": "integer", "required": True, "description": "Group ID"}
    ],
    "responses": {
        "200": {
            "description": "Old groups linked to a specific group retrieved successfully",
            "examples": {
                "application/json": [
                    {"id": 5, "name": "Old Group Zeta", "code": "OGZ-05", "leader": "Jane Doe"}
                ]
            }
        },
        "404": {"description": "No old groups found for this group ID"}
    },
})
def oldgroups_by_group(group_id):
    old_groups = OldGroup.query.filter_by(group_id=group_id).all()
    return jsonify([og.to_dict() for og in old_groups])


@hierarchy_bp.route("/group/<int:id>", methods=["PUT"])
@swag_from({
    "tags": ["Groups"],
    "summary": "Update a group",
    "description": "Update an existing group's name or access level.",
    "parameters": [
        {"name": "group_id", "in": "path", "type": "integer", "required": True, "description": "Group ID"},
        {
            "name": "body",
            "in": "body",
            "schema": {
                "properties": {
                    "group_name": {"type": "string"},
                    "access_level": {"type": "string"}
                }
            },
        },
    ],
    "responses": {
        "200": {
            "description": "Group updated successfully",
            "examples": {
                "application/json": {"status": "success", "message": "Group updated successfully"}
            },
        },
        "404": {"description": "Group not found"},
    },
})
@jwt_required()
def update_group(id):

    current_user = User.query.get(get_jwt_identity())
    group = Group.query.get_or_404(id)
    data = request.get_json() or {}
    
    # 🎯 ADD ACCESS CONTROL
    if not current_user.has_role("Super Admin"):
        # State Admin can only update groups in their state
        if current_user.has_role("State Admin") and current_user.state_id != group.state_id:
            return jsonify({"error": "You cannot update groups outside your state"}), 403
            
        # Region Admin can only update groups in their region
        if current_user.has_role("Region Admin") and current_user.region_id != group.region_id:
            return jsonify({"error": "You cannot update groups outside your region"}), 403
            
        # District Admin can only update groups in their district
        if current_user.has_role("District Admin") and current_user.district_id != group.district_id:
            return jsonify({"error": "You cannot update groups outside your district"}), 403
            
        # Group Admin can only update their own group (if you implement this role)
        if current_user.has_role("Group Admin") and current_user.group_id != id:
            return jsonify({"error": "You cannot update groups outside your assigned group"}), 403
    
    # Super Admin and authorized users can update the group
    group.name = data.get("name", group.name)
    group.code = data.get("code", group.code)
    group.leader = data.get("leader", group.leader)
    group.leader_email = data.get("leader_email", group.leader_email)
    group.leader_phone = data.get("leader_phone", group.leader_phone)
    db.session.commit()
    return jsonify(group.to_dict()), 200


    # data = request.get_json() or {}
    # group = Group.query.get_or_404(id)
    # group.name = data.get("name", group.name)
    # group.code = data.get("code", group.code)
    # group.leader = data.get("leader", group.leader)
    # db.session.commit()
    # return jsonify(group.to_dict()), 200

