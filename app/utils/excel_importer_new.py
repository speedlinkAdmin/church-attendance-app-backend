# app/utils/excel_importer_new.py
import pandas as pd
from app.extensions import db
from app.models import State, OldGroup, Group, District

def safe_strip(value):
    """Safely strip any value - converts to string first"""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()

def import_hierarchy_from_excel_new(file_path, state_name, state_code="RIV-CEN"):
    """
    NEW: Completely safe import function
    """
    print("=== Using NEW import function ===")
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path, sheet_name=0, header=None)
        print(f"Loaded Excel with {len(df)} rows, {len(df.columns)} columns")
        
        # Convert ALL data to strings to avoid .strip() issues
        df_str = df.astype(str)
        print("Converted all cells to strings")
        
        # Create state
        state = State.query.filter_by(name=state_name).first()
        if not state:
            state = State(name=state_name, code=state_code)
            db.session.add(state)
            db.session.commit()
            print(f"Created state: {state_name} (ID: {state.id})")

        current_old_group = None
        current_group = None

        for index, row in df_str.iterrows():  # Use the string-converted dataframe
            print(f"Processing row {index}: {list(row)}")
            
            # Skip empty rows
            if all(cell == 'nan' for cell in row):
                continue

            # Detect OldGroup - column 0
            if row[0] != 'nan' and "OLD GROUP" in row[0].upper():
                old_group_name = row[0].strip()
                print(f"Found OldGroup: {old_group_name}")
                
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
                    print(f"Created OldGroup: {old_group_name} (ID: {current_old_group.id})")
                continue

            # Detect Group - column 1  
            if row[1] != 'nan':
                group_name = row[1].strip()
                print(f"Found Group: {group_name}")
                
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
                    print(f"Created Group: {group_name} (ID: {current_group.id})")
                continue

            # Detect District - column 3
            if row[3] != 'nan':
                district_name = row[3].strip()
                print(f"Found District: {district_name}")
                
                if current_group is None:
                    print("Warning: District found without Group context")
                    continue
                    
                district_code = row[0].strip() if row[0] != 'nan' else district_name[:4].upper()
                
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
                    print(f"Created District: {district_name}")

        db.session.commit()
        print("=== Import completed successfully ===")
        return {"message": "Hierarchy imported successfully!"}
        
    except Exception as e:
        db.session.rollback()
        print(f"=== Import failed ===")
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise e