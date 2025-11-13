from ..extensions import db
from datetime import datetime


class YouthAttendance(db.Model):
    """Simplified Youth attendance model covering weekly and revival types.

    Fields are intentionally permissive so a single table can store both
    'weekly' and 'revival' attendance records. Use the `attendance_type`
    column to distinguish the record shape.

    Columns:
    - id: primary key
    - attendance_type: 'weekly' | 'revival' | 'other'
    - state_id, region_id, district_id, group_id, old_group_id: hierarchy refs
    - period fields: year, month, week (week nullable for revival)
    - member_boys, member_girls, visitor_boys, visitor_girls: weekly counts
    - male, female, testimony, challenges, solutions, remarks: revival fields
    - created_at, updated_at timestamps
    """

    __tablename__ = "youth_attendance"

    id = db.Column(db.Integer, primary_key=True)
    attendance_type = db.Column(db.String(30), nullable=False, default="weekly")

    # Hierarchy references
    state_id = db.Column(db.Integer, db.ForeignKey("states.id"), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey("regions.id"), nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=True)
    old_group_id = db.Column(db.Integer, db.ForeignKey("old_groups.id"), nullable=True)

    # Period fields
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.String(20), nullable=False)
    week = db.Column(db.Integer, nullable=True)

    # Weekly attendance fields
    member_boys = db.Column(db.Integer, default=0)
    member_girls = db.Column(db.Integer, default=0)
    visitor_boys = db.Column(db.Integer, default=0)
    visitor_girls = db.Column(db.Integer, default=0)

    # Revival attendance fields
    male = db.Column(db.Integer, default=0)
    female = db.Column(db.Integer, default=0)
    testimony = db.Column(db.Text, nullable=True)
    challenges = db.Column(db.Text, nullable=True)
    solutions = db.Column(db.Text, nullable=True)
    remarks = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (optional backrefs exist in other models)

    def to_dict(self):
        return {
            "id": self.id,
            "attendance_type": self.attendance_type,
            "state_id": self.state_id,
            "region_id": self.region_id,
            "district_id": self.district_id,
            "group_id": self.group_id,
            "old_group_id": self.old_group_id,
            "year": self.year,
            "month": self.month,
            "week": self.week,
            "member_boys": self.member_boys,
            "member_girls": self.member_girls,
            "visitor_boys": self.visitor_boys,
            "visitor_girls": self.visitor_girls,
            "male": self.male,
            "female": self.female,
            "testimony": self.testimony,
            "challenges": self.challenges,
            "solutions": self.solutions,
            "remarks": self.remarks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    