from ..extensions import db
from datetime import datetime

class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    service_type = db.Column(db.String(50), nullable=False)  # e.g. 'Sunday Worship Service'

    # Hierarchy references
    state_id = db.Column(db.Integer, db.ForeignKey("states.id"), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey("regions.id"), nullable=False)
    old_group_id = db.Column(db.Integer, db.ForeignKey("old_groups.id"), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=True)
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"), nullable=True)  # Now optional

    # Attendance data
    month = db.Column(db.String(20), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    men = db.Column(db.Integer, default=0)
    women = db.Column(db.Integer, default=0)
    youth_boys = db.Column(db.Integer, default=0)
    youth_girls = db.Column(db.Integer, default=0)
    children_boys = db.Column(db.Integer, default=0)
    children_girls = db.Column(db.Integer, default=0)

    # ✅ NEW
    new_comers = db.Column(db.Integer, default=0)   # just a tracker
    tithe_offering = db.Column(db.Numeric(12, 2), default=0.00)

    year = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (optional)
    state = db.relationship("State", backref="attendances")
    region = db.relationship("Region", backref="attendances")
    district = db.relationship("District", backref="attendances")
    group = db.relationship("Group", backref="attendances")
    old_group = db.relationship("OldGroup", backref="attendances")

    def to_dict(self):
        return {
            "id": self.id,
            "service_type": self.service_type,
            "state_id": self.state_id,
            "region_id": self.region_id,
            "district_id": self.district_id,
            "district_name": self.district.name if self.district else None,

            "group_id": self.group_id,
            "old_group_id": self.old_group_id,
            "month": self.month,
            "week": self.week,
            "men": self.men,
            "women": self.women,
            "youth_boys": self.youth_boys,
            "youth_girls": self.youth_girls,
            "children_boys": self.children_boys,
            "children_girls": self.children_girls,
            "new_comers": int(self.new_comers or 0),
            "tithe_offering": float(self.tithe_offering or 0),
            "year": self.year,
            "created_at": self.created_at.isoformat(),
        }
