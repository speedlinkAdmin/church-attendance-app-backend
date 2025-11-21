from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

# Association tables
user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)  # ✅ NEW FIELD
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Hierarchy links
    state_id = db.Column(db.Integer, db.ForeignKey("states.id"), nullable=True)
    region_id = db.Column(db.Integer, db.ForeignKey("regions.id"), nullable=True)
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=True)  # 🆕 ADDED
    old_group_id = db.Column(db.Integer, db.ForeignKey("old_groups.id"), nullable=True)  # 🆕 ADDED

    roles = db.relationship("Role", secondary=user_roles, back_populates="users")

    # 🆕 ADD relationships for the new fields
    group = db.relationship("Group", backref="users")
    old_group = db.relationship("OldGroup", backref="users")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role_name):
        """Check if user has a specific role (case-insensitive)"""
        return any(role.name.lower() == role_name.lower() for role in self.roles)

     # ----- ACCESS LEVEL -----
    def access_level(self):
        """Determine access level based on role."""
        role_names = [r.name for r in self.roles]
        if "Super Admin" in role_names:
            return "Global Access (All States)"
        elif "State Admin" in role_names:
            return f"State Access (State ID: {self.state_id})"
        elif "Region Admin" in role_names:
            return f"Region Access (Region ID: {self.region_id})"
        elif "District Admin" in role_names:
            return f"District Access (District ID: {self.district_id})"
        elif "Group Admin" in role_names:
            return f"Group Access (Group ID: {self.group_id})"  # 🎯 FIXED: Now uses group_id
        elif "Old_Group Admin" in role_names:
            return f"Old_Group Access (Old_Group ID: {self.old_group_id})"
        else:
            return "Basic Access"
        
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "is_active": self.is_active,
            "roles": [r.name for r in self.roles],
            "state_id": self.state_id,
            "region_id": self.region_id,
            "district_id": self.district_id,
            "group_id": self.group_id,  # 🆕 ADDED
            "old_group_id": self.old_group_id,  # 🆕 ADDED
            "access_level": self.access_level(),
        }



class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)

    users = db.relationship("User", secondary=user_roles, back_populates="roles")
    permissions = db.relationship("Permission", secondary=role_permissions, back_populates="roles")

    def __repr__(self):
        return f"<Role {self.name}>"

class Permission(db.Model):
    __tablename__ = "permissions"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(120), unique=True, nullable=False, index=True)  # e.g., 'states.create'
    description = db.Column(db.String(255), nullable=True)

    roles = db.relationship("Role", secondary=role_permissions, back_populates="permissions")

    def __repr__(self):
        return f"<Permission {self.code}>"
