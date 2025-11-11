# app/routes/hierarchy_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.hierarchy import State, Region, District, Group, OldGroup
import pandas as pd
from io import BytesIO
from flasgger import swag_from

hierarchy_bp = Blueprint('hierarchy_bp', __name__)

### ---------- STATES ----------
@hierarchy_bp.route('/states', methods=['GET'])
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
    states = State.query.all()
    return jsonify([{
        "id": s.id,
        "name": s.name,
        "code": s.code,
        "leader": s.leader
    } for s in states])

@hierarchy_bp.route('/states', methods=['POST'])
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
@jwt_required()
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
    regions = Region.query.all()
    return jsonify([{
        "id": r.id,
        "name": r.name,
        "code": r.code,
        "leader": r.leader,
        "state": r.state.name
    } for r in regions])


@hierarchy_bp.route("/region/<int:id>", methods=["PUT"])
@jwt_required()
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
    data = request.get_json()
    district = District(
        name=data['name'],
        code=data['code'],
        leader=data.get('leader'),
        state_id=data['state_id'],
        region_id=data['region_id']
    )
    db.session.add(district)
    db.session.commit()
    return jsonify({"message": "District created"}), 201

@hierarchy_bp.route('/districts', methods=['GET'])
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
    districts = District.query.all()
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
                    "district_id": {"type": "integer", "example": 3},
                    "leader": {"type": "string", "example": "John Doe"},
                    "access_level": {"type": "string", "example": "state-admin"}
                },
                "required": ["group_name", "state_id", "region_id", "district_id"]
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
                        "district_id": 3,
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

    # Validate required fields
    required_fields = ["group_name", "state_id", "region_id", "district_id"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Missing required field '{field}'"}), 400

    # Auto-generate group code from first 2 letters of group name (uppercase)
    group_name = data["group_name"]
    group_code = f"GRP-{''.join([word[0].upper() for word in group_name.split()[:2]])}"

    group = Group(
        name=group_name,
        code=group_code,
        leader=data.get("leader"),
        state_id=data["state_id"],
        region_id=data["region_id"],
        district_id=data["district_id"]
    )

    db.session.add(group)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Group created successfully",
        "data": {
            "id": group.id,
            "group_name": group.name,
            "group_code": group.code,
            "state_id": group.state_id,
            "region_id": group.region_id,
            "district_id": group.district_id,
            "leader": group.leader,
            "access_level": data.get("access_level")
        }
    }), 201

# ### ---------- GROUPS ----------
# @hierarchy_bp.route('/groups', methods=['POST'])
# @swag_from({
#     "tags": ["Groups"],
#     "summary": "Create a new group",
#     "description": "Creates a new group by specifying group name, state, and access level.",
#     "parameters": [
#         {
#             "name": "body",
#             "in": "body",
#             "required": True,
#             "schema": {
#                 "properties": {
#                     "group_name": {"type": "string"},
#                     "state_id": {"type": "integer"},
#                     "access_level": {"type": "string", "example": "state-admin"},
#                 },
#                 "required": ["group_name", "state_id"]
#             },
#         }
#     ],
#     "responses": {
#         "201": {
#             "description": "Group successfully created",
#             "examples": {
#                 "application/json": {
#                     "status": "success",
#                     "data": {
#                         "id": 1,
#                         "group_name": "South West Admins",
#                         "state_id": 5,
#                         "access_level": "state-admin"
#                     }
#                 }
#             },
#         },
#         "400": {"description": "Invalid input data"},
#     },
# })
# def create_group():
#     data = request.get_json()
#     group = Group(
#         name=data['group_name'],
#         code=data['code'],
#         leader=data.get('leader'),
#         state_id=data['state_id'],
#         region_id=data['region_id'],
#         district_id=data['district_id']
#     )
#     db.session.add(group)
#     db.session.commit()
#     return jsonify({"message": "Group created"}), 201

@hierarchy_bp.route('/groups', methods=['GET'])
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
    groups = Group.query.all()
    return jsonify([{
        "id": g.id,
        "name": g.name,
        "code": g.code,
        "leader": g.leader,
        "district": g.district.name,
        "region": g.region.name,
        "state": g.region.state.name
    } for g in groups])

# ---------------------------
# UPDATE GROUP
# # ---------------------------
# @group_bp.route("/groups/<int:group_id>", methods=["PUT"])
# @swag_from({
#     "tags": ["Groups"],
#     "summary": "Update a group",
#     "description": "Update an existing group's name or access level.",
#     "parameters": [
#         {"name": "group_id", "in": "path", "type": "integer", "required": True, "description": "Group ID"},
#         {
#             "name": "body",
#             "in": "body",
#             "schema": {
#                 "properties": {
#                     "group_name": {"type": "string"},
#                     "access_level": {"type": "string"}
#                 }
#             },
#         },
#     ],
#     "responses": {
#         "200": {
#             "description": "Group updated successfully",
#             "examples": {
#                 "application/json": {"status": "success", "message": "Group updated successfully"}
#             },
#         },
#         "404": {"description": "Group not found"},
#     },
# })
# def update_group(group_id):
#     data = request.get_json()
#     return jsonify({"status": "success", "message": f"Group {group_id} updated"}), 200


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
@hierarchy_bp.route('/oldgroups', methods=['POST'])
@swag_from({
    "tags": ["Old Groups"],
    "summary": "Create a new Old Group",
    "description": "Create a new record for an old or archived group by specifying its details such as name, code, and hierarchy relationships.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "properties": {
                    "name": {"type": "string"},
                    "code": {"type": "string"},
                    "leader": {"type": "string"},
                    "state_id": {"type": "integer"},
                    "region_id": {"type": "integer"},
                    "district_id": {"type": "integer"},
                    "group_id": {"type": "integer"}
                },
                "required": ["name", "code", "state_id", "region_id", "district_id", "group_id"]
            },
        }
    ],
    "responses": {
        "201": {
            "description": "Old Group successfully created",
            "examples": {
                "application/json": {
                    "message": "Old Group created"
                }
            }
        },
        "400": {"description": "Invalid request or missing required fields"}
    }
})
def create_oldgroup():
    data = request.get_json()
    old_group = OldGroup(
        name=data['name'],
        code=data['code'],
        leader=data.get('leader'),
        state_id=data['state_id'],
        region_id=data['region_id'],
        district_id=data['district_id'],
        group_id=data['group_id']
    )
    db.session.add(old_group)
    db.session.commit()
    return jsonify({"message": "Old Group created"}), 201

