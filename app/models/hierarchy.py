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

    # Relationships
    regions = db.relationship('Region', back_populates='state', lazy=True)
    old_groups = db.relationship('OldGroup', back_populates='state', lazy=True)
    groups = db.relationship('Group', back_populates='state', lazy=True)
    districts = db.relationship('District', back_populates='state', lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "code": self.code, "leader": self.leader}


# =========================
# Region
# =========================
class Region(db.Model):
    __tablename__ = 'regions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    leader = db.Column(db.String(100), nullable=True)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)

    # Relationships
    state = db.relationship('State', back_populates='regions')
    old_groups = db.relationship('OldGroup', back_populates='region', lazy=True)
    districts = db.relationship('District', back_populates='region', lazy=True)
    groups = db.relationship('Group', back_populates='region', lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "code": self.code, "leader": self.leader, "state_id": self.state_id}


# =========================
# OldGroup
# =========================
class OldGroup(db.Model):
    __tablename__ = 'old_groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    leader = db.Column(db.String(100), nullable=True)
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
            "state_id": self.state_id,
            "region_id": self.region_id,
            "old_group_id": self.old_group_id,
            "group_id": self.group_id
        }


# run on server after push  - 
# docker exec -it church-backend flask db migrate -m "Restructure hierarchy to State->Region->OldGroups->Groups->Districts"

# # Apply migration
# docker exec -it church-backend flask db upgrade






# # app/models/hierarchy.py
# from app.extensions import db


# class State(db.Model):
#     __tablename__ = 'states'

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     code = db.Column(db.String(20), unique=True, nullable=False)
#     leader = db.Column(db.String(100), nullable=True)

#     regions = db.relationship('Region', backref='state', lazy=True)

#     def __repr__(self):
#         return f"<State {self.name}>"

#     def to_dict(self):
#         return {
#             "id": self.id,
#             "name": self.name,
#             "code": self.code,
#             "leader": self.leader
#         }

# class Region(db.Model):
#     __tablename__ = 'regions'

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     code = db.Column(db.String(20), unique=True, nullable=False)
#     leader = db.Column(db.String(100), nullable=True)

#     state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
#     districts = db.relationship('District', backref='region', lazy=True)

#     def __repr__(self):
#         return f"<Region {self.name}>"

#     def to_dict(self):
#         return {
#             "id": self.id,
#             "name": self.name,
#             "code": self.code,
#             "leader": self.leader,
#             "state_id": self.state_id
#         }

# class District(db.Model):
#     __tablename__ = 'districts'

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     code = db.Column(db.String(20), unique=True, nullable=False)
#     leader = db.Column(db.String(100), nullable=True)

#     state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
#     region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)

#     # groups = db.relationship('Group', backref='district', lazy=True)

#     def __repr__(self):
#         return f"<District {self.name}>"

#     def to_dict(self):
#         return {
#             "id": self.id,
#             "name": self.name,
#             "code": self.code,
#             "leader": self.leader,
#             "state_id": self.state_id,
#             "region_id": self.region_id
#         }

# class Group(db.Model):
#     __tablename__ = 'groups'

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     code = db.Column(db.String(20), unique=True, nullable=False)
#     leader = db.Column(db.String(100), nullable=True)

#     state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
#     region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)
#     district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)

#     # ✅ Unique backrefs
#     state = db.relationship('State', backref='state_groups', lazy=True)
#     region = db.relationship('Region', backref='region_groups', lazy=True)
#     district = db.relationship('District', backref='district_groups', lazy=True)

#     old_groups = db.relationship('OldGroup', back_populates='group', lazy=True)

#     def __repr__(self):
#         return f"<Group {self.name}>"

#     def to_dict(self):
#         return {
#             "id": self.id,
#             "name": self.name,
#             "code": self.code,
#             "leader": self.leader,
#             "state_id": self.state_id,
#             "region_id": self.region_id,
#             "district_id": self.district_id
#         }

# class OldGroup(db.Model):
#     __tablename__ = 'old_groups'

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     code = db.Column(db.String(20), unique=True, nullable=False)
#     leader = db.Column(db.String(100), nullable=True)

#     state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
#     region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)
#     district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)
#     group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)

#     # ✅ Unique backrefs again
#     state = db.relationship('State', backref='old_state_groups', lazy=True)
#     region = db.relationship('Region', backref='old_region_groups', lazy=True)
#     district = db.relationship('District', backref='old_district_groups', lazy=True)
#     # ✅ Back_populates instead of backref
#     group = db.relationship('Group', back_populates='old_groups', lazy=True)

#     def __repr__(self):
#         return f"<OldGroup {self.name}>"

#     def to_dict(self):
#         return {
#             "id": self.id,
#             "name": self.name,
#             "code": self.code,
#             "leader": self.leader,
#             "state_id": self.state_id,
#             "region_id": self.region_id,
#             "district_id": self.district_id,
#             "group_id": self.group_id
#         }

