from flask import Blueprint, request, jsonify

from app.controllers.user_controller import can_create_role
from ..extensions import db
from ..models.user import User, Role, Permission
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/setup-admin", methods=["POST"])
def setup_admin():
    """
    One-time setup endpoint for Render deployment
    """
    # You can add some basic security like a secret key if needed
    secret = request.args.get('secret')
    if secret != 'your-secret-key-here':  # Change this
        return jsonify({"error": "Unauthorized"}), 401
    
    from ..models.user import User, Role
    
    # Ensure roles exist
    roles_data = {
        "Super Admin": "Full system administrator with access to everything",
        "State Admin": "Administrator for a specific state", 
        "Region Admin": "Administrator for a specific region",
        "District Admin": "Administrator for a specific district",
        "Group Admin": "Administrator for a specific group",
        "Viewer": "Read-only access"
    }
    
    created_roles = []
    for role_name, description in roles_data.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=description)
            db.session.add(role)
            created_roles.append(role_name)
    
    db.session.commit()
    
    # Update existing admin user
    user = User.query.filter_by(email='edward.ndiyo@speedlinkng.com').first()
    super_admin_role = Role.query.filter_by(name='Super Admin').first()
    
    if user and super_admin_role:
        user.roles = [super_admin_role]
        db.session.commit()
        return jsonify({
            "message": "Setup complete",
            "created_roles": created_roles,
            "user_updated": True
        })
    else:
        return jsonify({
            "message": "Roles created but user not updated",
            "created_roles": created_roles,
            "user_found": user is not None,
            "role_found": super_admin_role is not None
        })

@auth_bp.route("/available-roles", methods=["GET"])
@jwt_required()
def get_available_roles():
    """Get roles that the current user can assign to new users."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    all_roles = Role.query.all()
    available_roles = []
    
    for role in all_roles:
        if can_create_role(current_user, [role]):
            available_roles.append({
                "id": role.id,
                "name": role.name,
                "description": role.description
            })
    
    return jsonify(available_roles)

@auth_bp.route("/create-admin", methods=["POST"])
@jwt_required()  # ADD JWT PROTECTION
def create_admin():
    """
    Create System Admin User
    ---
    tags:
      - Authentication
    description: Create a new system administrator user (Super Admin only).
    security:
      - Bearer: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: CreateAdmin
          required:
            - email
            - password
            - name
          properties:
            email:
              type: string
              example: admin@example.com
            password:
              type: string
              example: strongpassword123
            name:
              type: string
              example: Daniel Uokon
    responses:
      201:
        description: Admin user created successfully
      400:
        description: Missing or invalid input data
      403:
        description: Insufficient permissions (not a Super Admin)
    """
    # Check if current user is Super Admin
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    current_user_roles = [r.name for r in current_user.roles]
    if "Super Admin" not in current_user_roles:
        return jsonify({"error": "Only Super Admins can create system administrators"}), 403

    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")

    if not all([email, password, name]):
        return jsonify({"error": "Email, password, and name are required"}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "User with this email already exists"}), 400

    # Get Super Admin role (should exist after setup)
    super_admin_role = Role.query.filter_by(name="Super Admin").first()
    if not super_admin_role:
        return jsonify({"error": "Super Admin role not found. Run setup first."}), 500

    # Create user as Super Admin
    user = User(email=email, name=name, is_active=True)
    user.set_password(password)
    user.roles.append(super_admin_role)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "System Administrator created successfully",
        "user": user.to_dict()
    }), 201

# @auth_bp.route("/create-admin", methods=["POST"])
# def create_admin():
#     """
#     Create Admin User
#     ---
#     tags:
#       - Authentication
#     description: Create a new administrator user account.
#     consumes:
#       - application/json
#     parameters:
#       - in: body
#         name: body
#         required: true
#         schema:
#           id: CreateAdmin
#           required:
#             - email
#             - password
#             - name
#           properties:
#             email:
#               type: string
#               example: admin@example.com
#             password:
#               type: string
#               example: strongpassword123
#             name:
#               type: string
#               example: Daniel Uokon
#     responses:
#       201:
#         description: Admin user created successfully
#       400:
#         description: Missing or invalid input data
#     """
#     data = request.get_json() or {}
#     email = data.get("email")
#     password = data.get("password")
#     name = data.get("name")

#     if not all([email, password, name]):
#         return jsonify({"error": "email, password, and name required"}), 400

#     existing = User.query.filter_by(email=email).first()
#     if existing:
#         return jsonify({"error": "user already exists"}), 400

#     # Get or create admin role
#     admin_role = Role.query.filter_by(name="admin").first()
#     if not admin_role:
#         admin_role = Role(name="admin", description="System Administrator")
#         db.session.add(admin_role)
#         db.session.commit()

#     # Create user
#     user = User(email=email, name=name)
#     user.set_password(password)
#     user.roles.append(admin_role)

#     db.session.add(user)
#     db.session.commit()

#     return jsonify({
#         "message": "Admin user created successfully",
#         "user": user.to_dict()
#     }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    User Login
    ---
    tags:
      - Authentication
    description: Authenticates a user and returns JWT tokens.
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          id: Login
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: password123
    responses:
      200:
        description: Successfully logged in
        schema:
          id: LoginResponse
          properties:
            access_token:
              type: string
            refresh_token:
              type: string
            user:
              type: object
      401:
        description: Invalid credentials
      403:
        description: Account disabled
    """
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401
    if not user.is_active:
        return jsonify({"error": "account disabled"}), 403

    # access = create_access_token(identity=user.id, additional_claims={"roles": [r.name for r in user.roles]})
    # refresh = create_refresh_token(identity=user.id)
    access = create_access_token(identity=str(user.id), additional_claims={"roles": [r.name for r in user.roles]})
    refresh = create_refresh_token(identity=str(user.id))

    return jsonify({"access_token": access, "refresh_token": refresh, "user": user.to_dict()}), 200

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh Access Token
    ---
    tags:
      - Authentication
    description: Generate a new access token using a valid refresh token.
    security:
      - Bearer: []
    responses:
      200:
        description: Returns new access token
      401:
        description: Missing or invalid refresh token
    """
    user_id = get_jwt_identity()
    # access = create_access_token(identity=user_id)
    access = create_access_token(identity=str(user_id))
    return jsonify({"access_token": access}), 200


@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    """
    Delete a User
    ---
    tags:
      - Users
    description: Deletes a user by ID.
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        required: true
        type: integer
    responses:
      200:
        description: User deleted successfully
      404:
        description: User not found
      403:
        description: Insufficient permissions
    """
    current_user = User.query.get(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Prevent self-deletion
    if user.id == current_user.id:
        return jsonify({"error": "You cannot delete your own account"}), 403

    # Optionally, check hierarchy permissions
    current_roles = [r.name for r in current_user.roles]
    target_roles = [r.name for r in user.roles]
    if "Super Admin" not in current_roles and "Super Admin" in target_roles:
        return jsonify({"error": "Insufficient permissions to delete this user"}), 403

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User {user.email} deleted successfully"}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Get Current User Info
    ---
    tags:
      - Authentication
    description: Retrieves the authenticated user's details.
    security:
      - Bearer: []
    responses:
      200:
        description: Returns the current logged-in user's data
      404:
        description: User not found
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404
    return jsonify({"user": user.to_dict()}), 200
