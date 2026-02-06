from flask import request, jsonify

from app.models.hierarchy import Group, OldGroup
from ..extensions import db
from ..models import User, Role
from flask_jwt_extended import jwt_required, get_jwt_identity



def can_create_role(current_user, target_roles):
    """Restrict role creation based on hierarchy."""
    current_role_names = [r.name for r in current_user.roles]
    target_role_names = [r.name for r in target_roles]

    # Super Admin can create any role
    if "Super Admin" in current_role_names:
        return True

    # State Admins can create: State Admin, Region Admin, District Admin, Group Admin, Viewer
    if "State Admin" in current_role_names:
        allowed_roles = ["State Admin", "Region Admin", "District Admin", "Old Group Admin","Group Admin", "Viewer"]
        return all(role in allowed_roles for role in target_role_names)

    # Region Admins can create: Region Admin, District Admin, Group Admin, Viewer  
    if "Region Admin" in current_role_names:
        allowed_roles = ["Region Admin", "District Admin", "Group Admin", "Old Group Admin","Viewer"]
        return all(role in allowed_roles for role in target_role_names)

    # District Admins can create: District Admin, Group Admin, Viewer
    if "District Admin" in current_role_names:
        allowed_roles = ["District Admin",  "Viewer"]
        return all(role in allowed_roles for role in target_role_names)

    # 🆕 Group Admins can create: Group Admin, Viewer
    if "Group Admin" in current_role_names:
        allowed_roles = ["Group Admin", "Viewer", "District Admin"]
        return all(role in allowed_roles for role in target_role_names)

    # 🆕 Group Admins can create: Group Admin, Viewer
    if "Old_Group Admin" in current_role_names:
        allowed_roles = ["Group Admin", "Viewer", "District Admin", "Old_Group Admin"]
        return all(role in allowed_roles for role in target_role_names)

    return False

# @jwt_required()
# def create_user():
#     """
#     Create User (for State Admins and below)
#     ---
#     tags:
#       - Users
#     description: Create a new user account with hierarchical role restrictions.
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
#             - role_id
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
#             role_id:
#               type: integer
#               example: 2
#               description: "Role ID (2=State Admin, 3=Region Admin, 4=District Admin, 5=Group Admin, 6=Viewer)"
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
#     current_user_id = get_jwt_identity()
#     current_user = User.query.get(current_user_id)

#     # Required fields
#     email = data.get("email")
#     password = data.get("password")
#     role_id = data.get("role_id")
    
#     if not all([email, password, role_id]):
#         return jsonify({"error": "Email, password, and role_id are required"}), 400

#     # Check duplicates
#     if User.query.filter_by(email=email).first():
#         return jsonify({"error": "User with this email already exists"}), 400

#     # Get the target role
#     target_role = Role.query.get(role_id)
#     if not target_role:
#         return jsonify({"error": "Invalid role ID"}), 400

#     # Check permissions - can current user create this role?
#     if not can_create_role(current_user, [target_role]):
#         return jsonify({"error": "Insufficient permissions to create users with this role"}), 403

#     # Validate hierarchy based on the role being assigned
#     validation_error = validate_user_hierarchy(data, [target_role])
#     if validation_error:
#         return jsonify({"error": validation_error}), 400

#     # Auto-assign hierarchy based on current user's level
#     state_id, region_id, district_id, group_id, old_group_id = auto_assign_hierarchy(current_user, data, target_role)

#     # Create user
#     user = User(
#         name=data.get("name"),
#         email=email,
#         phone=data.get("phone"),
#         is_active=True,
#         state_id=state_id,
#         region_id=region_id,
#         district_id=district_id,
#         group_id=group_id,
#         old_group_id=old_group_id
#     )
#     user.set_password(password)
#     user.roles = [target_role]

#     db.session.add(user)
#     db.session.commit()

#     return jsonify({
#         "message": f"User created successfully as {target_role.name}",
#         "user": user.to_dict()
#     }), 201

