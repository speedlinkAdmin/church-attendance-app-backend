# Super admin user role must be expliccitly called "Super Admin"

from functools import wraps
from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from app.models import User, State, Region, District, Group


from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User
from app.models.hierarchy import OldGroup
from ..extensions import db



# -----------------------------
# ROLE-BASED DECORATOR (OPTIMIZED)
# -----------------------------
def require_role(allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)

            if not user:
                return jsonify({"error": "Invalid user"}), 401

            # Normalize role names: convert to lowercase and replace hyphens/underscores with spaces
            def normalize_role_name(role_name):
                return role_name.lower().replace('-', ' ').replace('_', ' ').strip()
            
            user_role_names = {normalize_role_name(r.name) for r in user.roles}
            allowed_role_names = {normalize_role_name(role) for role in allowed_roles}

            # 🎯 SUPER ADMIN BYPASS: If user is Super Admin, allow access regardless of allowed_roles
            if "super admin" in user_role_names:
                return fn(*args, **kwargs)

            if not user_role_names.intersection(allowed_role_names):
                return jsonify({"error": "You do not have permission for this action"}), 403

            return fn(*args, **kwargs)
        return decorated
    return wrapper



# -----------------------------
# ROLE-BASED DECORATOR
# -----------------------------
# def require_role(allowed_roles):
#     def wrapper(fn):
#         @wraps(fn)
#         def decorated(*args, **kwargs):
#             user_id = get_jwt_identity()
#             user = User.query.get(user_id)

#             if not user:
#                 return jsonify({"error": "Invalid user"}), 401

#             # Normalize role names: convert to lowercase and replace hyphens with spaces
#             def normalize_role_name(role_name):
#                 return role_name.lower().replace('-', ' ').strip()
            
#             user_role_names = {normalize_role_name(r.name) for r in user.roles}
#             allowed_role_names = {normalize_role_name(role) for role in allowed_roles}

#             if not user_role_names.intersection(allowed_role_names):
#                 return jsonify({"error": "You do not have permission for this action"}), 403

#             return fn(*args, **kwargs)
#         return decorated
#     return wrapper


# # -----------------------------
# # HIERARCHY ACCESS ENFORCEMENT
# # -----------------------------

# def restrict_by_access(query, user):
#     """
#     Restrict database query based on user's access level and hierarchy position.
#     """
#     if not user or not hasattr(user, 'roles'):
#         return query
    
#     try:
#         role_names = [r.name.lower() for r in user.roles]
        
#         # Super Admin - no restrictions (check lowercase)
#         if "super admin" in role_names:
#             return query
        
#         # State Admin - restrict to their state
#         elif "state admin" in role_names and user.state_id:
#             return query.filter_by(state_id=user.state_id)
        
#         # Regional Admin - restrict to their region
#         elif "region admin" in role_names and user.region_id:
#             return query.filter_by(region_id=user.region_id)
        
#         # District Admin - restrict to their district
#         elif "district admin" in role_names and user.district_id:
#             return query.filter_by(district_id=user.district_id)
        
#         # No matching role or missing hierarchy data - return empty query
#         else:
#             return query.filter_by(id=None)
            
#     except Exception as e:
#         print(f"Error in restrict_by_access: {e}")
#         return query.filter_by(id=None)


# # -----------------------------
# # HIERARCHY ACCESS ENFORCEMENT (COMPLETE HIERARCHY)
# # -----------------------------

# def restrict_by_access(query, user):
#     """
#     Restrict database query based on user's access level and complete hierarchy position.
#     Now supports: State → Region → District → Group → OldGroup
#     """
#     if not user or not hasattr(user, 'roles'):
#         return query.filter_by(id=None)  # No access if no user/roles
    
#     try:
#         role_names = [r.name.lower() for r in user.roles]
        
#         # 🎯 SUPER ADMIN - no restrictions
#         if "super admin" in role_names:
#             print("🔓 Super Admin - no access restrictions applied")
#             return query
        
#         # 🎯 STATE ADMIN - restrict to their state
#         elif "state admin" in role_names and user.state_id:
#             print(f"🔐 State Admin - filtering by state_id: {user.state_id}")
#             if hasattr(query, 'state_id'):
#                 return query.filter_by(state_id=user.state_id)
#             # For models without state_id, check related hierarchy
#             elif hasattr(query, 'region_id'):
#                 # Get regions in user's state and filter by those regions
#                 state_regions = Region.query.filter_by(state_id=user.state_id).with_entities(Region.id).all()
#                 region_ids = [r[0] for r in state_regions]
#                 return query.filter(query.region_id.in_(region_ids))
        
