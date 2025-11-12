from ..extensions import db
from ..models import Attendance

def create_attendance(data):
    attendance = Attendance(**data)
    db.session.add(attendance)
    db.session.commit()
    return attendance

def get_all_attendance(service_type=None, state_id=None, region_id=None, district_id=None, year=None, month=None):
    query = Attendance.query

    if service_type:
        query = query.filter_by(service_type=service_type)
    if state_id:
        query = query.filter_by(state_id=state_id)
    if region_id:
        query = query.filter_by(region_id=region_id)
    if district_id:
        query = query.filter_by(district_id=district_id)
    if year:
        query = query.filter_by(year=year)
    if month:
        query = query.filter_by(month=month)
    
    # ADD THIS RETURN STATEMENT - it was missing!
    return query.all()

def get_attendance_by_id(attendance_id):
    return Attendance.query.get(attendance_id)

def update_attendance(attendance_id, data):
    attendance = Attendance.query.get(attendance_id)
    if not attendance:
        return None
    for key, value in data.items():
        setattr(attendance, key, value)
    db.session.commit()
    return attendance

def delete_attendance(attendance_id):
    attendance = Attendance.query.get(attendance_id)
    if attendance:
        db.session.delete(attendance)
        db.session.commit()
        return True
    return False