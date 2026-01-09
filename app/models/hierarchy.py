from app.extensions import db

# =========================
# State
# =========================
class State(db.Model):
    __tablename__ = 'states'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20),  nullable=False)
    leader = db.Column(db.String(100), nullable=True)
    leader_email = db.Column(db.String(120), nullable=True)
    leader_phone = db.Column(db.String(20), nullable=True)

    # Relationships
    regions = db.relationship('Region', back_populates='state', lazy=True)
    old_groups = db.relationship('OldGroup', back_populates='state', lazy=True)
    groups = db.relationship('Group', back_populates='state', lazy=True)
    districts = db.relationship('District', back_populates='state', lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "code": self.code, "leader": self.leader, "leader_email": self.leader_email, "leader_phone": self.leader_phone}


# =========================
# Region
# =========================
class Region(db.Model):
    __tablename__ = 'regions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    leader = db.Column(db.String(100), nullable=True)
    leader_email = db.Column(db.String(120), nullable=True)
    leader_phone = db.Column(db.String(20), nullable=True)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)

    # Relationships
    state = db.relationship('State', back_populates='regions')
    old_groups = db.relationship('OldGroup', back_populates='region', lazy=True)
    districts = db.relationship('District', back_populates='region', lazy=True)
    groups = db.relationship('Group', back_populates='region', lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "code": self.code, "leader": self.leader, "state_id": self.state_id, "leader_email": self.leader_email, "leader_phone": self.leader_phone}


# =========================
# OldGroup
# =========================
class OldGroup(db.Model):
    __tablename__ = 'old_groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    leader = db.Column(db.String(100), nullable=True)
    leader_email = db.Column(db.String(120), nullable=True)
    leader_phone = db.Column(db.String(20), nullable=True)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)

    # Relationships
    state = db.relationship('State', back_populates='old_groups')
    region = db.relationship('Region', back_populates='old_groups')
    groups = db.relationship('Group', back_populates='old_group', lazy=True)
    districts = db.relationship('District', back_populates='old_group', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "leader": self.leader,
            "leader_email": self.leader_email,
            "leader_phone": self.leader_phone,
            "state_id": self.state_id,
            "region_id": self.region_id
        }


# =========================
# Group
# =========================
class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    leader = db.Column(db.String(100), nullable=True)
    leader_email = db.Column(db.String(120), nullable=True)
    leader_phone = db.Column(db.String(20), nullable=True)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)
    old_group_id = db.Column(db.Integer, db.ForeignKey('old_groups.id'), nullable=False)

    # Relationships
    state = db.relationship('State', back_populates='groups')
    region = db.relationship('Region', back_populates='groups')
    old_group = db.relationship('OldGroup', back_populates='groups')
    districts = db.relationship('District', back_populates='group', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "leader": self.leader,
            "leader_email": self.leader_email,
            "leader_phone": self.leader_phone,
            "state_id": self.state_id,
            "region_id": self.region_id,
            "old_group_id": self.old_group_id
        }


# =========================
# District
# =========================
class District(db.Model):
    __tablename__ = 'districts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20),  nullable=False)
    leader = db.Column(db.String(100), nullable=True)
    leader_email = db.Column(db.String(120), nullable=True)
    leader_phone = db.Column(db.String(20), nullable=True)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)
    old_group_id = db.Column(db.Integer, db.ForeignKey('old_groups.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)

    # Relationships
    state = db.relationship('State', back_populates='districts')
    region = db.relationship('Region', back_populates='districts')
    old_group = db.relationship('OldGroup', back_populates='districts')
    group = db.relationship('Group', back_populates='districts')

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "leader": self.leader,
            "leader_email": self.leader_email,
            "leader_phone": self.leader_phone,
            "state_id": self.state_id,
            "region_id": self.region_id,
            "old_group_id": self.old_group_id,
            "group_id": self.group_id
        }


# run on server after push  - 
# docker exec -it church-backend flask db migrate -m "Restructure hierarchy to State->Region->OldGroups->Groups->Districts"

# # Apply migration
# docker exec -it church-backend flask db upgrade