#         # 🎯 REGION ADMIN - restrict to their region
#         elif "region admin" in role_names and user.region_id:
#             print(f"🔐 Region Admin - filtering by region_id: {user.region_id}")
#             if hasattr(query, 'region_id'):
#                 return query.filter_by(region_id=user.region_id)
#             # For models without region_id, check related hierarchy
#             elif hasattr(query, 'district_id'):
#                 # Get districts in user's region and filter by those districts
#                 region_districts = District.query.filter_by(region_id=user.region_id).with_entities(District.id).all()
#                 district_ids = [d[0] for d in region_districts]
#                 return query.filter(query.district_id.in_(district_ids))
        
#         # 🎯 DISTRICT ADMIN - restrict to their district
#         elif "district admin" in role_names and user.district_id:
#             print(f"🔐 District Admin - filtering by district_id: {user.district_id}")
#             if hasattr(query, 'district_id'):
#                 return query.filter_by(district_id=user.district_id)
#             # For models without district_id, check related hierarchy
#             elif hasattr(query, 'group_id'):
#                 # Get groups in user's district and filter by those groups
#                 district_groups = Group.query.filter_by(district_id=user.district_id).with_entities(Group.id).all()
#                 group_ids = [g[0] for g in district_groups]
#                 return query.filter(query.group_id.in_(group_ids))
        
#         # 🎯 GROUP ADMIN - restrict to their group
#         elif "group admin" in role_names and user.group_id:
#             print(f"🔐 Group Admin - filtering by group_id: {user.group_id}")
#             if hasattr(query, 'group_id'):
#                 return query.filter_by(group_id=user.group_id)
#             # For models without group_id, check related hierarchy
#             elif hasattr(query, 'old_group_id'):
#                 # Get old groups for user's group and filter by those old groups
#                 group_old_groups = OldGroup.query.filter_by(id=user.old_group_id).with_entities(OldGroup.id).all()
#                 old_group_ids = [og[0] for og in group_old_groups]
#                 return query.filter(query.old_group_id.in_(old_group_ids))
            
#          # 🎯 OLD GROUP ADMIN - restrict to their group
#         elif "old_group admin" in role_names and user.old_group_id:
#             print(f"🔐 Old Group Admin - filtering by old_group_id: {user.old_group_id}")
#             if hasattr(query, 'old_group_id'):
#                 return query.filter_by(old_group_id=user.old_group_id)
#             # For models without group_id, check related hierarchy
#             elif hasattr(query, 'group_id'):
#                 # Get old groups for user's group and filter by those old groups
#                 group_old_groups = Group.query.filter_by(id=user.group_id).with_entities(Group.id).all()
#                 old_group_ids = [og[0] for og in group_old_groups]
#                 return query.filter(query.group_id.in_(old_group_ids))
        
#         # No matching role or missing hierarchy data - return empty query
#         else:
#             print("🚫 No valid role or hierarchy data - returning empty query")
#             return query.filter_by(id=None)
            
#     except Exception as e:
#         print(f"❌ Error in restrict_by_access: {e}")
#         return query.filter_by(id=None)

# -----------------------------
# HIERARCHY ACCESS ENFORCEMENT (COMPLETE HIERARCHY) - FIXED VERSION
# -----------------------------

