# app/utils/excel_importer.py
import pandas as pd
from app.extensions import db
from app.models import State, OldGroup, Group, District

def safe_strip(value):
    """Safely strip any value - converts to string first"""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()

def import_hierarchy_from_excel(file_path, state_name, state_code="RIV-CEN"):
    """
    Fixed: Properly handles multiple Old Groups and assigns groups to correct Old Groups
    """
    print("=== Starting hierarchy import ===")
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path, sheet_name=0, header=None)
        print(f"Loaded Excel with {len(df)} rows, {len(df.columns)} columns")
        
        # Create state
        state = State.query.filter_by(name=state_name).first()
        if not state:
            state = State(name=state_name, code=state_code)
            db.session.add(state)
            db.session.commit()
            print(f"Created state: {state_name} (ID: {state.id})")

        current_old_group = None
        old_groups_created = 0
        groups_created = 0
        districts_created = 0

        for index, row in df.iterrows():
            # Convert all cells to strings for safe processing
            row_str = [safe_strip(cell) for cell in row]
            
            # Skip completely empty rows
            if all(cell == '' for cell in row_str):
                continue

            # DEBUG: Show rows that might contain Old Groups
            if any("OLD GROUP" in cell.upper() for cell in row_str if cell):
                print(f"Row {index} MAY CONTAIN OLD GROUP: {[cell for cell in row_str if cell]}")
            
            # DETECT OLD GROUP - Check ALL columns for "OLD GROUP"
            for col_idx, cell_value in enumerate(row_str):
                if cell_value and "OLD GROUP" in cell_value.upper():
                    old_group_name = cell_value
                    print(f"🎯 FOUND OLD GROUP: '{old_group_name}' in column {col_idx}")
                    
                    # Find or create the Old Group
                    current_old_group = OldGroup.query.filter_by(
                        name=old_group_name, state_id=state.id
                    ).first()
                    if not current_old_group:
                        current_old_group = OldGroup(
                            name=old_group_name,
                            code=old_group_name.replace("OLD GROUP", "").strip()[:4].upper(),
                            state_id=state.id,
                            region_id=1
                        )
                        db.session.add(current_old_group)
                        db.session.commit()
                        old_groups_created += 1
                        print(f"✅ CREATED OldGroup: {old_group_name} (ID: {current_old_group.id})")
                    else:
                        print(f"📁 USING existing OldGroup: {old_group_name} (ID: {current_old_group.id})")
                    
                    # Once we find an Old Group, break and move to next row
                    break

            # Only process groups and districts if we have a current Old Group
            if current_old_group:
                # Look for group names in this row (they typically appear after Old Group rows)
                for col_idx in range(len(row_str)):
                    group_name = row_str[col_idx]
                    
                    # Skip empty cells, numbers, and Old Group indicators
                    if (not group_name or 
                        group_name.isdigit() or 
                        "OLD GROUP" in group_name.upper()):
                        continue
                    
                    # Check if this looks like a group name 
                    # Groups are typically multi-word and don't contain numbers
                    if (len(group_name.split()) >= 2 or 
                        any(word in group_name.upper() for word in ['GROUP', 'DISTRICT', 'UNIPORT', 'CORPER', 'FELLOWSHIP'])):
                        
                        print(f"🎯 FOUND GROUP '{group_name}' under OldGroup '{current_old_group.name}'")
                        
                        # Find or create the Group
                        group = Group.query.filter_by(
                            name=group_name, old_group_id=current_old_group.id
                        ).first()
                        if not group:
                            group = Group(
                                name=group_name,
                                code=group_name[:4].upper(),
                                state_id=state.id,
                                region_id=1,
                                old_group_id=current_old_group.id
                            )
                            db.session.add(group)
                            db.session.commit()
                            groups_created += 1
                            print(f"✅ CREATED Group: {group_name} (ID: {group.id}) under {current_old_group.name}")
                            
                            # Now process districts under this group
                            # Districts are in the same column but in subsequent rows
                            district_start_row = index + 1
                            for dist_row_idx in range(district_start_row, min(district_start_row + 20, len(df))):
                                district_name = safe_strip(df.iloc[dist_row_idx, col_idx])
                                
                                # Stop when we hit another group, Old Group, or empty row
                                if (not district_name or 
                                    district_name.isdigit() or
                                    any(word in district_name.upper() for word in ['GROUP', 'OLD GROUP']) or
                                    dist_row_idx >= len(df)):
                                    break
                                
                                # Get district code from column 0 of the same row
                                district_code = safe_strip(df.iloc[dist_row_idx, 0])
                                if not district_code or district_code.isdigit():
                                    district_code = district_name[:4].upper()
                                
                                # Only create district if it's a valid name (not numbers, not group-like)
                                if (district_name and 
                                    not district_name.isdigit() and 
                                    "GROUP" not in district_name.upper()):
                                    
                                    print(f"  🎯 FOUND DISTRICT: {district_name} (Code: {district_code})")
                                    
                                    # Check if district already exists
                                    existing = District.query.filter_by(
                                        name=district_name,
                                        group_id=group.id,
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
                                            group_id=group.id
                                        )
                                        db.session.add(district)
                                        districts_created += 1
                                        print(f"  ✅ CREATED District: {district_name} under {group.name}")

        db.session.commit()
        
        print(f"\n=== IMPORT SUMMARY ===")
        print(f"Old Groups created: {old_groups_created}")
        print(f"Groups created: {groups_created}") 
        print(f"Districts created: {districts_created}")
        print("=== Import completed successfully! ===")
        
        return {
            "message": "Hierarchy imported successfully!",
            "summary": {
                "old_groups": old_groups_created,
                "groups": groups_created,
                "districts": districts_created
            }
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ IMPORT FAILED: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise e







# # app/utils/excel_importer_new.py
# import pandas as pd
# from app.extensions import db
# from app.models import State, OldGroup, Group, District

# def safe_strip(value):
#     """Safely strip any value - converts to string first"""
#     if value is None or pd.isna(value):
#         return ""
#     return str(value).strip()

# def import_hierarchy_from_excel_new(file_path, state_name, state_code="RIV-CEN"):
#     """
#     NEW: Completely safe import function
#     """
#     print("=== Using NEW import function ===")
    
#     try:
#         # Read Excel file
#         df = pd.read_excel(file_path, sheet_name=0, header=None)
#         print(f"Loaded Excel with {len(df)} rows, {len(df.columns)} columns")
        
#         # Convert ALL data to strings to avoid .strip() issues
#         df_str = df.astype(str)
#         print("Converted all cells to strings")
        
#         # Create state
#         state = State.query.filter_by(name=state_name).first()
#         if not state:
#             state = State(name=state_name, code=state_code)
#             db.session.add(state)
#             db.session.commit()
#             print(f"Created state: {state_name} (ID: {state.id})")

#         current_old_group = None
#         current_group = None

#         for index, row in df_str.iterrows():  # Use the string-converted dataframe
#             print(f"Processing row {index}: {list(row)}")
            
#             # Skip empty rows
#             if all(cell == 'nan' for cell in row):
#                 continue

#             # Detect OldGroup - column 0
#             if row[0] != 'nan' and "OLD GROUP" in row[0].upper():
#                 old_group_name = row[0].strip()
#                 print(f"Found OldGroup: {old_group_name}")
                
#                 current_old_group = OldGroup.query.filter_by(
#                     name=old_group_name, state_id=state.id
#                 ).first()
#                 if not current_old_group:
#                     current_old_group = OldGroup(
#                         name=old_group_name,
#                         code=old_group_name[:4].upper(),
#                         state_id=state.id,
#                         region_id=1
#                     )
#                     db.session.add(current_old_group)
#                     db.session.commit()
#                     print(f"Created OldGroup: {old_group_name} (ID: {current_old_group.id})")
#                 continue

#             # Detect Group - column 1  
#             if row[1] != 'nan':
#                 group_name = row[1].strip()
#                 print(f"Found Group: {group_name}")
                
#                 if current_old_group is None:
#                     print("Warning: Group found without OldGroup context")
#                     continue
                    
#                 current_group = Group.query.filter_by(
#                     name=group_name, old_group_id=current_old_group.id
#                 ).first()
#                 if not current_group:
#                     current_group = Group(
#                         name=group_name,
#                         code=group_name[:4].upper(),
#                         state_id=state.id,
#                         region_id=1,
#                         old_group_id=current_old_group.id
#                     )
#                     db.session.add(current_group)
#                     db.session.commit()
#                     print(f"Created Group: {group_name} (ID: {current_group.id})")
#                 continue

#             # Detect District - column 3
#             if row[3] != 'nan':
#                 district_name = row[3].strip()
#                 print(f"Found District: {district_name}")
                
#                 if current_group is None:
#                     print("Warning: District found without Group context")
#                     continue
                    
#                 district_code = row[0].strip() if row[0] != 'nan' else district_name[:4].upper()
                
#                 existing = District.query.filter_by(
#                     name=district_name,
#                     group_id=current_group.id,
#                     old_group_id=current_old_group.id,
#                     state_id=state.id
#                 ).first()
#                 if not existing:
#                     district = District(
#                         name=district_name,
#                         code=district_code,
#                         state_id=state.id,
#                         region_id=1,
#                         old_group_id=current_old_group.id,
#                         group_id=current_group.id
#                     )
#                     db.session.add(district)
#                     print(f"Created District: {district_name}")

#         db.session.commit()
#         print("=== Import completed successfully ===")
#         return {"message": "Hierarchy imported successfully!"}
        
#     except Exception as e:
#         db.session.rollback()
#         print(f"=== Import failed ===")
#         print(f"Error: {str(e)}")
#         print(f"Error type: {type(e).__name__}")
#         import traceback
#         print(f"Traceback: {traceback.format_exc()}")
#         raise e