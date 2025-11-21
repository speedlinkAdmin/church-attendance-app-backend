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


# -----------------------------
# HIERARCHY ACCESS ENFORCEMENT
# -----------------------------

def restrict_by_access(query, user):
    """
    Restrict database query based on user's access level and hierarchy position.
    """
    if not user or not hasattr(user, 'roles'):
        return query
    
    try:
        role_names = [r.name.lower() for r in user.roles]
        
        # Super Admin - no restrictions (check lowercase)
        if "super admin" in role_names:
            return query
        
        # State Admin - restrict to their state
        elif "state admin" in role_names and user.state_id:
            return query.filter_by(state_id=user.state_id)
        
        # Regional Admin - restrict to their region
        elif "region admin" in role_names and user.region_id:
            return query.filter_by(region_id=user.region_id)
        
        # District Admin - restrict to their district
        elif "district admin" in role_names and user.district_id:
            return query.filter_by(district_id=user.district_id)
        
        # No matching role or missing hierarchy data - return empty query
        else:
            return query.filter_by(id=None)
            
    except Exception as e:
        print(f"Error in restrict_by_access: {e}")
        return query.filter_by(id=None)


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


