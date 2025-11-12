# app/models/hierarchy.py
from app.extensions import db


class State(db.Model):
    __tablename__ = 'states'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    leader = db.Column(db.String(100), nullable=True)

    regions = db.relationship('Region', backref='state', lazy=True)

    def __repr__(self):
        return f"<State {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "leader": self.leader
        }

class Region(db.Model):
    __tablename__ = 'regions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    leader = db.Column(db.String(100), nullable=True)

    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    districts = db.relationship('District', backref='region', lazy=True)

    def __repr__(self):
        return f"<Region {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "leader": self.leader,
            "state_id": self.state_id
        }

class District(db.Model):
    __tablename__ = 'districts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    leader = db.Column(db.String(100), nullable=True)

    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)

    # groups = db.relationship('Group', backref='district', lazy=True)

    def __repr__(self):
        return f"<District {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "leader": self.leader,
            "state_id": self.state_id,
            "region_id": self.region_id
        }

class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    leader = db.Column(db.String(100), nullable=True)

    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)

    # ✅ Unique backrefs
    state = db.relationship('State', backref='state_groups', lazy=True)
    region = db.relationship('Region', backref='region_groups', lazy=True)
    district = db.relationship('District', backref='district_groups', lazy=True)

    old_groups = db.relationship('OldGroup', back_populates='group', lazy=True)

    def __repr__(self):
        return f"<Group {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "leader": self.leader,
            "state_id": self.state_id,
            "region_id": self.region_id,
            "district_id": self.district_id
        }

class OldGroup(db.Model):
    __tablename__ = 'old_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    leader = db.Column(db.String(100), nullable=True)

    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)

    # ✅ Unique backrefs again
    state = db.relationship('State', backref='old_state_groups', lazy=True)
    region = db.relationship('Region', backref='old_region_groups', lazy=True)
    district = db.relationship('District', backref='old_district_groups', lazy=True)
    # ✅ Back_populates instead of backref
    group = db.relationship('Group', back_populates='old_groups', lazy=True)

    def __repr__(self):
        return f"<OldGroup {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "leader": self.leader,
            "state_id": self.state_id,
            "region_id": self.region_id,
            "district_id": self.district_id,
            "group_id": self.group_id
        }


# class State(db.Model):
#     __tablename__ = 'states'

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     code = db.Column(db.String(20), unique=True, nullable=False)
#     leader = db.Column(db.String(100), nullable=True)

#     regions = db.relationship('Region', backref='state', lazy=True)

#     def __repr__(self):
#         return f"<State {self.name}>"

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

# class District(db.Model):
#     __tablename__ = 'districts'

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     code = db.Column(db.String(20), unique=True, nullable=False)
#     leader = db.Column(db.String(100), nullable=True)

#     state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
#     region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)

#     groups = db.relationship('Group', backref='district', lazy=True)

#     def __repr__(self):
#         return f"<District {self.name}>"

# class Group(db.Model):
#     __tablename__ = 'groups'

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     code = db.Column(db.String(20), unique=True, nullable=False)
#     leader = db.Column(db.String(100), nullable=True)

#     state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
#     region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)
#     district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)

#     old_groups = db.relationship('OldGroup', backref='group', lazy=True)

#     def __repr__(self):
#         return f"<Group {self.name}>"

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

#     def __repr__(self):
#         return f"<OldGroup {self.name}>"
