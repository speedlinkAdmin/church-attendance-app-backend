# app/utils/excel_importer_enhanced.py
import pandas as pd
from app.extensions import db
from app.models import State, Region, OldGroup, Group, District, User, Role

def safe_strip(value):
    """Safely strip any value - converts to string first"""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()

def create_group_user(group_name, group, district=None):
    """
    Create a user for a group with proper hierarchy links
    Username/email format: groupname@thedcmp.org (lowercase, no spaces)
    """
    # Clean group name for email
    clean_name = group_name.lower().replace(' ', '_').replace("'", "").replace("-", "_")
    email = f"{clean_name}"
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        print(f"📧 User already exists, updating: {email}")
        user = existing_user
    else:
        print(f"👤 CREATING User: {email} for group '{group_name}'")
        user = User(
            email=email,
            name=f"{group_name} Admin",
            phone=None
        )
        user.set_password("12345678")  # Default password
    
    # Set hierarchy links - CRITICAL FOR ACCESS CONTROL
    user.state_id = group.state_id
    user.region_id = group.region_id
    user.district_id = district.id if district else None
    
    # Assign Group Admin role
    group_admin_role = Role.query.filter_by(name="Group Admin").first()
    if group_admin_role and group_admin_role not in user.roles:
        user.roles.append(group_admin_role)
        print(f"✅ Assigned Group Admin role to {email}")
    elif not group_admin_role:
        print(f"⚠️  Warning: Group Admin role not found!")
    
    if not existing_user:
        db.session.add(user)
    
    print(f"🔗 User {email} linked to - State: {user.state_id}, Region: {user.region_id}, District: {user.district_id}")
    return user