@hierarchy_bp.route('/oldgroups', methods=['GET'])
@swag_from({
    "tags": ["Old Groups"],
    "summary": "Get old groups",
    "description": "Fetch all previously deactivated or archived groups with optional filters.",
    "parameters": [
        {"name": "state_id", "in": "query", "type": "integer", "required": False},
        {"name": "date_archived", "in": "query", "type": "string", "required": False, "description": "Filter by archive date (YYYY-MM-DD)"}
    ],
    "responses": {
        "200": {
            "description": "Archived groups retrieved successfully",
            "examples": {
                "application/json": {
                    "status": "success",
                    "data": [
                        {"id": 3, "group_name": "North Central Admins", "archived_on": "2025-06-01"}
                    ]
                }
            }
        }
    },
})
def get_oldgroups():
    oldgroups = OldGroup.query.all()
    return jsonify([{
        "id": o.id,
        "name": o.name,
        "code": o.code,
        "leader": o.leader,
        "group": o.group.name,
        "district": o.group.district.name,
        "region": o.group.region.name,
        "state": o.group.region.state.name
    } for o in oldgroups])

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


# actions - 

# @hierarchy_bp.route("/state/<int:id>", methods=["PUT"])
# @jwt_required()
# def update_state(id):
#     data = request.get_json() or {}
#     state = State.query.get_or_404(id)
#     state.name = data.get("name", state.name)
#     state.code = data.get("code", state.code)
#     state.leader = data.get("leader", state.leader)
#     db.session.commit()
#     return jsonify(state.to_dict()), 200


# @hierarchy_bp.route("/state/<int:id>", methods=["DELETE"])
# @jwt_required()
# def delete_state(id):
#     state = State.query.get_or_404(id)
#     db.session.delete(state)
#     db.session.commit()
#     return jsonify({"message": "State deleted"}), 200


# @hierarchy_bp.route("/region/<int:id>", methods=["PUT"])
# @jwt_required()
# def update_region(id):
#     data = request.get_json() or {}
#     region = Region.query.get_or_404(id)
#     region.name = data.get("name", region.name)
#     region.code = data.get("code", region.code)
#     region.leader = data.get("leader", region.leader)
#     db.session.commit()
#     return jsonify(region.to_dict()), 200

# @hierarchy_bp.route("/region/<int:id>", methods=["DELETE"])
# @jwt_required()
# def delete_region(id):
#     region = Region.query.get_or_404(id)
#     db.session.delete(region)
#     db.session.commit()
#     return jsonify({"message": "Region deleted"}), 200

# @hierarchy_bp.route("/district/<int:id>", methods=["PUT"])
# @jwt_required()
# def update_district(id):
#     data = request.get_json() or {}
#     district = District.query.get_or_404(id)
#     district.name = data.get("name", district.name)
#     district.code = data.get("code", district.code)
#     district.leader = data.get("leader", district.leader)
#     db.session.commit()
#     return jsonify(district.to_dict()), 200

# @hierarchy_bp.route("/district/<int:id>", methods=["DELETE"])
# @jwt_required()
# def delete_district(id):
#     district = District.query.get_or_404(id)
#     db.session.delete(district)
#     db.session.commit()
#     return jsonify({"message": "District deleted"}), 200

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

# @hierarchy_bp.route("/group/<int:id>", methods=["DELETE"])
# @jwt_required()
# def delete_group(id):
#     group = Group.query.get_or_404(id)
#     db.session.delete(group)
#     db.session.commit()
#     return jsonify({"message": "Group deleted"}), 200

# @hierarchy_bp.route("/oldgroup/<int:id>", methods=["PUT"])
# @jwt_required()
# def update_oldgroup(id):
#     data = request.get_json() or {}
#     old_group = OldGroup.query.get_or_404(id)
#     old_group.name = data.get("name", old_group.name)
#     old_group.code = data.get("code", old_group.code)
#     old_group.leader = data.get("leader", old_group.leader)
#     db.session.commit()
#     return jsonify(old_group.to_dict()), 200

# @hierarchy_bp.route("/oldgroup/<int:id>", methods=["DELETE"])
# @jwt_required()
# def delete_oldgroup(id):
#     old_group = OldGroup.query.get_or_404(id)
#     db.session.delete(old_group)
#     db.session.commit()
#     return jsonify({"message": "Old Group deleted"}), 200

# # end actions