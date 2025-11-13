"""app.routes.user_routes

Blueprint and route registration for user-related endpoints.

This module wires the HTTP endpoints to controller functions in
``app.controllers.user_controller`` and applies JWT protection to each
route using ``flask_jwt_extended.jwt_required``.

Notes:
- Register the blueprint on the Flask app with an appropriate prefix,
  for example: ``app.register_blueprint(user_bp, url_prefix='/api/users')``.
- Controllers are responsible for input validation and response shaping.
"""

from flask import Blueprint
from ..controllers import user_controller
from flask_jwt_extended import jwt_required

# Create a blueprint named "users". Keep the module import path relative so
# the package structure remains consistent when the app is initialized.
user_bp = Blueprint("users", __name__)


# Route: GET /
# Description: Return a list of users. Controller handles pagination/filtering.
# Protection: JWT required - client must supply a valid access token.
user_bp.route("/", methods=["GET"])(jwt_required()(user_controller.list_users))


# Route: POST /
# Description: Create a new user. Expects JSON body with user fields.
# Protection: JWT required - only authenticated requests may create users.
user_bp.route("/", methods=["POST"])(jwt_required()(user_controller.create_user))


# Route: PUT /<int:user_id>
# Description: Update an existing user identified by user_id. Controller is
# responsible for verifying the user exists and for returning 404/400 as
# appropriate.
# Protection: JWT required - authenticated requests only.
user_bp.route("/<int:user_id>", methods=["PUT"])(jwt_required()(user_controller.update_user))