def import_hierarchy_from_excel(file_path, state_name, state_code="RIV-CEN", region_name="Rivers Central Region"):
    """
    Enhanced version that properly links users to hierarchy
    """
    print("=== Starting ENHANCED hierarchy import ===")
    
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
            print(f"✅ Created state: {state_name} (ID: {state.id})")
        else:
            print(f"📁 Using existing state: {state_name} (ID: {state.id})")
        
        # Create region
        region = Region.query.filter_by(name=region_name, state_id=state.id).first()
        if not region:
            region = Region(
                name=region_name,
                code=region_name[:4].upper(),
                state_id=state.id
            )
            db.session.add(region)
            db.session.commit()
            print(f"✅ Created region: {region_name} (ID: {region.id})")
        else:
            print(f"📁 Using existing region: {region_name} (ID: {region.id})")
        
        current_old_group = None
        old_groups_created = 0
        groups_created = 0
        districts_created = 0
        users_created = 0
        
        # Track groups we process to avoid duplicates
        processed_groups = set()
        
        for index, row in df.iterrows():
            # Convert all cells to strings for safe processing
            row_str = [safe_strip(cell) for cell in row]
            
            # Skip completely empty rows
            if all(cell == '' for cell in row_str):
                continue
            
            # DETECT OLD GROUP - Check ALL columns for "OLD GROUP"
            for col_idx, cell_value in enumerate(row_str):
                if cell_value and "OLD GROUP" in cell_value.upper():
                    old_group_name = cell_value
                    print(f"\n🎯 FOUND OLD GROUP: '{old_group_name}'")
                    
                    # Create the Old Group
                    current_old_group = OldGroup(
                        name=old_group_name,
                        code=old_group_name.replace("OLD GROUP", "").strip()[:4].upper(),
                        state_id=state.id,
                        region_id=region.id
                    )
                    db.session.add(current_old_group)
                    db.session.commit()
                    old_groups_created += 1
                    print(f"✅ CREATED OldGroup: {old_group_name} (ID: {current_old_group.id})")
                    break
            
            # Process groups and districts if we have a current Old Group
            if current_old_group:
                for col_idx in range(len(row_str)):
                    group_name = row_str[col_idx]
                    
                    # Skip empty cells, numbers, and Old Group indicators
                    if (not group_name or
                        group_name.isdigit() or
                        "OLD GROUP" in group_name.upper()):
                        continue
                    
                    # Check if this looks like a group name
                    if (len(group_name.split()) >= 2 or
                        any(word in group_name.upper() for word in ['GROUP', 'DISTRICT', 'UNIPORT', 'CORPER', 'FELLOWSHIP'])):
                        
                        group_key = f"{group_name}_{current_old_group.id}"
                        if group_key in processed_groups:
                            continue
                        processed_groups.add(group_key)
                        
                        print(f"\n🎯 PROCESSING GROUP: '{group_name}' under '{current_old_group.name}'")
                        
                        # Create the Group with proper hierarchy links
                        group = Group(
                            name=group_name,
                            code=group_name[:4].upper(),
                            state_id=state.id,
                            region_id=region.id,
                            old_group_id=current_old_group.id
                        )
                        db.session.add(group)
                        db.session.commit()
                        groups_created += 1
                        print(f"✅ CREATED Group: {group_name} (ID: {group.id})")
                        
                        # 🆕 CREATE USER FOR THIS GROUP with proper hierarchy links
                        group_user = create_group_user(group_name, group)
                        if group_user:
                            users_created += 1
                        
                        # Process districts under this group
                        district_start_row = index + 1
                        district_count = 0
                        
                        for dist_row_idx in range(district_start_row, min(district_start_row + 30, len(df))):
                            district_name = safe_strip(df.iloc[dist_row_idx, col_idx])
                            
                            # Stop when we hit another group, Old Group, or empty row
                            if (not district_name or
                                district_name.isdigit() or
                                any(word in district_name.upper() for word in ['GROUP', 'OLD GROUP']) or
                                dist_row_idx >= len(df)):
                                if district_count > 0:  # Only break if we found at least one district
                                    break
                                else:
                                    continue
                            
                            # Get district code from column 0 of the same row
                            district_code = safe_strip(df.iloc[dist_row_idx, 0])
                            if not district_code or district_code.isdigit():
                                district_code = district_name[:4].upper()
                            
                            # Only create district if it's a valid name
                            if (district_name and
                                not district_name.isdigit() and
                                "GROUP" not in district_name.upper()):
                                
                                print(f"  🎯 FOUND DISTRICT: {district_name}")
                                
                                district = District(
                                    name=district_name,
                                    code=district_code,
                                    state_id=state.id,
                                    region_id=region.id,
                                    old_group_id=current_old_group.id,
                                    group_id=group.id
                                )
                                db.session.add(district)
                                db.session.commit()
                                districts_created += 1
                                district_count += 1
                                print(f"  ✅ CREATED District: {district_name} (ID: {district.id})")
                                
                                # 🆕 CREATE USER FOR THIS DISTRICT (Optional - uncomment if needed)
                                # district_user = create_group_user(
                                #     f"{district_name} District", 
                                #     group, 
                                #     district
                                # )
                                # if district_user:
                                #     users_created += 1
        
        db.session.commit()
        
        print(f"\n=== IMPORT SUMMARY ===")
        print(f"✅ States: 1")
        print(f"✅ Regions: 1") 
        print(f"✅ Old Groups: {old_groups_created}")
        print(f"✅ Groups: {groups_created}")
        print(f"✅ Districts: {districts_created}")
        print(f"✅ Users: {users_created}")
        print("🎉 Enhanced import completed successfully!")
        
        return {
            "message": "Enhanced hierarchy imported successfully with proper user links!",
            "summary": {
                "states": 1,
                "regions": 1,
                "old_groups": old_groups_created,
                "groups": groups_created,
                "districts": districts_created,
                "users": users_created
            }
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ IMPORT FAILED: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise e










# # app/utils/excel_importer.py
# import pandas as pd
# from app.extensions import db
# from app.models import State, OldGroup, Group, District, User, Role

# def safe_strip(value):
#     """Safely strip any value - converts to string first"""
#     if value is None or pd.isna(value):
#         return ""
#     return str(value).strip()

# def create_group_user(group_name, group_id, district_id=None):
#     """
#     Create a user for a group with default password
#     Username/email format: groupname@thedcmp.org (lowercase, no spaces)
#     """
#     # Clean group name for email
#     clean_name = group_name.lower().replace(' ', '_').replace("'", "").replace("-", "_")
#     email = f"{clean_name}@thedcmp.org"
    
#     # Check if user already exists
#     existing_user = User.query.filter_by(email=email).first()
#     if existing_user:
#         print(f"📧 User already exists: {email}")
#         return existing_user
    
#     # Create new user
#     user = User(
#         email=email,
#         name=f"{group_name} Admin",
#         phone=None,
#         district_id=district_id
#     )
#     user.set_password("12345678")  # Default password
    
#     # Assign Group Admin role
#     group_admin_role = Role.query.filter_by(name="Group Admin").first()
#     if group_admin_role:
#         user.roles.append(group_admin_role)
#         print(f"✅ Assigned Group Admin role to {email}")
#     else:
#         print(f"⚠️  Warning: Group Admin role not found!")
    
#     db.session.add(user)
#     db.session.commit()
    
#     print(f"👤 CREATED User: {email} for group '{group_name}'")
#     return user

# def import_hierarchy_from_excel(file_path, state_name, state_code="RIV-CEN"):
#     """
#     Enhanced version that creates users for both new AND existing groups
#     """
#     print("=== Starting hierarchy import ===")
    
#     try:
#         # Read Excel file
#         df = pd.read_excel(file_path, sheet_name=0, header=None)
#         print(f"Loaded Excel with {len(df)} rows, {len(df.columns)} columns")
        
#         # Create state
#         state = State.query.filter_by(name=state_name).first()
#         if not state:
#             state = State(name=state_name, code=state_code)
#             db.session.add(state)
#             db.session.commit()
#             print(f"Created state: {state_name} (ID: {state.id})")
        
#         current_old_group = None
#         old_groups_created = 0
#         groups_created = 0
#         districts_created = 0
#         users_created = 0
        
#         # Track groups we process to avoid duplicates
#         processed_groups = set()
        
#         for index, row in df.iterrows():
#             # Convert all cells to strings for safe processing
#             row_str = [safe_strip(cell) for cell in row]
            
#             # Skip completely empty rows
#             if all(cell == '' for cell in row_str):
#                 continue
            
#             # DEBUG: Show rows that might contain Old Groups
#             if any("OLD GROUP" in cell.upper() for cell in row_str if cell):
#                 print(f"Row {index} MAY CONTAIN OLD GROUP: {[cell for cell in row_str if cell]}")
            
#             # DETECT OLD GROUP - Check ALL columns for "OLD GROUP"
#             for col_idx, cell_value in enumerate(row_str):
#                 if cell_value and "OLD GROUP" in cell_value.upper():
#                     old_group_name = cell_value
#                     print(f"🎯 FOUND OLD GROUP: '{old_group_name}' in column {col_idx}")
                    
#                     # Find or create the Old Group
#                     current_old_group = OldGroup.query.filter_by(
#                         name=old_group_name, state_id=state.id
#                     ).first()
#                     if not current_old_group:
#                         current_old_group = OldGroup(
#                             name=old_group_name,
#                             code=old_group_name.replace("OLD GROUP", "").strip()[:4].upper(),
#                             state_id=state.id,
#                             region_id=1
#                         )
#                         db.session.add(current_old_group)
#                         db.session.commit()
#                         old_groups_created += 1
#                         print(f"✅ CREATED OldGroup: {old_group_name} (ID: {current_old_group.id})")
#                     else:
#                         print(f"📁 USING existing OldGroup: {old_group_name} (ID: {current_old_group.id})")
                    
#                     break
            
#             # Only process groups and districts if we have a current Old Group
#             if current_old_group:
#                 # Look for group names in this row (they typically appear after Old Group rows)
#                 for col_idx in range(len(row_str)):
#                     group_name = row_str[col_idx]
                    
#                     # Skip empty cells, numbers, and Old Group indicators
#                     if (not group_name or
#                         group_name.isdigit() or
#                         "OLD GROUP" in group_name.upper()):
#                         continue
                    
#                     # Check if this looks like a group name
#                     # Groups are typically multi-word and don't contain numbers
#                     if (len(group_name.split()) >= 2 or
#                         any(word in group_name.upper() for word in ['GROUP', 'DISTRICT', 'UNIPORT', 'CORPER', 'FELLOWSHIP'])):
                        
#                         # Skip if we've already processed this group in this run
#                         group_key = f"{group_name}_{current_old_group.id}"
#                         if group_key in processed_groups:
#                             continue
#                         processed_groups.add(group_key)
                        
#                         print(f"🎯 FOUND GROUP '{group_name}' under OldGroup '{current_old_group.name}'")
                        
#                         # Find or create the Group
#                         group = Group.query.filter_by(
#                             name=group_name, old_group_id=current_old_group.id
#                         ).first()
                        
#                         is_new_group = False
#                         if not group:
#                             group = Group(
#                                 name=group_name,
#                                 code=group_name[:4].upper(),
#                                 state_id=state.id,
#                                 region_id=1,
#                                 old_group_id=current_old_group.id
#                             )
#                             db.session.add(group)
#                             db.session.commit()
#                             groups_created += 1
#                             is_new_group = True
#                             print(f"✅ CREATED Group: {group_name} (ID: {group.id}) under {current_old_group.name}")
#                         else:
#                             print(f"📁 USING existing Group: {group_name} (ID: {group.id})")
                        
#                         # 🆕 CREATE USER FOR THIS GROUP (whether new or existing)
#                         group_user = create_group_user(group_name, group.id)
#                         if group_user:
#                             users_created += 1
                        
#                         # Process districts under this group (only for new groups to avoid duplicates)
#                         if is_new_group:
#                             district_start_row = index + 1
#                             for dist_row_idx in range(district_start_row, min(district_start_row + 20, len(df))):
#                                 district_name = safe_strip(df.iloc[dist_row_idx, col_idx])
                                
#                                 # Stop when we hit another group, Old Group, or empty row
#                                 if (not district_name or
#                                     district_name.isdigit() or
#                                     any(word in district_name.upper() for word in ['GROUP', 'OLD GROUP']) or
#                                     dist_row_idx >= len(df)):
#                                     break
                                
#                                 # Get district code from column 0 of the same row
#                                 district_code = safe_strip(df.iloc[dist_row_idx, 0])
#                                 if not district_code or district_code.isdigit():
#                                     district_code = district_name[:4].upper()
                                
#                                 # Only create district if it's a valid name (not numbers, not group-like)
#                                 if (district_name and
#                                     not district_name.isdigit() and
#                                     "GROUP" not in district_name.upper()):
                                    
#                                     print(f" 🎯 FOUND DISTRICT: {district_name} (Code: {district_code})")
                                    
#                                     # Check if district already exists
#                                     existing = District.query.filter_by(
#                                         name=district_name,
#                                         group_id=group.id,
#                                         old_group_id=current_old_group.id,
#                                         state_id=state.id
#                                     ).first()
                                    
#                                     if not existing:
#                                         district = District(
#                                             name=district_name,
#                                             code=district_code,
#                                             state_id=state.id,
#                                             region_id=1,
#                                             old_group_id=current_old_group.id,
#                                             group_id=group.id
#                                         )
#                                         db.session.add(district)
#                                         districts_created += 1
#                                         print(f" ✅ CREATED District: {district_name} under {group.name}")
        
#         db.session.commit()
        
#         print(f"\n=== IMPORT SUMMARY ===")
#         print(f"Old Groups created: {old_groups_created}")
#         print(f"Groups created: {groups_created}")
#         print(f"Districts created: {districts_created}")
#         print(f"Users created: {users_created}")
#         print("=== Import completed successfully! ===")
        
#         return {
#             "message": "Hierarchy imported successfully!",
#             "summary": {
#                 "old_groups": old_groups_created,
#                 "groups": groups_created,
#                 "districts": districts_created,
#                 "users": users_created
#             }
#         }
        
#     except Exception as e:
#         db.session.rollback()
#         print(f"❌ IMPORT FAILED: {str(e)}")
#         import traceback
#         print(f"Traceback: {traceback.format_exc()}")
#         raise e















# # app/utils/excel_importer.py
# import pandas as pd
# from app.extensions import db
# from app.models import State, OldGroup, Group, District, User, Role

# def safe_strip(value):
#     """Safely strip any value - converts to string first"""
#     if value is None or pd.isna(value):
#         return ""
#     return str(value).strip()

# def create_group_user(group_name, group_id, district_id=None):
#     """
#     Create a user for a group with default password
#     Username/email format: groupname@thedcmp.org (lowercase, no spaces)
#     """
#     # Clean group name for email
#     clean_name = group_name.lower().replace(' ', '_').replace("'", "").replace("-", "_")
#     email = f"{clean_name}@thedcmp.org"
    
#     # Check if user already exists
#     existing_user = User.query.filter_by(email=email).first()
#     if existing_user:
#         print(f"📧 User already exists: {email}")
#         return existing_user
    
#     # Create new user
#     user = User(
#         email=email,
#         name=f"{group_name} Admin",
#         phone=None,
#         district_id=district_id
#     )
#     user.set_password("12345678")  # Default password
    
#     # Assign Group Admin role
#     group_admin_role = Role.query.filter_by(name="Group Admin").first()
#     if group_admin_role:
#         user.roles.append(group_admin_role)
#         print(f"✅ Assigned Group Admin role to {email}")
#     else:
#         print(f"⚠️  Warning: Group Admin role not found!")
    
#     db.session.add(user)
    
#     print(f"👤 CREATED User: {email} for group '{group_name}'")
#     return user

# def import_hierarchy_from_excel(file_path, state_name, state_code="RIV-CEN"):
#     """
#     Fixed: Properly handles multiple Old Groups and assigns groups to correct Old Groups
#     Now also creates users for each group with default passwords
#     """
#     print("=== Starting hierarchy import ===")

#     # Optional: Uncomment to clear existing data for this state
#     # print("🧹 Clearing existing hierarchy data...")
#     # Group.query.filter(Group.state_id == state.id).delete()
#     # OldGroup.query.filter(OldGroup.state_id == state.id).delete()
#     # District.query.filter(District.state_id == state.id).delete()
#     # # Don't delete users as they might be used elsewhere
#     # db.session.commit()
    
#     try:
#         # Read Excel file
#         df = pd.read_excel(file_path, sheet_name=0, header=None)
#         print(f"Loaded Excel with {len(df)} rows, {len(df.columns)} columns")
        
#         # Create state
#         state = State.query.filter_by(name=state_name).first()
#         if not state:
#             state = State(name=state_name, code=state_code)
#             db.session.add(state)
#             db.session.commit()
#             print(f"Created state: {state_name} (ID: {state.id})")
        
#         current_old_group = None
#         old_groups_created = 0
#         groups_created = 0
#         districts_created = 0
#         users_created = 0
        
#         for index, row in df.iterrows():
#             # Convert all cells to strings for safe processing
#             row_str = [safe_strip(cell) for cell in row]
            
#             # Skip completely empty rows
#             if all(cell == '' for cell in row_str):
#                 continue
            
#             # DEBUG: Show rows that might contain Old Groups
#             if any("OLD GROUP" in cell.upper() for cell in row_str if cell):
#                 print(f"Row {index} MAY CONTAIN OLD GROUP: {[cell for cell in row_str if cell]}")
            
#             # DETECT OLD GROUP - Check ALL columns for "OLD GROUP"
#             for col_idx, cell_value in enumerate(row_str):
#                 if cell_value and "OLD GROUP" in cell_value.upper():
#                     old_group_name = cell_value
#                     print(f"🎯 FOUND OLD GROUP: '{old_group_name}' in column {col_idx}")
                    
#                     # Find or create the Old Group
#                     current_old_group = OldGroup.query.filter_by(
#                         name=old_group_name, state_id=state.id
#                     ).first()
#                     if not current_old_group:
#                         current_old_group = OldGroup(
#                             name=old_group_name,
#                             code=old_group_name.replace("OLD GROUP", "").strip()[:4].upper(),
#                             state_id=state.id,
#                             region_id=1
#                         )
#                         db.session.add(current_old_group)
#                         db.session.commit()
#                         old_groups_created += 1
#                         print(f"✅ CREATED OldGroup: {old_group_name} (ID: {current_old_group.id})")
#                     else:
#                         print(f"📁 USING existing OldGroup: {old_group_name} (ID: {current_old_group.id})")
                    
#                     # Once we find an Old Group, break and move to next row
#                     break
            
#             # Only process groups and districts if we have a current Old Group
#             if current_old_group:
#                 # Look for group names in this row (they typically appear after Old Group rows)
#                 for col_idx in range(len(row_str)):
#                     group_name = row_str[col_idx]
                    
#                     # Skip empty cells, numbers, and Old Group indicators
#                     if (not group_name or
#                         group_name.isdigit() or
#                         "OLD GROUP" in group_name.upper()):
#                         continue
                    
#                     # Check if this looks like a group name
#                     # Groups are typically multi-word and don't contain numbers
#                     if (len(group_name.split()) >= 2 or
#                         any(word in group_name.upper() for word in ['GROUP', 'DISTRICT', 'UNIPORT', 'CORPER', 'FELLOWSHIP'])):
                        
#                         print(f"🎯 FOUND GROUP '{group_name}' under OldGroup '{current_old_group.name}'")
                        
#                         # Find or create the Group
#                         group = Group.query.filter_by(
#                             name=group_name, old_group_id=current_old_group.id
#                         ).first()
#                         if not group:
#                             group = Group(
#                                 name=group_name,
#                                 code=group_name[:4].upper(),
#                                 state_id=state.id,
#                                 region_id=1,
#                                 old_group_id=current_old_group.id
#                             )
#                             db.session.add(group)
#                             db.session.commit()
#                             groups_created += 1
#                             print(f"✅ CREATED Group: {group_name} (ID: {group.id}) under {current_old_group.name}")
                            
#                             # 🆕 CREATE USER FOR THIS GROUP
#                             group_user = create_group_user(group_name, group.id)
#                             if group_user:
#                                 users_created += 1
                            
#                             # Now process districts under this group
#                             # Districts are in the same column but in subsequent rows
#                             district_start_row = index + 1
#                             for dist_row_idx in range(district_start_row, min(district_start_row + 20, len(df))):
#                                 district_name = safe_strip(df.iloc[dist_row_idx, col_idx])
                                
#                                 # Stop when we hit another group, Old Group, or empty row
#                                 if (not district_name or
#                                     district_name.isdigit() or
#                                     any(word in district_name.upper() for word in ['GROUP', 'OLD GROUP']) or
#                                     dist_row_idx >= len(df)):
#                                     break
                                
#                                 # Get district code from column 0 of the same row
#                                 district_code = safe_strip(df.iloc[dist_row_idx, 0])
#                                 if not district_code or district_code.isdigit():
#                                     district_code = district_name[:4].upper()
                                
#                                 # Only create district if it's a valid name (not numbers, not group-like)
#                                 if (district_name and
#                                     not district_name.isdigit() and
#                                     "GROUP" not in district_name.upper()):
                                    
#                                     print(f" 🎯 FOUND DISTRICT: {district_name} (Code: {district_code})")
                                    
#                                     # Check if district already exists
#                                     existing = District.query.filter_by(
#                                         name=district_name,
#                                         group_id=group.id,
#                                         old_group_id=current_old_group.id,
#                                         state_id=state.id
#                                     ).first()
                                    
#                                     if not existing:
#                                         district = District(
#                                             name=district_name,
#                                             code=district_code,
#                                             state_id=state.id,
#                                             region_id=1,
#                                             old_group_id=current_old_group.id,
#                                             group_id=group.id
#                                         )
#                                         db.session.add(district)
#                                         db.session.commit()  # Commit to get district ID
#                                         districts_created += 1
#                                         print(f" ✅ CREATED District: {district_name} under {group.name}")
                                        
#                                         # 🆕 CREATE USER FOR THIS DISTRICT (Optional)
#                                         # Uncomment if you want district-level users too
#                                         # district_user = create_group_user(
#                                         #     f"{district_name} District", 
#                                         #     group.id, 
#                                         #     district.id
#                                         # )
#                                         # if district_user:
#                                         #     users_created += 1
        
#         db.session.commit()
        
#         print(f"\n=== IMPORT SUMMARY ===")
#         print(f"Old Groups created: {old_groups_created}")
#         print(f"Groups created: {groups_created}")
#         print(f"Districts created: {districts_created}")
#         print(f"Users created: {users_created}")
#         print("=== Import completed successfully! ===")
        
#         return {
#             "message": "Hierarchy imported successfully!",
#             "summary": {
#                 "old_groups": old_groups_created,
#                 "groups": groups_created,
#                 "districts": districts_created,
#                 "users": users_created
#             }
#         }
        
#     except Exception as e:
#         db.session.rollback()
#         print(f"❌ IMPORT FAILED: {str(e)}")
#         import traceback
#         print(f"Traceback: {traceback.format_exc()}")
#         raise e













# # app/utils/excel_importer.py
# import pandas as pd
# from app.extensions import db
# from app.models import State, OldGroup, Group, District

# def safe_strip(value):
#     """Safely strip any value - converts to string first"""
#     if value is None or pd.isna(value):
#         return ""
#     return str(value).strip()

# def import_hierarchy_from_excel(file_path, state_name, state_code="RIV-CEN"):
#     """
#     Fixed: Properly handles multiple Old Groups and assigns groups to correct Old Groups
#     """
#     print("=== Starting hierarchy import ===")
    
#     try:
#         # Read Excel file
#         df = pd.read_excel(file_path, sheet_name=0, header=None)
#         print(f"Loaded Excel with {len(df)} rows, {len(df.columns)} columns")
        
#         # Create state
#         state = State.query.filter_by(name=state_name).first()
#         if not state:
#             state = State(name=state_name, code=state_code)
#             db.session.add(state)
#             db.session.commit()
#             print(f"Created state: {state_name} (ID: {state.id})")

#         current_old_group = None
#         old_groups_created = 0
#         groups_created = 0
#         districts_created = 0

#         for index, row in df.iterrows():
#             # Convert all cells to strings for safe processing
#             row_str = [safe_strip(cell) for cell in row]
            
#             # Skip completely empty rows
#             if all(cell == '' for cell in row_str):
#                 continue

#             # DEBUG: Show rows that might contain Old Groups
#             if any("OLD GROUP" in cell.upper() for cell in row_str if cell):
#                 print(f"Row {index} MAY CONTAIN OLD GROUP: {[cell for cell in row_str if cell]}")
            
#             # DETECT OLD GROUP - Check ALL columns for "OLD GROUP"
#             for col_idx, cell_value in enumerate(row_str):
#                 if cell_value and "OLD GROUP" in cell_value.upper():
#                     old_group_name = cell_value
#                     print(f"🎯 FOUND OLD GROUP: '{old_group_name}' in column {col_idx}")
                    
#                     # Find or create the Old Group
#                     current_old_group = OldGroup.query.filter_by(
#                         name=old_group_name, state_id=state.id
#                     ).first()
#                     if not current_old_group:
#                         current_old_group = OldGroup(
#                             name=old_group_name,
#                             code=old_group_name.replace("OLD GROUP", "").strip()[:4].upper(),
#                             state_id=state.id,
#                             region_id=1
#                         )
#                         db.session.add(current_old_group)
#                         db.session.commit()
#                         old_groups_created += 1
#                         print(f"✅ CREATED OldGroup: {old_group_name} (ID: {current_old_group.id})")
#                     else:
#                         print(f"📁 USING existing OldGroup: {old_group_name} (ID: {current_old_group.id})")
                    
#                     # Once we find an Old Group, break and move to next row
#                     break

#             # Only process groups and districts if we have a current Old Group
#             if current_old_group:
#                 # Look for group names in this row (they typically appear after Old Group rows)
#                 for col_idx in range(len(row_str)):
#                     group_name = row_str[col_idx]
                    
#                     # Skip empty cells, numbers, and Old Group indicators
#                     if (not group_name or 
#                         group_name.isdigit() or 
#                         "OLD GROUP" in group_name.upper()):
#                         continue
                    
#                     # Check if this looks like a group name 
#                     # Groups are typically multi-word and don't contain numbers
#                     if (len(group_name.split()) >= 2 or 
#                         any(word in group_name.upper() for word in ['GROUP', 'DISTRICT', 'UNIPORT', 'CORPER', 'FELLOWSHIP'])):
                        
#                         print(f"🎯 FOUND GROUP '{group_name}' under OldGroup '{current_old_group.name}'")
                        
#                         # Find or create the Group
#                         group = Group.query.filter_by(
#                             name=group_name, old_group_id=current_old_group.id
#                         ).first()
#                         if not group:
#                             group = Group(
#                                 name=group_name,
#                                 code=group_name[:4].upper(),
#                                 state_id=state.id,
#                                 region_id=1,
#                                 old_group_id=current_old_group.id
#                             )
#                             db.session.add(group)
#                             db.session.commit()
#                             groups_created += 1
#                             print(f"✅ CREATED Group: {group_name} (ID: {group.id}) under {current_old_group.name}")
                            
#                             # Now process districts under this group
#                             # Districts are in the same column but in subsequent rows
#                             district_start_row = index + 1
#                             for dist_row_idx in range(district_start_row, min(district_start_row + 20, len(df))):
#                                 district_name = safe_strip(df.iloc[dist_row_idx, col_idx])
                                
#                                 # Stop when we hit another group, Old Group, or empty row
#                                 if (not district_name or 
#                                     district_name.isdigit() or
#                                     any(word in district_name.upper() for word in ['GROUP', 'OLD GROUP']) or
#                                     dist_row_idx >= len(df)):
#                                     break
                                
#                                 # Get district code from column 0 of the same row
#                                 district_code = safe_strip(df.iloc[dist_row_idx, 0])
#                                 if not district_code or district_code.isdigit():
#                                     district_code = district_name[:4].upper()
                                
#                                 # Only create district if it's a valid name (not numbers, not group-like)
#                                 if (district_name and 
#                                     not district_name.isdigit() and 
#                                     "GROUP" not in district_name.upper()):
                                    
#                                     print(f"  🎯 FOUND DISTRICT: {district_name} (Code: {district_code})")
                                    
#                                     # Check if district already exists
#                                     existing = District.query.filter_by(
#                                         name=district_name,
#                                         group_id=group.id,
#                                         old_group_id=current_old_group.id,
#                                         state_id=state.id
#                                     ).first()
                                    
#                                     if not existing:
#                                         district = District(
#                                             name=district_name,
#                                             code=district_code,
#                                             state_id=state.id,
#                                             region_id=1,
#                                             old_group_id=current_old_group.id,
#                                             group_id=group.id
#                                         )
#                                         db.session.add(district)
#                                         districts_created += 1
#                                         print(f"  ✅ CREATED District: {district_name} under {group.name}")

#         db.session.commit()
        
#         print(f"\n=== IMPORT SUMMARY ===")
#         print(f"Old Groups created: {old_groups_created}")
#         print(f"Groups created: {groups_created}") 
#         print(f"Districts created: {districts_created}")
#         print("=== Import completed successfully! ===")
        
#         return {
#             "message": "Hierarchy imported successfully!",
#             "summary": {
#                 "old_groups": old_groups_created,
#                 "groups": groups_created,
#                 "districts": districts_created
#             }
#         }
        
#     except Exception as e:
#         db.session.rollback()
#         print(f"❌ IMPORT FAILED: {str(e)}")
#         import traceback
#         print(f"Traceback: {traceback.format_exc()}")
#         raise e