@jwt_required()
def create_user():
    """
    Create User (for State Admins and below)
    ---
    # ... (your Swagger docs remain the same)
    """
    data = request.get_json()
    print("🔍 [CREATE_USER] Incoming data:", data)  # Log incoming request body

    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user:
        print("❌ [CREATE_USER] Current user not found for ID:", current_user_id)
        return jsonify({"error": "Unauthorized - User not found"}), 401

    print("👤 [CREATE_USER] Current user:", current_user.email, "Roles:", [r.name for r in current_user.roles])

    # Required fields
    email = data.get("email")
    password = data.get("password")
    role_id = data.get("role_id")
    
    if not all([email, password, role_id]):
        print("❌ [CREATE_USER] Missing required fields")
        return jsonify({"error": "Email, password, and role_id are required"}), 400

    # Check duplicates
    if User.query.filter_by(email=email).first():
        print("❌ [CREATE_USER] Duplicate email:", email)
        return jsonify({"error": "User with this email already exists"}), 400

    # Get the target role
    target_role = Role.query.get(role_id)
    if not target_role:
        print("❌ [CREATE_USER] Invalid role ID:", role_id)
        return jsonify({"error": "Invalid role ID"}), 400

    print("🎯 [CREATE_USER] Target role:", target_role.name)

    # Check permissions - can current user create this role?
    if not can_create_role(current_user, [target_role]):
        print("❌ [CREATE_USER] Insufficient permissions for role:", target_role.name)
        return jsonify({"error": "Insufficient permissions to create users with this role"}), 403

    print("✅ [CREATE_USER] Permission check passed")

    # Validate hierarchy based on the role being assigned
    validation_error = validate_user_hierarchy(data, [target_role])
    if validation_error:
        print("❌ [CREATE_USER] Hierarchy validation failed:", validation_error)
        return jsonify({"error": validation_error}), 400

    print("✅ [CREATE_USER] Hierarchy validation passed")

    # Auto-assign hierarchy based on current user's level
    state_id, region_id, district_id, group_id, old_group_id = auto_assign_hierarchy(current_user, data, target_role)
    print("🔄 [CREATE_USER] Auto-assigned hierarchy:", {
        "state_id": state_id,
        "region_id": region_id,
        "district_id": district_id,
        "group_id": group_id,
        "old_group_id": old_group_id
    })

    # Create user
    user = User(
        name=data.get("name"),
        email=email,
        phone=data.get("phone"),
        is_active=True,
        state_id=state_id,
        region_id=region_id,
        district_id=district_id,
        group_id=group_id,
        old_group_id=old_group_id
    )
    user.set_password(password)
    user.roles = [target_role]

    db.session.add(user)
    db.session.commit()

    print("✅ [CREATE_USER] User created successfully:", user.email)

    return jsonify({
        "message": f"User created successfully as {target_role.name}",
        "user": user.to_dict()
    }), 201


def validate_hierarchy_relationships(data):
    """Validate that hierarchy IDs have proper relationships"""
    
    # 🎯 Validate group_id and old_group_id relationships if provided
    if data.get('group_id'):
        group = Group.query.get(data['group_id'])
        if not group:
            return f"Group with ID {data['group_id']} does not exist"
        
        # If state_id is provided, ensure group belongs to that state
        if data.get('state_id') and group.state_id != data['state_id']:
            return f"Group {data['group_id']} does not belong to state {data['state_id']}"
            
        # If region_id is provided, ensure group belongs to that region
        if data.get('region_id') and group.region_id != data['region_id']:
            return f"Group {data['group_id']} does not belong to region {data['region_id']}"
    
    # 🎯 Validate old_group_id relationships if provided
    if data.get('old_group_id'):
        old_group = OldGroup.query.get(data['old_group_id'])
        if not old_group:
            return f"Old Group with ID {data['old_group_id']} does not exist"
        
        # If state_id is provided, ensure old_group belongs to that state
        if data.get('state_id') and old_group.state_id != data['state_id']:
            return f"Old Group {data['old_group_id']} does not belong to state {data['state_id']}"
            
        # If region_id is provided, ensure old_group belongs to that region
        if data.get('region_id') and old_group.region_id != data['region_id']:
            return f"Old Group {data['old_group_id']} does not belong to region {data['region_id']}"
    
    # 🎯 Validate group and old_group relationship if both are provided
    if data.get('group_id') and data.get('old_group_id'):
        group = Group.query.get(data['group_id'])
        if group.old_group_id != data['old_group_id']:
            return f"Group {data['group_id']} does not belong to Old Group {data['old_group_id']}"
    
    return None

