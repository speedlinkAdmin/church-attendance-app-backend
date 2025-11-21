# app/routes/profile_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import User

profile_bp = Blueprint('profile_bp', __name__)

@profile_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get current user profile
    ---
    tags:
      - Profile
    description: Get the current authenticated user's profile information
    security:
      - Bearer: []
    responses:
      200:
        description: User profile data
      401:
        description: Unauthorized
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({
            "message": "Profile retrieved successfully",
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@profile_bp.route('/profile/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """
    Change user password
    ---
    tags:
      - Profile
    description: Change the current user's password
    security:
      - Bearer: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: ChangePassword
          required:
            - current_password
            - new_password
            - confirm_new_password
          properties:
            current_password:
              type: string
              example: "oldpassword123"
            new_password:
              type: string
              example: "newpassword456"
            confirm_new_password:
              type: string
              example: "newpassword456"
    responses:
      200:
        description: Password changed successfully
      400:
        description: Invalid input or validation error
      401:
        description: Unauthorized or current password incorrect
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        
        # Validate required fields
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_new_password = data.get('confirm_new_password')
        
        if not all([current_password, new_password, confirm_new_password]):
            return jsonify({"error": "All password fields are required"}), 400
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({"error": "Current password is incorrect"}), 401
        
        # Check if new passwords match
        if new_password != confirm_new_password:
            return jsonify({"error": "New passwords do not match"}), 400
        
        # Check if new password is different from current password
        if user.check_password(new_password):
            return jsonify({"error": "New password cannot be the same as current password"}), 400
        
        # Validate password strength (optional - add your requirements)
        if len(new_password) < 6:
            return jsonify({"error": "Password must be at least 6 characters long"}), 400
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            "message": "Password changed successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@profile_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update user profile
    ---
    tags:
      - Profile
    description: Update the current user's profile information
    security:
      - Bearer: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: UpdateProfile
          properties:
            name:
              type: string
              example: "John Doe Updated"
            phone:
              type: string
              example: "+2348012345678"
            email:
              type: string
              example: "updated@example.com"
    responses:
      200:
        description: Profile updated successfully
      400:
        description: Invalid input or validation error
      409:
        description: Email already exists
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Check for email uniqueness if email is being updated
        new_email = data.get('email')
        if new_email and new_email != user.email:
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({"error": "Email already exists"}), 409
        
        # Update allowed fields
        updateable_fields = ['name', 'email', 'phone']
        
        for field in updateable_fields:
            if field in data and data[field] is not None:
                setattr(user, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            "message": "Profile updated successfully",
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500