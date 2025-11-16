# app/routes/hierarchy_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.hierarchy import State, Region, District, Group, OldGroup
import pandas as pd
from io import BytesIO
from flasgger import swag_from
from app.models.user import User
from app.utils.access_control import require_role, restrict_by_access


hierarchy_bp = Blueprint('hierarchy_bp', __name__)

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
        "leader": s.leader
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
    new_state = State(name=data['name'], code=data['code'], leader=data.get('leader'))
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
        state = State(name=row['name'], code=row['code'], leader=row.get('leader'))
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
    current_user = User.query.get(get_jwt_identity())
    if current_user.has_role("Super Admin") and data["state_id"] != current_user.state_id:
        return jsonify({"error": "You cannot create a region in another state"}), 403

    data = request.get_json()
    region = Region(
        name=data['name'],
        code=data['code'],
        leader=data.get('leader'),
        state_id=data['state_id']
    )
    db.session.add(region)
    db.session.commit()
    return jsonify({"message": "Region created"}), 201

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
    region = Region.query.get_or_404(id)
    region.name = data.get("name", region.name)
    region.code = data.get("code", region.code)
    region.leader = data.get("leader", region.leader)
    db.session.commit()
    return jsonify(region.to_dict()), 200


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
    region = Region.query.get_or_404(id)
    db.session.delete(region)
    db.session.commit()
    return jsonify({"message": "Region deleted"}), 200



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
    responses:
      201:
        description: District created successfully
    """

    current_user = User.query.get(get_jwt_identity())   

    if current_user.state_id != data["state_id"]:
        return jsonify({"error": "You cannot create a district outside your state"}), 403

    if current_user.region_id not in (None, data["region_id"]):
        return jsonify({"error": "You cannot create a district outside your region"}), 403

    data = request.get_json()
    district = District(
        name=data['name'],
        code=data['code'],
        leader=data.get('leader'),
        state_id=data['state_id'],
        region_id=data['region_id'],
        old_group_id=data['old_group_id'],
        group_id=data['group_id']
    )
    db.session.add(district)
    db.session.commit()
    return jsonify({"message": "District created"}), 201

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
        "region": d.region.name,
        "state": d.region.state.name
    } for d in districts])

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
    data = request.get_json() or {}
    district = District.query.get_or_404(id)
    district.name = data.get("name", district.name)
    district.code = data.get("code", district.code)
    district.leader = data.get("leader", district.leader)
    db.session.commit()
    return jsonify(district.to_dict()), 200


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
    district = District.query.get_or_404(id)
    db.session.delete(district)
    db.session.commit()
    return jsonify({"message": "District deleted"}), 200


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
                        "access_level": "state-admin"
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

    # Debug: Print received data
    print(f"Received data: {data}")

    # Fix 1: Use the correct method call with parentheses
    # STATE ADMIN cannot create group in another state
    if current_user.has_role("state admin") and data.get("state_id") != current_user.state_id:
        return jsonify({"error": "You are not allowed to create groups in another state"}), 403

    # REGION ADMIN cannot create group in another region
    if current_user.has_role("region admin") and data.get("region_id") != current_user.region_id:
        return jsonify({"error": "You cannot create groups in another region"}), 403

    # Fix 2: Use correct field names that match the frontend payload
    required_fields = ["group_name", "state_id", "region_id"]  # Removed old_group_id if not required
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Missing required field '{field}'"}), 400

    # Fix 3: Use group_name instead of name
    name = data["group_name"]
    code = f"GRP-{''.join([word[0].upper() for word in name.split()[:2]])}"

    # Fix 4: Create group with correct fields
    group = Group(
        name=name,  # Use the group_name as name
        code=code,
        leader=data.get("leader"),
        state_id=data["state_id"],
        region_id=data["region_id"],
        old_group_id=data.get("old_group_id")  # Use .get() since it might not be provided
    )

    db.session.add(group)
    db.session.commit()

    return jsonify({
        "message": "Group created",
        "data": group.to_dict()
    }), 201

# def create_group():
#     data = request.get_json() or {}
#     current_user = User.query.get(get_jwt_identity())

#     # Get user's role names
#     user_role_names = [role.name.lower() for role in current_user.roles]


#     # STATE ADMIN cannot create group in another state
#     if current_user.has_role == "state-admin" and data["state_id"] != current_user.state_id:
#         return jsonify({"error": "You are not allowed to create groups in another state"}), 403

#     # REGION ADMIN cannot create group in another region
#     if current_user.has_role == "region-admin" and data["region_id"] != current_user.region_id:
#         return jsonify({"error": "You cannot create groups in another region"}), 403

    
#     required_fields = ["name", "state_id", "region_id", "old_group_id"]
#     for field in required_fields:
#         if not data.get(field):
#             return jsonify({"error": f"Missing required field '{field}'"}), 400

#     # Auto-generate code
#     name = data["name"]
#     code = f"GRP-{''.join([word[0].upper() for word in name.split()[:2]])}"

#     group = Group(
#         name=name,
#         code=code,
#         leader=data.get("leader"),
#         state_id=data["state_id"],
#         region_id=data["region_id"],
#         old_group_id=data["old_group_id"]
#     )

#     db.session.add(group)
#     db.session.commit()

#     return jsonify({
#         "message": "Group created",
#         "data": group.to_dict()
#     }), 201


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
        "district": g.district.name if g.district else None,
        "region": g.region.name if g.region else None,
        "state": g.state.name if g.state else None
    } for g in groups])


# ---------------------------
# DELETE GROUP
# ---------------------------
@hierarchy_bp.route("/groups/<int:group_id>", methods=["DELETE"])
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
    return jsonify({"status": "success", "message": f"Group {group_id} deleted"}), 200


### ---------- OLD GROUPS ----------
### ---------- OLD GROUPS ----------
@hierarchy_bp.route('/oldgroups', methods=['POST'])
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

    # Validate required fields - REMOVED district_id and group_id
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
        state_id=data["state_id"],
        region_id=data["region_id"]
        # REMOVED: district_id and group_id
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
            "state_id": old_group.state_id,
            "region_id": old_group.region_id
            # REMOVED: district_id and group_id
        }
    }), 201

@hierarchy_bp.route('/oldgroups/<int:id>', methods=['PUT'])
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
    data = request.get_json() or {}
    
    old_group = OldGroup.query.get(id)
    if not old_group:
        return jsonify({"error": "Old Group not found"}), 404

    # Update fields if provided
    if 'name' in data:
        old_group.name = data['name']
        # Regenerate code if name changed and regenerate_code is True or not specified
        if data.get('regenerate_code', True):
            code = f"GRP-{''.join([word[0].upper() for word in data['name'].split()[:2]])}"
            old_group.code = code

    if 'leader' in data:
        old_group.leader = data['leader']
    
    if 'state_id' in data:
        old_group.state_id = data['state_id']
    
    if 'region_id' in data:
        old_group.region_id = data['region_id']
    
    # REMOVED: district_id and group_id updates

    db.session.commit()

    return jsonify({
        "message": "Old Group updated",
        "data": {
            "id": old_group.id,
            "name": old_group.name,
            "code": old_group.code,
            "leader": old_group.leader,
            "state_id": old_group.state_id,
            "region_id": old_group.region_id
            # REMOVED: district_id and group_id
        }
    }), 200


@hierarchy_bp.route('/oldgroups/<int:id>', methods=['DELETE'])
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
    old_group = OldGroup.query.get(id)
    if not old_group:
        return jsonify({"error": "Old Group not found"}), 404

    db.session.delete(old_group)
    db.session.commit()

    return jsonify({"message": "Old Group deleted successfully"}), 200


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
    data = request.get_json() or {}
    group = Group.query.get_or_404(id)
    group.name = data.get("name", group.name)
    group.code = data.get("code", group.code)
    group.leader = data.get("leader", group.leader)
    db.session.commit()
    return jsonify(group.to_dict()), 200

