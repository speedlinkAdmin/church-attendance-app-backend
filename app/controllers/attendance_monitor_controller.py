from app.models import State, Region, District, Group, OldGroup, Attendance
from app.utils.attendance_monitor import get_attendance_status
from sqlalchemy import func, case
from datetime import datetime
from ..extensions import db

def get_attendance_monitor_summary():
    current_year = datetime.now().year
    current_month = datetime.now().strftime('%B')  # e.g., "November"
    
    # Get all attendance data in ONE query
    attendance_data = db.session.query(
        Attendance.state_id,
        Attendance.region_id, 
        Attendance.district_id,
        Attendance.group_id,
        Attendance.old_group_id,
        func.max(Attendance.week).label('last_week')
    ).filter(
        Attendance.year == current_year,
        Attendance.month == current_month
    ).group_by(
        Attendance.state_id,
        Attendance.region_id,
        Attendance.district_id, 
        Attendance.group_id,
        Attendance.old_group_id
    ).all()
    
    # Convert to dictionaries for fast lookup
    state_weeks = {}
    region_weeks = {}
    district_weeks = {}
    group_weeks = {}
    old_group_weeks = {}
    
    for record in attendance_data:
        if record.state_id:
            state_weeks[record.state_id] = record.last_week
        if record.region_id:
            region_weeks[record.region_id] = record.last_week
        if record.district_id:
            district_weeks[record.district_id] = record.last_week
        if record.group_id:
            group_weeks[record.group_id] = record.last_week
        if record.old_group_id:
            old_group_weeks[record.old_group_id] = record.last_week
    
    summary = {
        "states": [],
        "regions": [],
        "districts": [],
        "groups": [],
        "old_groups": []
    }

    # STATES - Single query
    states = State.query.all()
    summary["states"] = [{
        "id": state.id,
        "name": state.name,
        "last_filled_week": state_weeks.get(state.id, 0),
        "status": get_attendance_status(state_weeks.get(state.id, 0))
    } for state in states]

    # REGIONS - Single query  
    regions = Region.query.all()
    summary["regions"] = [{
        "id": region.id,
        "name": region.name,
        "last_filled_week": region_weeks.get(region.id, 0),
        "status": get_attendance_status(region_weeks.get(region.id, 0))
    } for region in regions]

    # DISTRICTS - Single query
    districts = District.query.all()
    summary["districts"] = [{
        "id": district.id,
        "name": district.name,
        "last_filled_week": district_weeks.get(district.id, 0),
        "status": get_attendance_status(district_weeks.get(district.id, 0))
    } for district in districts]

    # GROUPS - Single query
    groups = Group.query.all()
    summary["groups"] = [{
        "id": group.id,
        "name": group.name,
        "last_filled_week": group_weeks.get(group.id, 0),
        "status": get_attendance_status(group_weeks.get(group.id, 0))
    } for group in groups]

    # OLD GROUPS - Single query
    old_groups = OldGroup.query.all()
    summary["old_groups"] = [{
        "id": old_group.id,
        "name": old_group.name,
        "last_filled_week": old_group_weeks.get(old_group.id, 0),
        "status": get_attendance_status(old_group_weeks.get(old_group.id, 0))
    } for old_group in old_groups]

    return summary














# from app.models import State, Region, District, Group, OldGroup
# from app.utils.attendance_monitor import get_last_attendance_week, get_attendance_status

# def get_attendance_monitor_summary():
#     summary = {
#         "states": [],
#         "regions": [],
#         "districts": [],
#         "groups": [],
#         "old_groups": []
#     }

#     # STATES
#     for state in State.query.all():
#         last_week = get_last_attendance_week("state", state.id)
#         summary["states"].append({
#             "id": state.id,
#             "name": state.name,
#             "last_filled_week": last_week,
#             "status": get_attendance_status(last_week)
#         })

#     # REGIONS
#     for region in Region.query.all():
#         last_week = get_last_attendance_week("region", region.id)
#         summary["regions"].append({
#             "id": region.id,
#             "name": region.name,
#             "last_filled_week": last_week,
#             "status": get_attendance_status(last_week)
#         })

#     # DISTRICTS
#     for district in District.query.all():
#         last_week = get_last_attendance_week("district", district.id)
#         summary["districts"].append({
#             "id": district.id,
#             "name": district.name,
#             "last_filled_week": last_week,
#             "status": get_attendance_status(last_week)
#         })

#     # GROUPS
#     for group in Group.query.all():
#         last_week = get_last_attendance_week("group", group.id)
#         summary["groups"].append({
#             "id": group.id,
#             "name": group.name,
#             "last_filled_week": last_week,
#             "status": get_attendance_status(last_week)
#         })

#     # OLD GROUPS
#     for old_group in OldGroup.query.all():
#         last_week = get_last_attendance_week("old_group", old_group.id)
#         summary["old_groups"].append({
#             "id": old_group.id,
#             "name": old_group.name,
#             "last_filled_week": last_week,
#             "status": get_attendance_status(last_week)
#         })

#     return summary
