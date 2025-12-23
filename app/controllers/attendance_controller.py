from ..extensions import db
from ..models import Attendance

def create_attendance(data):

    data.setdefault("new_comers", 0)
    data.setdefault("tithe_offering", 0.00)
    
    attendance = Attendance(**data)
    db.session.add(attendance)
    db.session.commit()
    return attendance


def get_all_attendance(service_type=None, state_id=None, region_id=None, district_id=None, 
                      group_id=None, old_group_id=None, year=None, month=None):
    query = Attendance.query

    print(f"🔍 [ATTENDANCE CONTROLLER] Building query with filters:")
    print(f"   - service_type: {service_type}")
    print(f"   - state_id: {state_id}") 
    print(f"   - region_id: {region_id}")
    print(f"   - district_id: {district_id}")
    # ... other filters

    # Only apply filters if they are not None
    if service_type:
        query = query.filter_by(service_type=service_type)
    if state_id is not None:  # Important: check for None, not truthy
        query = query.filter_by(state_id=state_id)
    if region_id is not None:  # Important: check for None, not truthy  
        query = query.filter_by(region_id=region_id)
    if district_id is not None:  # Important: check for None, not truthy
        query = query.filter_by(district_id=district_id)
    if group_id:
        query = query.filter_by(group_id=group_id)
    if old_group_id:
        query = query.filter_by(old_group_id=old_group_id)
    if year:
        query = query.filter_by(year=year)
    if month:
        query = query.filter_by(month=month)
    
    results = query.all()
    print(f"🔍 [ATTENDANCE CONTROLLER] Query returned {len(results)} records")
    
    return results


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