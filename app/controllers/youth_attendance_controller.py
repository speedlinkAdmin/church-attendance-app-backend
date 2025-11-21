from ..extensions import db
from ..models import YouthAttendance
import logging

logger = logging.getLogger(__name__)


def create_youth_attendance(data):
    logger.info(f"Creating youth attendance with data: {data}")
    obj = YouthAttendance(**data)
    db.session.add(obj)
    db.session.commit()
    logger.info(f"Created youth attendance record ID: {obj.id}")
    return obj


# def get_all_youth_attendance(attendance_type=None, state_id=None, region_id=None, district_id=None, year=None, month=None):
#     query = YouthAttendance.query

#     if attendance_type:
#         query = query.filter_by(attendance_type=attendance_type)
#     if state_id:
#         query = query.filter_by(state_id=state_id)
#     if region_id:
#         query = query.filter_by(region_id=region_id)
#     if district_id:
#         query = query.filter_by(district_id=district_id)
#     if year:
#         query = query.filter_by(year=year)
#     if month:
#         query = query.filter_by(month=month)

#     return query.all()

def get_all_youth_attendance(attendance_type=None, state_id=None, region_id=None, district_id=None, year=None, month=None):
    query = YouthAttendance.query

    print(f"🔍 [CONTROLLER] Building query with filters:")
    print(f"   - attendance_type: {attendance_type}")
    print(f"   - state_id: {state_id}") 
    print(f"   - region_id: {region_id}")
    print(f"   - district_id: {district_id}")
    print(f"   - year: {year}")
    print(f"   - month: {month}")

    if attendance_type:
        query = query.filter_by(attendance_type=attendance_type)
        print(f"   ✅ Applied attendance_type filter: {attendance_type}")
    if state_id:
        query = query.filter_by(state_id=state_id)
        print(f"   ✅ Applied state_id filter: {state_id}")
    if region_id:
        query = query.filter_by(region_id=region_id)
        print(f"   ✅ Applied region_id filter: {region_id}")
    if district_id:
        query = query.filter_by(district_id=district_id)
        print(f"   ✅ Applied district_id filter: {district_id}")
    if year:
        query = query.filter_by(year=year)
        print(f"   ✅ Applied year filter: {year}")
    if month:
        query = query.filter_by(month=month)
        print(f"   ✅ Applied month filter: {month}")

    results = query.all()
    print(f"🔍 [CONTROLLER] Query returned {len(results)} records")
    
    return results


def get_youth_attendance_by_id(record_id):
    return YouthAttendance.query.get(record_id)


def update_youth_attendance(record_id, data):
    obj = YouthAttendance.query.get(record_id)
    if not obj:
        return None
    for key, value in data.items():
        setattr(obj, key, value)
    db.session.commit()
    return obj


def delete_youth_attendance(record_id):
    obj = YouthAttendance.query.get(record_id)
    if obj:
        db.session.delete(obj)
        db.session.commit()
        return True
    return False