def auto_assign_hierarchy(current_user, data, target_role):
    """
    Auto-assign hierarchy fields based on current user's level and target role
    """
    current_roles = [r.name for r in current_user.roles]
    
    # If current user is Super Admin, use provided values or allow null
    if "Super Admin" in current_roles:
        return (
            data.get("state_id"), 
            data.get("region_id"), 
            data.get("district_id"),
            data.get("group_id"),
            data.get("old_group_id")
        )
    
    # If current user is State Admin, they can only create users in their state
    elif "State Admin" in current_roles:
        state_id = current_user.state_id
        # For State Admin role, lower hierarchy can be null
        if target_role.name == "State Admin":
            return state_id, None, None, None, None
        # For lower roles, use provided values but enforce state
        else:
            return (
                state_id, 
                data.get("region_id"), 
                data.get("district_id"),
                data.get("group_id"),
                data.get("old_group_id")
            )
    
    # If current user is Region Admin, they can only create users in their region
    elif "Region Admin" in current_roles:
        return (
            current_user.state_id, 
            current_user.region_id, 
            data.get("district_id"),
            data.get("group_id"),
            data.get("old_group_id")
        )
    
    # If current user is District Admin, they can only create users in their district
    elif "District Admin" in current_roles:
        return (
            current_user.state_id, 
            current_user.region_id, 
            current_user.district_id,
            data.get("group_id"),  # District Admin can assign groups
            data.get("old_group_id")  # District Admin can assign old groups
        )
    
    # 🆕 If current user is Group Admin, they can only create users in their group
    elif "Group Admin" in current_roles:
        return (
            current_user.state_id, 
            current_user.region_id, 
            current_user.district_id,
            current_user.group_id,  # Must be their group
            current_user.old_group_id  # Must be their old group
        )
    
    return None, None, None, None, None