def restrict_by_access(query, user):
    """
    DEBUG VERSION with detailed logging
    """
    print(f"🎯 ENTERING restrict_by_access")
    print(f"🎯 User: {user.id}, Email: {user.email}")
    print(f"🎯 User roles: {[r.name for r in user.roles]}")
    print(f"🎯 User group_id: {user.group_id}")
    
    if not user or not hasattr(user, 'roles'):
        print("❌ No user or roles - returning empty query")
        return query.filter_by(id=None)
    
    try:
        # Get role names (case insensitive)
        role_names = [r.name.lower() for r in user.roles]
        print(f"🎯 Normalized roles: {role_names}")
        
        # Get the model class from the query
        if not query._entities:
            print("❌ No query entities - returning empty query")
            return query.filter_by(id=None)
        
        model_class = query._entities[0].type
        print(f"🎯 Model class: {model_class.__name__}")
        
        # 🎯 Check for Group Admin
        if "group admin" in role_names:
            print(f"✅ FOUND 'group admin' in roles: {role_names}")
            if user.group_id:
                print(f"✅ User has group_id: {user.group_id}")
                
                if model_class == Group:
                    print(f"✅ Processing Group model - filtering by id = {user.group_id}")
                    result = query.filter(Group.id == user.group_id)
                    print(f"✅ Group query SQL: {result}")
                    return result
                
                elif model_class == District:
                    print(f"✅ Processing District model - filtering by group_id = {user.group_id}")
                    result = query.filter(District.group_id == user.group_id)
                    print(f"✅ District query SQL: {result}")
                    return result
                
                else:
                    print(f"❌ Unknown model type for Group Admin: {model_class.__name__}")
                    return query.filter_by(id=None)
            else:
                print("❌ User has 'group admin' role but no group_id")
                return query.filter_by(id=None)
        else:
            print(f"❌ 'group admin' NOT found in roles: {role_names}")
            return query.filter_by(id=None)
            
    except Exception as e:
        print(f"❌ Exception in restrict_by_access: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return query.filter_by(id=None)
    

def get_current_user():
    """Get current user with eager loading of roles for performance"""
    user_id = get_jwt_identity()
    return User.query.options(db.joinedload(User.roles)).get(user_id)

def apply_scope_filters(model, user):
    """
    Automatically restrict query based on user's complete access level.
    Supports full hierarchy: State → Region → District → Group → OldGroup
    """
    if not user:
        return model.query.filter_by(id=None)
    
    # 🎯 SUPER ADMIN BYPASS
    if any(role.name.lower() == "super admin" for role in user.roles):
        print("🔓 Super Admin - full access granted")
        return model.query  # FULL ACCESS

    query = model.query
    print(f"🔍 Applying scope filters for user: {user.id}, roles: {[r.name for r in user.roles]}")

    # 🎯 APPLY HIERARCHICAL RESTRICTIONS (most specific to least specific)
    
    # Group Admin level - most restrictive
    if user.group_id and hasattr(model, "group_id"):
        print(f"🔐 Group Admin - filtering by group_id: {user.group_id}")
        return query.filter(model.group_id == user.group_id)
    
    # District Admin level
    elif user.district_id and hasattr(model, "district_id"):
        print(f"🔐 District Admin - filtering by district_id: {user.district_id}")
        return query.filter(model.district_id == user.district_id)
    
    # Region Admin level  
    elif user.region_id and hasattr(model, "region_id"):
        print(f"🔐 Region Admin - filtering by region_id: {user.region_id}")
        return query.filter(model.region_id == user.region_id)
    
    # State Admin level
    elif user.state_id and hasattr(model, "state_id"):
        print(f"🔐 State Admin - filtering by state_id: {user.state_id}")
        return query.filter(model.state_id == user.state_id)
    
    # 🎯 HANDLE RELATED HIERARCHY FILTERING
    # If model doesn't have the direct field, filter through relationships
    
    # For models with old_group_id but user has group_id
    elif user.group_id and hasattr(model, "old_group_id"):
        print(f"🔐 Filtering by old_group_id through user's group")
        user_group = Group.query.get(user.group_id)
        if user_group and user_group.old_group_id:
            return query.filter(model.old_group_id == user_group.old_group_id)
    
    # For models with district_id but user has group_id
    elif user.group_id and hasattr(model, "district_id"):
        print(f"🔐 Filtering by district_id through user's group")
        user_group = Group.query.get(user.group_id)
        if user_group and user_group.district_id:
            return query.filter(model.district_id == user_group.district_id)
    
    # For models with region_id but user has district_id
    elif user.district_id and hasattr(model, "region_id"):
        print(f"🔐 Filtering by region_id through user's district")
        user_district = District.query.get(user.district_id)
        if user_district and user_district.region_id:
            return query.filter(model.region_id == user_district.region_id)
    
    # For models with state_id but user has region_id
    elif user.region_id and hasattr(model, "state_id"):
        print(f"🔐 Filtering by state_id through user's region")
        user_region = Region.query.get(user.region_id)
        if user_region and user_region.state_id:
            return query.filter(model.state_id == user_region.state_id)

    print("🚫 No applicable scope filters - user may not have access")
    return query.filter_by(id=None)  # No access by default


def scoped_query(model):
    """
    Decorator to apply access filtering automatically to GET, POST, PUT, DELETE.
    Now supports complete hierarchy with proper logging.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"error": "User not found"}), 401
                
            scoped_q = apply_scope_filters(model, user)
            return fn(scoped_q, *args, **kwargs)
        return wrapper
    return decorator

# -----------------------------
# ENHANCED HIERARCHY VALIDATION
# -----------------------------

def validate_hierarchy_access(user, target_entity):
    """
    Validate if user has access to a specific hierarchy entity (State, Region, District, Group, OldGroup)
    Returns True if access granted, False otherwise
    """
    if not user or not target_entity:
        return False
    
    # 🎯 SUPER ADMIN BYPASS
    if any(role.name.lower() == "super admin" for role in user.roles):
        return True
    
    # Determine entity type and check access
    if isinstance(target_entity, State):
        return user.state_id == target_entity.id
    
    elif isinstance(target_entity, Region):
        # User can access if it's their region OR if they're State Admin for that state
        if user.region_id == target_entity.id:
            return True
        if user.state_id == target_entity.state_id and any(r.name.lower() == "state admin" for r in user.roles):
            return True
    
    elif isinstance(target_entity, District):
        # User can access if it's their district OR if they're Region Admin for that region OR State Admin for that state
        if user.district_id == target_entity.id:
            return True
        if user.region_id == target_entity.region_id and any(r.name.lower() == "region admin" for r in user.roles):
            return True
        if user.state_id == target_entity.state_id and any(r.name.lower() == "state admin" for r in user.roles):
            return True
    
    elif isinstance(target_entity, Group):
        # User can access if it's their group OR if they're District Admin for that district, etc.
        if user.group_id == target_entity.id:
            return True
        if user.district_id == target_entity.district_id and any(r.name.lower() == "district admin" for r in user.roles):
            return True
        if user.region_id == target_entity.region_id and any(r.name.lower() == "region admin" for r in user.roles):
            return True
        if user.state_id == target_entity.state_id and any(r.name.lower() == "state admin" for r in user.roles):
            return True
    
    elif isinstance(target_entity, OldGroup):
        # Similar logic for OldGroup
        if user.old_group_id == target_entity.id:
            return True
        # Check through group relationships
        user_group = Group.query.get(user.group_id) if user.group_id else None
        if user_group and user_group.old_group_id == target_entity.id:
            return True
    
    return False


def can_manage_entity(user, entity):
    """
    Check if user can manage (create/update/delete) a specific hierarchy entity
    More restrictive than read access
    """
    if not user or not entity:
        return False
    
    # 🎯 SUPER ADMIN CAN MANAGE ANYTHING
    if any(role.name.lower() == "super admin" for role in user.roles):
        return True
    
    # Entity-specific management rules
    if isinstance(entity, State):
        return user.state_id == entity.id and any(r.name.lower() == "state admin" for r in user.roles)
    
    elif isinstance(entity, Region):
        return user.region_id == entity.id and any(r.name.lower() == "region admin" for r in user.roles)
    
    elif isinstance(entity, District):
        return user.district_id == entity.id and any(r.name.lower() == "district admin" for r in user.roles)
    
    elif isinstance(entity, Group):
        return user.group_id == entity.id and any(r.name.lower() == "group admin" for r in user.roles)
    
    elif isinstance(entity, OldGroup):
        # OldGroup management typically requires higher level access
        return any(r.name.lower() in ["state admin", "region admin"] for r in user.roles)
    
    return False


# def get_current_user():
#     user_id = get_jwt_identity()
#     return User.query.get(user_id)

# def apply_scope_filters(model, user):
#     """Automatically restrict query based on user access level."""
#     if any(role.name == "Super Admin" for role in user.roles):
#         return model.query  # FULL ACCESS

#     query = model.query

#     # Apply hierarchical restriction
#     if user.district_id:
#         if hasattr(model, "district_id"):
#             query = query.filter(model.district_id == user.district_id)

#     elif user.region_id:
#         if hasattr(model, "region_id"):
#             query = query.filter(model.region_id == user.region_id)

#     elif user.state_id:
#         if hasattr(model, "state_id"):
#             query = query.filter(model.state_id == user.state_id)

#     return query


# def scoped_query(model):
#     """
#     Decorator to apply access filtering automatically to GET, POST, PUT, DELETE.
#     """
#     def decorator(fn):
#         @wraps(fn)
#         def wrapper(*args, **kwargs):
#             user = get_current_user()
#             scoped_q = apply_scope_filters(model, user)
#             return fn(scoped_q, *args, **kwargs)
#         return wrapper
#     return decorator


