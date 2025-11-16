from flask import request, jsonify
from ..extensions import db
from ..models import User, Role
from flask_jwt_extended import jwt_required, get_jwt_identity


# def can_create_role(current_user, target_roles):
#     """Restrict role creation based on hierarchy."""
#     current_roles = [r.name for r in current_user.roles]
#     target_role_names = [r.name for r in target_roles]

#     # Super admin can create anyone
#     if "Super Admin" in current_roles:
#         return True

#     # State Admins cannot create Super Admins
#     if "State Admin" in current_roles and any(r in ["Super Admin"] for r in target_role_names):
#         return False

#     # Region/District Admins cannot create higher-level roles
#     if "Region Admin" in current_roles and any(r in ["Super Admin", "State Admin"] for r in target_role_names):
#         return False

#     return True

def can_create_role(current_user, target_roles):
    """Restrict role creation based on hierarchy."""
    current_role_names = [r.name for r in current_user.roles]
    target_role_names = [r.name for r in target_roles]

    # Super Admin can create any role
    if "Super Admin" in current_role_names:
        return True

    # State Admins can create: State Admin, Region Admin, District Admin, Group Admin, Viewer
    if "State Admin" in current_role_names:
        allowed_roles = ["State Admin", "Region Admin", "District Admin", "Group Admin", "Viewer"]
        return all(role in allowed_roles for role in target_role_names)

    # Region Admins can create: Region Admin, District Admin, Group Admin, Viewer  
    if "Region Admin" in current_role_names:
        allowed_roles = ["Region Admin", "District Admin", "Group Admin", "Viewer"]
        return all(role in allowed_roles for role in target_role_names)

    # District Admins can create: District Admin, Group Admin, Viewer
    if "District Admin" in current_role_names:
        allowed_roles = ["District Admin", "Group Admin", "Viewer"]
        return all(role in allowed_roles for role in target_role_names)

    return False

@jwt_required()
def create_user():
    """
    Create User (for State Admins and below)
    ---
    tags:
      - Users
    description: Create a new user account with hierarchical role restrictions.
    security:
      - Bearer: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: CreateUser
          required:
            - email
            - password
            - role_id
          properties:
            name:
              type: string
              example: John Doe
            email:
              type: string
              example: johndoe@example.com
            phone:
              type: string
              example: "+2348012345678"
            password:
              type: string
              example: mysecurepass
            role_id:
              type: integer
              example: 2
              description: "Role ID (2=State Admin, 3=Region Admin, 4=District Admin, 5=Group Admin, 6=Viewer)"
            state_id:
              type: integer
            region_id:
              type: integer
            district_id:
              type: integer
    responses:
      201:
        description: User created successfully
      400:
        description: Invalid or missing input
      403:
        description: Insufficient permissions
    """
    data = request.get_json()
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # Required fields
    email = data.get("email")
    password = data.get("password")
    role_id = data.get("role_id")
    
    if not all([email, password, role_id]):
        return jsonify({"error": "Email, password, and role_id are required"}), 400

    # Check duplicates
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User with this email already exists"}), 400

    # Get the target role
    target_role = Role.query.get(role_id)
    if not target_role:
        return jsonify({"error": "Invalid role ID"}), 400

    # Check permissions - can current user create this role?
    if not can_create_role(current_user, [target_role]):
        return jsonify({"error": "Insufficient permissions to create users with this role"}), 403

    # Validate hierarchy based on the role being assigned
    validation_error = validate_user_hierarchy(data, [target_role])
    if validation_error:
        return jsonify({"error": validation_error}), 400

    # Auto-assign hierarchy based on current user's level
    state_id, region_id, district_id = auto_assign_hierarchy(current_user, data, target_role)

    # Create user
    user = User(
        name=data.get("name"),
        email=email,
        phone=data.get("phone"),
        is_active=True,
        state_id=state_id,
        region_id=region_id,
        district_id=district_id
    )
    user.set_password(password)
    user.roles = [target_role]

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": f"User created successfully as {target_role.name}",
        "user": user.to_dict()
    }), 201

def auto_assign_hierarchy(current_user, data, target_role):
    """
    Auto-assign hierarchy fields based on current user's level and target role
    """
    current_roles = [r.name for r in current_user.roles]
    
    # If current user is Super Admin, use provided values or allow null
    if "Super Admin" in current_roles:
        return data.get("state_id"), data.get("region_id"), data.get("district_id")
    
    # If current user is State Admin, they can only create users in their state
    elif "State Admin" in current_roles:
        state_id = current_user.state_id
        # For State Admin role, region/district can be null (covers entire state)
        if target_role.name == "State Admin":
            return state_id, None, None
        # For lower roles, use provided values but enforce state
        else:
            return state_id, data.get("region_id"), data.get("district_id")
    
    # If current user is Region Admin, they can only create users in their region
    elif "Region Admin" in current_roles:
        return current_user.state_id, current_user.region_id, data.get("district_id")
    
    # If current user is District Admin, they can only create users in their district
    elif "District Admin" in current_roles:
        return current_user.state_id, current_user.region_id, current_user.district_id
    
    return None, None, None