def validate_user_hierarchy(data, roles):
    """Validate that hierarchy fields match the user's roles"""
    role_names = [role.name for role in roles]
    
    # State Admin should have state_id but can have null lower hierarchy
    if "State Admin" in role_names:
        if not data.get("state_id"):
            return "State Admin must have a state_id"
    
    # Region Admin should have region_id and state_id
    elif "Region Admin" in role_names:
        if not data.get("state_id") or not data.get("region_id"):
            return "Region Admin must have state_id and region_id"
    
    # District Admin should have district_id, region_id and state_id
    elif "District Admin" in role_names:
        if not all([data.get("state_id"), data.get("region_id"), data.get("district_id")]):
            return "District Admin must have state_id, region_id, and district_id"
    
    # 🆕 Group Admin should have complete hierarchy including group_id
    elif "Group Admin" in role_names:
        required_fields = ["state_id", "region_id", "district_id", "group_id"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return f"Group Admin must have {', '.join(missing_fields)}"
        
        # 🎯 Group Admin should also have old_group_id that matches their group
        if data.get('group_id'):
            group = Group.query.get(data['group_id'])
            if group and group.old_group_id and not data.get('old_group_id'):
                return "Group Admin must have old_group_id that matches their group's old group"
            if data.get('old_group_id') and group.old_group_id != data.get('old_group_id'):
                return "Group Admin's old_group_id must match their group's old group"
    
    return None



# def auto_assign_hierarchy(current_user, data, target_role):
#     """
#     Auto-assign hierarchy fields based on current user's level and target role
#     """
#     current_roles = [r.name for r in current_user.roles]
    
#     # If current user is Super Admin, use provided values or allow null
#     if "Super Admin" in current_roles:
#         return data.get("state_id"), data.get("region_id"), data.get("district_id")
    
#     # If current user is State Admin, they can only create users in their state
#     elif "State Admin" in current_roles:
#         state_id = current_user.state_id
#         # For State Admin role, region/district can be null (covers entire state)
#         if target_role.name == "State Admin":
#             return state_id, None, None
#         # For lower roles, use provided values but enforce state
#         else:
#             return state_id, data.get("region_id"), data.get("district_id")
    
#     # If current user is Region Admin, they can only create users in their region
#     elif "Region Admin" in current_roles:
#         return current_user.state_id, current_user.region_id, data.get("district_id")
    
#     # If current user is District Admin, they can only create users in their district
#     elif "District Admin" in current_roles:
#         return current_user.state_id, current_user.region_id, current_user.district_id
    
#     return None, None, None


# def validate_user_hierarchy(data, roles):
#     """Validate that hierarchy fields match the user's roles"""
#     role_names = [role.name for role in roles]
    
#     # State Admin should have state_id but can have null region/district
#     if "State Admin" in role_names:
#         if not data.get("state_id"):
#             return "State Admin must have a state_id"
#         # State Admin can have null region_id and district_id (covers entire state)
    
#     # Regional Admin should have region_id and state_id
#     elif "Region Admin" in role_names:
#         if not data.get("state_id") or not data.get("region_id"):
#             return "Regional Admin must have state_id and region_id"
    
#     # District Admin should have all hierarchy fields
#     elif "District Admin" in role_names:
#         if not all([data.get("state_id"), data.get("region_id"), data.get("district_id")]):
#             return "District Admin must have state_id, region_id, and district_id"
    
#     # Group Admin logic would go here when you implement group-level admin
    
#     return None


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

    # 🎯 VALIDATE HIERARCHY RELATIONSHIPS for updates too
    validation_error = validate_hierarchy_relationships(data)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    # Update basic fields
    user.name = data.get("name", user.name)
    user.email = data.get("email", user.email)
    user.phone = data.get("phone", user.phone)
    user.is_active = data.get("is_active", user.is_active)

    # Update hierarchy
    user.state_id = data.get("state_id", user.state_id)
    user.region_id = data.get("region_id", user.region_id)
    user.district_id = data.get("district_id", user.district_id)
    user.group_id = data.get("group_id", user.group_id)
    user.old_group_id = data.get("old_group_id", user.old_group_id)

    # Enhanced role assignment - accepts both IDs and names
    if "roles" in data:
        role_input = data["roles"]
        
        if not role_input:  # Empty array
            user.roles = []
        elif isinstance(role_input[0], int):  # Array of IDs [1, 2, 3]
            roles = Role.query.filter(Role.id.in_(role_input)).all()
            user.roles = roles
        elif isinstance(role_input[0], str):  # Array of names ["State Admin", "Region Admin"]
            roles = Role.query.filter(Role.name.in_(role_input)).all()
            user.roles = roles
        else:
            return jsonify({"error": "Roles must be an array of IDs (integers) or names (strings)"}), 400

    db.session.commit()
    return jsonify({"message": "User updated successfully", "user": user.to_dict()}), 200


# def list_users():
#     """
#     List All Users
#     ---
#     tags:
#       - Users
#     description: Returns a list of all users in the system.
#     security:
#       - Bearer: []
#     responses:
#       200:
#         description: A list of users
#         schema:
#           type: array
#           items:
#             type: object
#     """
#     # Pagination parameters
#     page = request.args.get('page', 1, type=int)
#     per_page = min(request.args.get('per_page', 50, type=int), 100)  # Max 100 per page
    
#     # Optimized query with eager loading
#     users_query = User.query.options(db.joinedload(User.roles))
    
#     paginated_users = users_query.paginate(
#         page=page, 
#         per_page=per_page, 
#         error_out=False
#     )
    
#     # Optimized serialization
#     users_data = []
#     for user in paginated_users.items:
#         users_data.append({
#             'id': user.id,
#             'email': user.email,
#             'name': user.name,
#             'phone': user.phone,
#             'is_active': user.is_active,
#             'state_id': user.state_id,
#             'region_id': user.region_id,
#             'district_id': user.district_id,
#             'group_id': user.group_id,
#             'old_group_id': user.old_group_id,
#             'roles': [role.name for role in user.roles],
#             'access_level': user.access_level()
#         })
    
#     return jsonify({
#         'users': users_data,
#         'pagination': {
#             'page': page,
#             'per_page': per_page,
#             'total': paginated_users.total,
#             'pages': paginated_users.pages,
#             'has_next': paginated_users.has_next,
#             'has_prev': paginated_users.has_prev
#         }
#     }), 200

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

    # Fetch all users with eager-loaded roles
    users = User.query.options(
        db.joinedload(User.roles)
    ).all()

    # Serialize users
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'phone': user.phone,
            'is_active': user.is_active,
            'state_id': user.state_id,
            'region_id': user.region_id,
            'district_id': user.district_id,
            'group_id': user.group_id,
            'old_group_id': user.old_group_id,
            'roles': [role.name for role in user.roles],
            'access_level': user.access_level()
        })

    return jsonify({
        'total': len(users),
        'users': users_data
    }), 200



    # users = User.query.all()
    # return jsonify([u.to_dict() for u in users]), 200
