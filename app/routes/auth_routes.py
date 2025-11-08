from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.user import User, Role, Permission
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/create-admin", methods=["POST"])
def create_admin():
    """
    Create Admin User
    ---
    tags:
      - Authentication
    description: Create a new administrator user account.
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
    """
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")

    if not all([email, password, name]):
        return jsonify({"error": "email, password, and name required"}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "user already exists"}), 400

    # Get or create admin role
    admin_role = Role.query.filter_by(name="admin").first()
    if not admin_role:
        admin_role = Role(name="admin", description="System Administrator")
        db.session.add(admin_role)
        db.session.commit()

    # Create user
    user = User(email=email, name=name)
    user.set_password(password)
    user.roles.append(admin_role)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "Admin user created successfully",
        "user": user.to_dict()
    }), 201

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
