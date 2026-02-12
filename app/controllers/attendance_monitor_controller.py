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
        "status": get_attendance_status(district_weeks.get(district.id, 0)),
         # Add group information
        "group_id": district.group_id,
        "group": district.group.name if district.group else None,
        # Also include region/state for hierarchical filtering
        "region_id": district.region_id,
        "region": district.region.name if district.region else None,
        "state_id": district.state_id,
        "state": district.state.name if district.state else None
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