# @jwt_required()
# def create_user():
#     """
#     Create User
#     ---
#     tags:
#       - Users
#     description: Create a new user account (with hierarchical role checks).
#     security:
#       - Bearer: []
#     consumes:
#       - application/json
#     parameters:
#       - in: body
#         name: body
#         required: true
#         schema:
#           id: CreateUser
#           required:
#             - email
#             - password
#           properties:
#             name:
#               type: string
#               example: John Doe
#             email:
#               type: string
#               example: johndoe@example.com
#             phone:
#               type: string
#               example: "+2348012345678"
#             password:
#               type: string
#               example: mysecurepass
#             roles:
#               type: array
#               items:
#                 type: integer
#               example: [1, 2]
#             state_id:
#               type: integer
#             region_id:
#               type: integer
#             district_id:
#               type: integer
#     responses:
#       201:
#         description: User created successfully
#       400:
#         description: Invalid or missing input
#       403:
#         description: Insufficient permissions
#     """
#     data = request.get_json()
#     current_user = User.query.get(get_jwt_identity())

#     # Required fields
#     email = data.get("email")
#     password = data.get("password")
#     if not all([email, password]):
#         return jsonify({"error": "Email and password are required"}), 400

#     # Check duplicates
#     if User.query.filter_by(email=email).first():
#         return jsonify({"error": "User with this email already exists"}), 400

#     # Validate hierarchy based on roles
#     role_ids = data.get("roles", [])
#     roles = Role.query.filter(Role.id.in_(role_ids)).all()
    
#     # Hierarchy validation
#     validation_error = validate_user_hierarchy(data, roles)
#     if validation_error:
#         return jsonify({"error": validation_error}), 400

#     if not can_create_role(current_user, roles):
#         return jsonify({"error": "Insufficient permissions to create this role"}), 403

#     # Create user
#     user = User(
#         name=data.get("name"),
#         email=email,
#         phone=data.get("phone"),
#         is_active=True,
#         state_id=data.get("state_id"),
#         region_id=data.get("region_id"),
#         district_id=data.get("district_id")
#     )
#     user.set_password(password)

#     if roles:
#         user.roles = roles

#     db.session.add(user)
#     db.session.commit()

#     return jsonify({
#         "message": "User created successfully",
#         "user": user.to_dict()
#     }), 201

def validate_user_hierarchy(data, roles):
    """Validate that hierarchy fields match the user's roles"""
    role_names = [role.name for role in roles]
    
    # State Admin should have state_id but can have null region/district
    if "State Admin" in role_names:
        if not data.get("state_id"):
            return "State Admin must have a state_id"
        # State Admin can have null region_id and district_id (covers entire state)
    
    # Regional Admin should have region_id and state_id
    elif "Regional Admin" in role_names:
        if not data.get("state_id") or not data.get("region_id"):
            return "Regional Admin must have state_id and region_id"
    
    # District Admin should have all hierarchy fields
    elif "District Admin" in role_names:
        if not all([data.get("state_id"), data.get("region_id"), data.get("district_id")]):
            return "District Admin must have state_id, region_id, and district_id"
    
    # Group Admin logic would go here when you implement group-level admin
    
    return None


def update_user(user_id):
    """
    Update User
    ---
    tags:
      - Users
    description: Update user details and assigned roles.
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        required: true
        type: integer
      - in: body
        name: body
        schema:
          id: UpdateUser
          properties:
            name:
              type: string
            email:
              type: string
            phone:
              type: string
            is_active:
              type: boolean
            roles:
              type: array
              items:
                type: integer
    responses:
      200:
        description: User updated successfully
      404:
        description: User not found
    """
    data = request.get_json()
    user = User.query.get_or_404(user_id)

    user.name = data.get("name", user.name)
    user.email = data.get("email", user.email)
    user.phone = data.get("phone", user.phone)
    user.is_active = data.get("is_active", user.is_active)

    # Update hierarchy
    user.state_id = data.get("state_id", user.state_id)
    user.region_id = data.get("region_id", user.region_id)
    user.district_id = data.get("district_id", user.district_id)

    # Reassign roles if provided
    if "roles" in data:
        role_ids = data["roles"]
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        user.roles = roles

    db.session.commit()
    return jsonify({"message": "User updated successfully", "user": user.to_dict()}), 200


def list_users():
    """
    List All Users
    ---
    tags:
      - Users
    description: Returns a list of all users in the system.
    security:
      - Bearer: []
    responses:
      200:
        description: A list of users
        schema:
          type: array
          items:
            type: object
    """
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200
