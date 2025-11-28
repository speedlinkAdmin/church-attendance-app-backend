# app/utils/excel_importer.py
import pandas as pd
from app.extensions import db
from app.models import State, Region, OldGroup, Group, District

def safe_strip(value):
    """Safely strip any value - converts to string first"""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()

def import_hierarchy_from_excel(file_path, state_name, state_code="RIV-CEN"):
    """
    Imports hierarchical data from Excel with safe string handling
    """
    try:
        # Read Excel file
        df = pd.read_excel(file_path, sheet_name=0, header=None)
        print(f"Loaded Excel with {len(df)} rows")
        
        # Create state
        state = State.query.filter_by(name=state_name).first()
        if not state:
            state = State(name=state_name, code=state_code)
            db.session.add(state)
            db.session.commit()
            print(f"Created state: {state_name}")

        current_old_group = None
        current_group = None

        for index, row in df.iterrows():
            print(f"Row {index}: {[safe_strip(cell) for cell in row]}")
            
            # Skip empty rows
            if row.isnull().all():
                continue

            # SAFE: Use our safe_strip function for all string operations
            # Detect OldGroup - column 0
            if pd.notna(row[0]):
                cell_value = safe_strip(row[0])
                if "OLD GROUP" in cell_value.upper():
                    old_group_name = cell_value
                    print(f"Processing OldGroup: {old_group_name}")
                    
                    current_old_group = OldGroup.query.filter_by(
                        name=old_group_name, state_id=state.id
                    ).first()
                    if not current_old_group:
                        current_old_group = OldGroup(
                            name=old_group_name,
                            code=old_group_name[:4].upper(),
                            state_id=state.id,
                            region_id=1
                        )
                        db.session.add(current_old_group)
                        db.session.commit()
                    continue

            # Detect Group - column 1  
            if pd.notna(row[1]):
                group_name = safe_strip(row[1])
                print(f"Processing Group: {group_name}")
                
                if current_old_group is None:
                    print("Warning: Group found without OldGroup context")
                    continue
                    
                current_group = Group.query.filter_by(
                    name=group_name, old_group_id=current_old_group.id
                ).first()
                if not current_group:
                    current_group = Group(
                        name=group_name,
                        code=group_name[:4].upper(),
                        state_id=state.id,
                        region_id=1,
                        old_group_id=current_old_group.id
                    )
                    db.session.add(current_group)
                    db.session.commit()
                continue

            # Detect District - column 3
            if pd.notna(row[3]):
                district_name = safe_strip(row[3])
                print(f"Processing District: {district_name}")
                
                if current_group is None:
                    print("Warning: District found without Group context")
                    continue
                    
                district_code = safe_strip(row[0]) if pd.notna(row[0]) else district_name[:4].upper()
                
                existing = District.query.filter_by(
                    name=district_name,
                    group_id=current_group.id,
                    old_group_id=current_old_group.id,
                    state_id=state.id
                ).first()
                if not existing:
                    district = District(
                        name=district_name,
                        code=district_code,
                        state_id=state.id,
                        region_id=1,
                        old_group_id=current_old_group.id,
                        group_id=current_group.id
                    )
                    db.session.add(district)

        db.session.commit()
        return {"message": "Hierarchy imported successfully!"}
        
    except Exception as e:
        db.session.rollback()
        print(f"Import error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        raise e

