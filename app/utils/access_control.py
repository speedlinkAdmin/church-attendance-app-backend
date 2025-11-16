# Super admin user role must be expliccitly called "Super Admin"

from functools import wraps
from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from app.models import User, State, Region, District, Group


from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User

# -----------------------------
# ROLE-BASED DECORATOR
# -----------------------------
def require_role(allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)

            if not user:
                return jsonify({"error": "Invalid user"}), 401

            # Normalize role names: convert to lowercase and replace hyphens with spaces
            def normalize_role_name(role_name):
                return role_name.lower().replace('-', ' ').strip()
            
            user_role_names = {normalize_role_name(r.name) for r in user.roles}
            allowed_role_names = {normalize_role_name(role) for role in allowed_roles}

            if not user_role_names.intersection(allowed_role_names):
                return jsonify({"error": "You do not have permission for this action"}), 403

            return fn(*args, **kwargs)
        return decorated
    return wrapper


# def require_role(allowed_roles):
#     """Decorator to ensure user has at least one allowed role."""

#     def wrapper(fn):
#         @wraps(fn)
#         def decorated(*args, **kwargs):
#             user_id = get_jwt_identity()
#             user = User.query.get(user_id)

#             if not user:
#                 return jsonify({"error": "Invalid user"}), 401

#             user_roles = [r.name.lower() for r in user.roles]

#             # Check if user has ANY allowed role
#             if not any(role.lower() in user_roles for role in allowed_roles):
#                 return jsonify({"error": "You do not have permission for this action"}), 403

#             return fn(*args, **kwargs)

#         return decorated

#     return wrapper


# -----------------------------
# HIERARCHY ACCESS ENFORCEMENT
# -----------------------------

def restrict_by_access(query, user):
    """
    Restrict database query based on user's access level and hierarchy position.
    """
    # Safety check - if user is not a User object, return query unchanged
    if not user or not hasattr(user, 'roles'):
        return query
    
    try:
        role_names = [r.name.lower() for r in user.roles]
        
        # Map your actual role names to expected role names
        # "admin" -> "super admin"
        # "state_manager" -> "state admin" 
        # etc.
        
        # Super Admin - no restrictions (maps to "admin")
        if "Super Admin" in role_names:
            return query
        
        # State Admin - restrict to their state (maps to "state_manager")
        elif "state_admin" in role_names and user.state_id:
            return query.filter_by(state_id=user.state_id)
        
        # Regional Admin - restrict to their region
        elif "region_admin" in role_names and user.region_id:
            return query.filter_by(region_id=user.region_id)
        
        # District Admin - restrict to their district
        elif "district_admin" in role_names and user.district_id:
            return query.filter_by(district_id=user.district_id)
        
        # No matching role or missing hierarchy data - return empty query
        else:
            return query.filter_by(id=None)  # FIXED: Use filter_by(id=None) instead of .none()
            
    except Exception as e:
        # Log the error but return empty query to be safe
        print(f"Error in restrict_by_access: {e}")
        return query.filter_by(id=None)  # FIXED: Use filter_by(id=None)
    

# def restrict_by_access(user, obj):
#     """Ensure user can only access data inside their assigned hierarchy."""

#     # Super Admin = full access
#     role_names = [r.name.lower() for r in user.roles]
#     if "super admin" in role_names:
#         return True

#     # Restrict by state
#     if user.state_id and hasattr(obj, "state_id") and obj.state_id != user.state_id:
#         return False

#     # Restrict by region
#     if user.region_id and hasattr(obj, "region_id") and obj.region_id != user.region_id:
#         return False

#     # Restrict by district
#     if user.district_id and hasattr(obj, "district_id") and obj.district_id != user.district_id:
#         return False

#     return True


def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

def apply_scope_filters(model, user):
    """Automatically restrict query based on user access level."""
    if any(role.name == "Super Admin" for role in user.roles):
        return model.query  # FULL ACCESS

    query = model.query

    # Apply hierarchical restriction
    if user.district_id:
        if hasattr(model, "district_id"):
            query = query.filter(model.district_id == user.district_id)

    elif user.region_id:
        if hasattr(model, "region_id"):
            query = query.filter(model.region_id == user.region_id)

    elif user.state_id:
        if hasattr(model, "state_id"):
            query = query.filter(model.state_id == user.state_id)

    return query


def scoped_query(model):
    """
    Decorator to apply access filtering automatically to GET, POST, PUT, DELETE.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            scoped_q = apply_scope_filters(model, user)
            return fn(scoped_q, *args, **kwargs)
        return wrapper
    return decorator










# from ..models import User, State, Region, District

# def get_user_scope(user: User):
#     """Return the scope of data a user has access to."""
#     if user.district_id:
#         return {"level": "district", "id": user.district_id}
#     elif user.region_id:
#         return {"level": "region", "id": user.region_id}
#     elif user.state_id:
#         return {"level": "state", "id": user.state_id}
#     else:
#         return {"level": "global"}

# def filter_data_by_user_scope(query, user: User):
#     """Filter database queries based on user's assigned scope."""
#     scope = get_user_scope(user)

#     if scope["level"] == "state":
#         return query.filter_by(state_id=scope["id"])
#     elif scope["level"] == "region":
#         return query.filter_by(region_id=scope["id"])
#     elif scope["level"] == "district":
#         return query.filter_by(district_id=scope["id"])
#     else:
#         # Global access (super admin)
#         return query


# # Now, in any controller where you fetch data, you can apply:
# # query = filter_data_by_user_scope(SomeModel.query, current_user)
