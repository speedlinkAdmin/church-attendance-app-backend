# app/utils/excel_importer_enhanced.py
from datetime import datetime 
# from datetime import now
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
    Create a user for a group with COMPLETE hierarchy links
    Username/email format: groupname.group (lowercase, no spaces, with .group suffix)
    Handles cases where 'group' is already in the name
    """
    # Clean group name for email
    clean_name = group_name.lower().replace(' ', '').replace("'", "").replace("-", "")
    
    # 🎯 REMOVE "group" suffix if already present to avoid duplication
    if clean_name.endswith('_group'):
        clean_name = clean_name[:-6]  # Remove "_group"
    elif clean_name.endswith('group'):
        clean_name = clean_name[:-5]  # Remove "group"
    
    # 🎯 ADD .group suffix (no domain)
    email = f"{clean_name}.group"
    
    print(f"🔄 Creating user with email: '{email}' for group '{group_name}'")
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        print(f"📧 User already exists, updating: {email}")
        user = existing_user
    else:
        print(f"👤 CREATING NEW User: {email} for group '{group_name}'")
        user = User(
            email=email,
            name=f"{group_name} Admin",
            phone=None
        )
        user.set_password("12345678")  # Default password
    
    # 🎯 SET COMPLETE HIERARCHY LINKS - CRITICAL FOR ACCESS CONTROL
    user.state_id = group.state_id
    user.region_id = group.region_id
    user.old_group_id = group.old_group_id  # 🎯 Link to old group
    user.group_id = group.id  # 🎯 Link to the group
    
    # For group admin, district_id should be NULL to access ALL districts in the group
    user.district_id = None  # 🎯 This gives access to all districts in the group
    
    print(f"🔗 Setting hierarchy for {email}: State={group.state_id}, Region={group.region_id}, OldGroup={group.old_group_id}, Group={group.id}")
    
    # Assign Group Admin role
    group_admin_role = Role.query.filter_by(name="Group Admin").first()
    if group_admin_role:
        if group_admin_role not in user.roles:
            user.roles.append(group_admin_role)
            print(f"✅ Assigned Group Admin role to {email}")
    else:
        print(f"⚠️  Warning: Group Admin role not found!")
        # Create the role if it doesn't exist
        group_admin_role = Role(name="Group Admin", description="Administrator for a specific group")
        db.session.add(group_admin_role)
        db.session.commit()
        user.roles.append(group_admin_role)
        print(f"✅ Created and assigned Group Admin role to {email}")
    
    if not existing_user:
        db.session.add(user)
    
    # Commit immediately to ensure user is saved with proper hierarchy
    db.session.commit()
    
    print(f"🔗 FINAL User {email} linked to - State: {user.state_id}, Region: {user.region_id}, " 
          f"District: {user.district_id}, Group: {user.group_id}, OldGroup: {user.old_group_id}")
    return user





# def import_hierarchy_from_excel(file_path, state_name="Rivers Central", state_code="RIV-CEN", region_name="Port Harcourt", simulate=True):
#     print("=== Starting ENHANCED hierarchy import ===")
#     print(f"🎯 Mode: {'SIMULATION (dry-run)' if simulate else 'REAL IMPORT'}")
    
#     df = pd.read_excel(file_path, sheet_name=0, header=None)
#     # df = pd.read_csv(file_path, header=None)

#     print(f"Loaded Excel: {df.shape[0]} rows, {df.shape[1]} columns")
    
#     # State & Region setup (fake in sim)
#     if not simulate:
#         state = State.query.filter_by(name=state_name).first() or State(name=state_name, code=state_code, leader="State Leader")
#         db.session.add(state) if state.id is None else None
#         db.session.commit()
        
#         region = Region.query.filter_by(name=region_name, state_id=state.id).first() or \
#                  Region(name=region_name, code="PH-RGN", leader="Region Leader", state_id=state.id)
#         db.session.add(region) if region.id is None else None
#         db.session.commit()
#     else:
#         state = type('FakeState', (), {'id': 999})()
#         region = type('FakeRegion', (), {'id': 888})()
#         print("[SIM] Fake IDs used")
    
#     old_groups_count = groups_count = districts_count = users_count = 0
#     i = 0
    
#     while i < len(df):
#         row_upper = df.iloc[i].astype(str).str.upper().str.strip()
        
#         if row_upper.str.contains('OLD GROUP').any():
#             old_group_col = row_upper[row_upper.str.contains('OLD GROUP')].index[0]
#             old_group_name = safe_strip(df.iloc[i, old_group_col])
#             print(f"\n🎯 FOUND OLD GROUP: '{old_group_name}' (row {i})")
#             old_groups_count += 1
            
#             if not simulate:
#                 og = OldGroup(name=old_group_name, code=old_group_name.replace("OLD GROUP", "").strip()[:6].upper() or "OLDGRP",
#                               state_id=state.id, region_id=region.id)
#                 db.session.add(og)
#                 db.session.commit()
#                 og_id = og.id
#             else:
#                 og_id = 9999
            
#             i += 1  # Move to group row
#             if i >= len(df): break
            
#             group_row = df.iloc[i]
#             group_names, group_columns = [], []
            
#             for col in range(df.shape[1]):
#                 name = safe_strip(group_row[col])
#                 if name and not name.isdigit() and 'OLD GROUP' not in name.upper():
#                     group_names.append(name)
#                     group_columns.append(col)
#                     print(f"  → Detected group: '{name}' (col {col})")
            
#             if not group_names:
#                 print("  ⚠️ No groups found! Skipping...")
#                 i += 1
#                 continue
            
#             groups_count += len(group_names)
#             group_objects = {}
            
#             for idx, g_name in enumerate(group_names):
#                 col = group_columns[idx]
#                 if not simulate:
#                     group = Group(name=g_name, code=g_name[:6].upper() or "GRP",
#                                   state_id=state.id, region_id=region.id, old_group_id=og_id,
#                                   leader=f"{g_name} Leader")
#                     db.session.add(group)
#                     db.session.commit()
#                     group_objects[col] = group
#                     create_group_user(g_name, group)  # creates user & commits
#                     users_count += 1
#                 else:
#                     print(f"  [SIM] Would create group '{g_name}' + user")
#                     users_count += 1
            
#             # District collection
#             i += 1
#             districts_this_section = 0
#             consec_empty = 0
            
#             while i < len(df):
#                 dist_row = df.iloc[i]
#                 dist_str = [safe_strip(c) for c in dist_row]
#                 dist_upper = [s.upper() for s in dist_str]
                
#                 # Stop conditions
#                 if any('OLD GROUP' in s for s in dist_upper):
#                     print(f"  → End of section at row {i} (next OLD GROUP)")
#                     i -= 1
#                     break
                
#                 filled = sum(1 for x in dist_str if x)
#                 has_num = any(c.isdigit() for c in dist_str if c)
                
#                 if filled > 8 and not has_num:
#                     print(f"  → End of section at row {i} (new group-like row)")
#                     i -= 1
#                     break
                
#                 if all(x == '' for x in dist_str):
#                     consec_empty += 1
#                     if consec_empty >= 3:
#                         print(f"  → End of section at row {i} (multiple empties)")
#                         break
#                     i += 1
#                     continue
#                 consec_empty = 0
                
#                 # Extract districts using strict alignment
#                 for g_col in group_columns:
#                     code_col = g_col if g_col % 2 == 0 else g_col - 1
#                     name_col = code_col + 1
                    
#                     if name_col >= df.shape[1]: continue
                    
#                     code = safe_strip(dist_row[code_col])
#                     name = safe_strip(dist_row[name_col])
                    
#                     if code.isdigit() and name and len(name) > 2:
#                         districts_this_section += 1
#                         districts_count += 1
#                         print(f"      + District {code}: '{name}' (group col {g_col})")
                        
#                         if not simulate:
#                             dist = District(name=name, code=code,
#                                             state_id=state.id, region_id=region.id,
#                                             old_group_id=og_id, group_id=group_objects[g_col].id,
#                                             leader=f"{name} Leader")
#                             db.session.add(dist)
#                             db.session.commit()
                
#                 i += 1
            
#             print(f"  → Found {districts_this_section} districts in this section")
#             continue
        
#         i += 1
    
#     if not simulate:
#         db.session.commit()
    
#     print("\n" + "="*60)
#     print(f"FINAL SUMMARY:")
#     print(f"Old Groups : {old_groups_count}")
#     print(f"Groups     : {groups_count}")
#     print(f"Districts  : {districts_count}")
#     print(f"Users      : {users_count}")
#     print("="*60)
    
#     return {
#         "old_groups": old_groups_count,
#         "groups": groups_count,
#         "districts": districts_count,
#         "users": users_count,
#         "status": "dry-run successful" if simulate else "import completed"
#     }



def import_hierarchy_from_excel(file_path, state_name="Rivers Central", state_code="RIV-CEN", region_name="Port Harcourt", simulate=False, import_districts=False):
    """
    Import only Old Groups and Groups from Excel/CSV
    Set import_districts=False to skip district import
    """
    print("=== Starting GROUPS-ONLY hierarchy import ===")
    print(f"🎯 Mode: {'SIMULATION (dry-run)' if simulate else 'REAL IMPORT'}")
    print(f"📋 Import Districts: {'YES' if import_districts else 'NO (groups only)'}")
    
    # Try to read as Excel first, then CSV
    try:
        df = pd.read_excel(file_path, sheet_name=0, header=None)
        print(f"Loaded Excel: {df.shape[0]} rows, {df.shape[1]} columns")
    except:
        try:
            df = pd.read_csv(file_path, header=None, encoding='latin-1')
            print(f"Loaded CSV: {df.shape[0]} rows, {df.shape[1]} columns")
        except Exception as e:
            print(f"Error reading file: {e}")
            return {"error": f"Could not read file: {e}"}
    
    # State & Region setup
    if not simulate:
        state = State.query.filter_by(name=state_name).first() or State(name=state_name, code=state_code, leader="State Leader")
        db.session.add(state) if state.id is None else None
        db.session.commit()
        
        region = Region.query.filter_by(name=region_name, state_id=state.id).first() or \
                 Region(name=region_name, code="PH-RGN", leader="Region Leader", state_id=state.id)
        db.session.add(region) if region.id is None else None
        db.session.commit()
    else:
        state = type('FakeState', (), {'id': 999})()
        region = type('FakeRegion', (), {'id': 888})()
        print("[SIM] Fake IDs used")
    
    old_groups_count = groups_count = districts_count = users_count = 0
    i = 0
    
    # Store group mapping for export
    group_mapping = []  # List of dicts with group info
    
    while i < len(df):
        row_upper = df.iloc[i].astype(str).str.upper().str.strip()
        
        if row_upper.str.contains('OLD GROUP').any():
            old_group_col = row_upper[row_upper.str.contains('OLD GROUP')].index[0]
            old_group_name = safe_strip(df.iloc[i, old_group_col])
            print(f"\n🎯 FOUND OLD GROUP: '{old_group_name}' (row {i})")
            old_groups_count += 1
            
            if not simulate:
                og = OldGroup(name=old_group_name, code=old_group_name.replace("OLD GROUP", "").strip()[:6].upper() or "OLDGRP",
                              state_id=state.id, region_id=region.id)
                db.session.add(og)
                db.session.commit()
                og_id = og.id
                og_code = og.code
            else:
                og_id = 9999
                og_code = old_group_name.replace("OLD GROUP", "").strip()[:6].upper() or "OLDGRP"
            
            i += 1  # Move to group row
            if i >= len(df): break
            
            group_row = df.iloc[i]
            group_names, group_columns = [], []
            
            for col in range(df.shape[1]):
                name = safe_strip(group_row[col])
                if name and not name.isdigit() and 'OLD GROUP' not in name.upper():
                    group_names.append(name)
                    group_columns.append(col)
                    print(f"  → Detected group: '{name}' (col {col})")
            
            if not group_names:
                print("  ⚠️ No groups found! Skipping...")
                i += 1
                continue
            
            groups_count += len(group_names)
            group_objects = {}
            
            for idx, g_name in enumerate(group_names):
                col = group_columns[idx]
                if not simulate:
                    group = Group(name=g_name, code=g_name[:6].upper() or "GRP",
                                  state_id=state.id, region_id=region.id, old_group_id=og_id,
                                  leader=f"{g_name} Leader")
                    db.session.add(group)
                    db.session.commit()
                    group_objects[col] = group
                    
                    # Store mapping for export
                    group_mapping.append({
                        'old_group_name': old_group_name,
                        'old_group_code': og_code,
                        'group_name': g_name,
                        'group_code': group.code,
                        'group_id': group.id,
                        'group_col': col,
                        'old_group_id': og_id
                    })
                    
                    create_group_user(g_name, group)  # creates user & commits
                    users_count += 1
                else:
                    print(f"  [SIM] Would create group '{g_name}' + user")
                    group_mapping.append({
                        'old_group_name': old_group_name,
                        'old_group_code': og_code,
                        'group_name': g_name,
                        'group_code': g_name[:6].upper() or "GRP",
                        'group_id': f"SIM_{len(group_mapping)}",
                        'group_col': col,
                        'old_group_id': og_id
                    })
                    users_count += 1
            
            # SKIP DISTRICT IMPORT if import_districts is False
            if not import_districts:
                print(f"  ⏭️  Skipping districts for '{old_group_name}' (import_districts=False)")
                # Skip to next OLD GROUP
                i += 1
                while i < len(df):
                    row_str = ' '.join([str(df.iloc[i, c]) for c in range(df.shape[1]) if df.iloc[i, c]])
                    if 'OLD GROUP' in row_str.upper():
                        i -= 1
                        break
                    i += 1
                continue
            
            # Original district import logic (only if import_districts=True)
            i += 1
            districts_this_section = 0
            consec_empty = 0
            
            while i < len(df):
                dist_row = df.iloc[i]
                dist_str = [safe_strip(c) for c in dist_row]
                dist_upper = [s.upper() for s in dist_str]
                
                # Stop conditions
                if any('OLD GROUP' in s for s in dist_upper):
                    print(f"  → End of section at row {i} (next OLD GROUP)")
                    i -= 1
                    break
                
                filled = sum(1 for x in dist_str if x)
                has_num = any(c.isdigit() for c in dist_str if c)
                
                if filled > 8 and not has_num:
                    print(f"  → End of section at row {i} (new group-like row)")
                    i -= 1
                    break
                
                if all(x == '' for x in dist_str):
                    consec_empty += 1
                    if consec_empty >= 3:
                        print(f"  → End of section at row {i} (multiple empties)")
                        break
                    i += 1
                    continue
                consec_empty = 0
                
                # Extract districts using strict alignment
                for g_col in group_columns:
                    code_col = g_col if g_col % 2 == 0 else g_col - 1
                    name_col = code_col + 1
                    
                    if name_col >= df.shape[1]: continue
                    
                    code = safe_strip(dist_row[code_col])
                    name = safe_strip(dist_row[name_col])
                    
                    if code.isdigit() and name and len(name) > 2:
                        districts_this_section += 1
                        districts_count += 1
                        print(f"      + District {code}: '{name}' (group col {g_col})")
                        
                        if not simulate:
                            dist = District(name=name, code=code,
                                            state_id=state.id, region_id=region.id,
                                            old_group_id=og_id, group_id=group_objects[g_col].id,
                                            leader=f"{name} Leader")
                            db.session.add(dist)
                            db.session.commit()
                
                i += 1
            
            if import_districts:
                print(f"  → Found {districts_this_section} districts in this section")
            continue
        
        i += 1
    
    if not simulate:
        db.session.commit()
    
    # Create export file with group mappings
    if not simulate and group_mapping:
        export_filename = f"group_mappings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        export_df = pd.DataFrame(group_mapping)
        export_df.to_csv(export_filename, index=False)
        print(f"\n📁 Group mappings exported to: {export_filename}")
        print(f"   Total groups mapped: {len(group_mapping)}")
    
    print("\n" + "="*60)
    print(f"FINAL SUMMARY:")
    print(f"Old Groups : {old_groups_count}")
    print(f"Groups     : {groups_count}")
    print(f"Districts  : {districts_count} {'(SKIPPED)' if not import_districts else ''}")
    print(f"Users      : {users_count}")
    print("="*60)
    
    # Show expected vs actual
    if groups_count != 111:
        print(f"⚠️  WARNING: Expected 111 groups, got {groups_count}")
    
    return {
        "old_groups": old_groups_count,
        "groups": groups_count,
        "districts": districts_count,
        "users": users_count,
        "group_mappings": group_mapping if simulate else export_filename,
        "status": "dry-run successful" if simulate else "import completed"
    }


def export_group_mappings_for_district_import():
    """
    Export all groups with their IDs for later district mapping
    Run this AFTER importing groups successfully
    """
    print("=== Exporting Group Mappings for District Import ===")
    
    groups = Group.query.all()
    export_data = []
    
    for group in groups:
        old_group = OldGroup.query.get(group.old_group_id)
        export_data.append({
            'group_id': group.id,
            'group_name': group.name,
            'group_code': group.code,
            'old_group_id': group.old_group_id,
            'old_group_name': old_group.name if old_group else '',
            'state_id': group.state_id,
            'region_id': group.region_id
        })
    
    if export_data:
        export_df = pd.DataFrame(export_data)
        filename = f"group_mappings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        export_df.to_csv(filename, index=False)
        print(f"✅ Exported {len(export_data)} groups to: {filename}")
        return filename
    else:
        print("⚠️  No groups found to export")
        return None


def import_districts_from_mapping(districts_file, groups_mapping_file):
    """
    Import districts using pre-defined group mappings
    districts_file: CSV with districts (group_name, district_number, district_name)
    groups_mapping_file: CSV with group mappings from previous export
    """
    print("=== Importing Districts with Group Mappings ===")
    
    # Load district data
    districts_df = pd.read_csv(districts_file)
    groups_df = pd.read_csv(groups_mapping_file)
    
    print(f"Loaded {len(districts_df)} districts to import")
    print(f"Loaded {len(groups_df)} group mappings")
    
    district_count = 0
    
    for _, district_row in districts_df.iterrows():
        group_name = district_row['group_name']
        district_num = district_row['district_number']
        district_name = district_row['district_name']
        
        # Find matching group
        group_match = groups_df[groups_df['group_name'] == group_name]
        
        if len(group_match) == 0:
            print(f"⚠️  No group found for district '{district_name}' (group: {group_name})")
            continue
        
        group_info = group_match.iloc[0]
        
        # Create district
        district = District(
            name=district_name,
            code=str(district_num),
            state_id=group_info['state_id'],
            region_id=group_info['region_id'],
            old_group_id=group_info['old_group_id'],
            group_id=group_info['group_id'],
            leader=f"{district_name} Leader"
        )
        
        db.session.add(district)
        district_count += 1
        
        if district_count % 50 == 0:
            db.session.commit()
            print(f"  → Committed {district_count} districts so far...")
    
    db.session.commit()
    print(f"\n✅ Imported {district_count} districts successfully")
    return district_count













# # app/utils/excel_importer_enhanced.py
# import pandas as pd
# from app.extensions import db
# from app.models import State, Region, OldGroup, Group, District, User, Role

# def safe_strip(value):
#     """Safely strip any value - converts to string first"""
#     if value is None or pd.isna(value):
#         return ""
#     return str(value).strip()

# def create_group_user(group_name, group, district=None):
#     """
#     Create a user for a group with COMPLETE hierarchy links
#     Username/email format: groupname.group (lowercase, no spaces, with .group suffix)
#     Handles cases where 'group' is already in the name
#     """
#     # Clean group name for email
#     clean_name = group_name.lower().replace(' ', '').replace("'", "").replace("-", "")
    
#     # 🎯 REMOVE "group" suffix if already present to avoid duplication
#     if clean_name.endswith('_group'):
#         clean_name = clean_name[:-6]  # Remove "_group"
#     elif clean_name.endswith('group'):
#         clean_name = clean_name[:-5]  # Remove "group"
    
#     # 🎯 ADD .group suffix (no domain)
#     email = f"{clean_name}.group"
    
#     print(f"🔄 Creating user with email: '{email}' for group '{group_name}'")
    
#     # Check if user already exists
#     existing_user = User.query.filter_by(email=email).first()
#     if existing_user:
#         print(f"📧 User already exists, updating: {email}")
#         user = existing_user
#     else:
#         print(f"👤 CREATING NEW User: {email} for group '{group_name}'")
#         user = User(
#             email=email,
#             name=f"{group_name} Admin",
#             phone=None
#         )
#         user.set_password("12345678")  # Default password
    
#     # 🎯 SET COMPLETE HIERARCHY LINKS - CRITICAL FOR ACCESS CONTROL
#     user.state_id = group.state_id
#     user.region_id = group.region_id
#     user.old_group_id = group.old_group_id  # 🎯 Link to old group
#     user.group_id = group.id  # 🎯 Link to the group
    
#     # For group admin, district_id should be NULL to access ALL districts in the group
#     user.district_id = None  # 🎯 This gives access to all districts in the group
    
#     print(f"🔗 Setting hierarchy for {email}: State={group.state_id}, Region={group.region_id}, OldGroup={group.old_group_id}, Group={group.id}")
    
#     # Assign Group Admin role
#     group_admin_role = Role.query.filter_by(name="Group Admin").first()
#     if group_admin_role:
#         if group_admin_role not in user.roles:
#             user.roles.append(group_admin_role)
#             print(f"✅ Assigned Group Admin role to {email}")
#     else:
#         print(f"⚠️  Warning: Group Admin role not found!")
#         # Create the role if it doesn't exist
#         group_admin_role = Role(name="Group Admin", description="Administrator for a specific group")
#         db.session.add(group_admin_role)
#         db.session.commit()
#         user.roles.append(group_admin_role)
#         print(f"✅ Created and assigned Group Admin role to {email}")
    
#     if not existing_user:
#         db.session.add(user)
    
#     # Commit immediately to ensure user is saved with proper hierarchy
#     db.session.commit()
    
#     print(f"🔗 FINAL User {email} linked to - State: {user.state_id}, Region: {user.region_id}, " 
#           f"District: {user.district_id}, Group: {user.group_id}, OldGroup: {user.old_group_id}")
#     return user

# def import_hierarchy_from_excel(file_path, state_name="Rivers Central", state_code="RIV-CEN", region_name="Port Harcourt"):
#     """
#     Enhanced version that properly links users to COMPLETE hierarchy
#     All data will be under Rivers Central state and Port Harcourt region
#     """
#     print("=== Starting ENHANCED hierarchy import ===")
#     print(f"🎯 Importing under State: {state_name}, Region: {region_name}")
    
#     try:
#         # Read Excel file
#         df = pd.read_excel(file_path, sheet_name=0, header=None)
#         print(f"Loaded Excel with {len(df)} rows, {len(df.columns)} columns")
        
#         # 🎯 CREATE OR GET STATE - Rivers Central
#         state = State.query.filter_by(name=state_name).first()
#         if not state:
#             state = State(name=state_name, code=state_code, leader="State Leader")
#             db.session.add(state)
#             db.session.commit()
#             print(f"✅ Created state: {state_name} (ID: {state.id})")
#         else:
#             print(f"📁 Using existing state: {state_name} (ID: {state.id})")
        
#         # 🎯 CREATE OR GET REGION - Port Harcourt Region
#         region = Region.query.filter_by(name=region_name, state_id=state.id).first()
#         if not region:
#             region = Region(
#                 name=region_name,
#                 code="PH-RGN",  # Port Harcourt Region code
#                 leader="Region Leader",
#                 state_id=state.id
#             )
#             db.session.add(region)
#             db.session.commit()
#             print(f"✅ Created region: {region_name} (ID: {region.id})")
#         else:
#             print(f"📁 Using existing region: {region_name} (ID: {region.id})")
        
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
            
#             # DETECT OLD GROUP - Check ALL columns for "OLD GROUP"
#             for col_idx, cell_value in enumerate(row_str):
#                 if cell_value and "OLD GROUP" in cell_value.upper():
#                     old_group_name = cell_value
#                     print(f"\n🎯 FOUND OLD GROUP: '{old_group_name}'")
                    
#                     # Create the Old Group under Rivers Central state and Port Harcourt region
#                     current_old_group = OldGroup(
#                         name=old_group_name,
#                         code=old_group_name.replace("OLD GROUP", "").strip()[:4].upper(),
#                         state_id=state.id,      # 🎯 Rivers Central
#                         region_id=region.id     # 🎯 Port Harcourt Region
#                     )
#                     db.session.add(current_old_group)
#                     db.session.commit()
#                     old_groups_created += 1
#                     print(f"✅ CREATED OldGroup: {old_group_name} (ID: {current_old_group.id}) under {state_name}/{region_name}")
#                     break
            
#             # Process groups and districts if we have a current Old Group
#             if current_old_group:
#                 for col_idx in range(len(row_str)):
#                     group_name = row_str[col_idx]
                    
#                     # Skip empty cells, numbers, and Old Group indicators
#                     if (not group_name or
#                         group_name.isdigit() or
#                         "OLD GROUP" in group_name.upper()):
#                         continue
                    
#                     # Check if this looks like a group name
#                     if (len(group_name.split()) >= 2 or
#                         any(word in group_name.upper() for word in ['GROUP', 'DISTRICT', 'UNIPORT', 'CORPER', 'FELLOWSHIP'])):
                        
#                         group_key = f"{group_name}_{current_old_group.id}"
#                         if group_key in processed_groups:
#                             continue
#                         processed_groups.add(group_key)
                        
#                         print(f"\n🎯 PROCESSING GROUP: '{group_name}' under '{current_old_group.name}'")
                        
#                         # Create the Group with COMPLETE hierarchy links
#                         group = Group(
#                             name=group_name,
#                             code=group_name[:4].upper(),
#                             state_id=state.id,          # 🎯 Rivers Central
#                             region_id=region.id,        # 🎯 Port Harcourt Region
#                             old_group_id=current_old_group.id,  # 🎯 Link to old group
#                             leader=f"{group_name} Leader"
#                         )
#                         db.session.add(group)
#                         db.session.commit()
#                         groups_created += 1
#                         print(f"✅ CREATED Group: {group_name} (ID: {group.id}) under {state_name}/{region_name}")
#                         print(f"📋 Group hierarchy: State={state.id}, Region={region.id}, OldGroup={current_old_group.id}")
                        
#                         # 🎯 CREATE USER FOR THIS GROUP with COMPLETE hierarchy links
#                         group_user = create_group_user(group_name, group)
#                         if group_user:
#                             users_created += 1
#                             print(f"✅ Created user {group_user.email} with Group ID: {group_user.group_id}, OldGroup ID: {group_user.old_group_id}")
                        
#                         # Process districts under this group
#                         district_start_row = index + 1
#                         district_count = 0
        
#                         for dist_row_idx in range(district_start_row, min(district_start_row + 30, len(df))):
#                             district_name = safe_strip(df.iloc[dist_row_idx, col_idx])
                            
#                             # Stop when we hit another group, Old Group, or empty row
#                             if (not district_name or
#                                 district_name.isdigit() or
#                                 any(word in district_name.upper() for word in ['GROUP', 'OLD GROUP']) or
#                                 dist_row_idx >= len(df)):
#                                 if district_count > 0:  # Only break if we found at least one district
#                                     break
#                                 else:
#                                     continue
                            
#                             # Get district code from column 0 of the same row
#                             district_code = safe_strip(df.iloc[dist_row_idx, 0])
#                             if not district_code or district_code.isdigit():
#                                 district_code = district_name[:4].upper()
                            
#                             # Only create district if it's a valid name
#                             if (district_name and
#                                 not district_name.isdigit() and
#                                 "GROUP" not in district_name.upper()):
                                
#                                 print(f"  🎯 FOUND DISTRICT: {district_name}")
                                
#                                 district = District(
#                                     name=district_name,
#                                     code=district_code,
#                                     state_id=state.id,          # 🎯 Rivers Central
#                                     region_id=region.id,        # 🎯 Port Harcourt Region
#                                     old_group_id=current_old_group.id,  # 🎯 Link to old group
#                                     group_id=group.id,          # 🎯 Link to parent group
#                                     leader=f"{district_name} Leader"
#                                 )
#                                 db.session.add(district)
#                                 db.session.commit()
#                                 districts_created += 1
#                                 district_count += 1
#                                 print(f"  ✅ CREATED District: {district_name} (ID: {district.id}) under {group.name}")
        
#         db.session.commit()
        
#         print(f"\n=== IMPORT SUMMARY ===")
#         print(f"✅ State: {state_name} (ID: {state.id})")
#         print(f"✅ Region: {region_name} (ID: {region.id})") 
#         print(f"✅ Old Groups: {old_groups_created}")
#         print(f"✅ Groups: {groups_created}")
#         print(f"✅ Districts: {districts_created}")
#         print(f"✅ Users: {users_created}")
#         print("🎉 Enhanced import completed successfully!")
        
#         # 🎯 VERIFY HIERARCHY LINKS - Check ALL users
#         print(f"\n=== HIERARCHY VERIFICATION ===")
#         all_users = User.query.all()
#         for user in all_users:
#             print(f"🔍 User {user.email}: State={user.state_id}, Region={user.region_id}, "
#                   f"District={user.district_id}, Group={user.group_id}, OldGroup={user.old_group_id}")
        
#         # Count users with proper group links
#         users_with_groups = User.query.filter(User.group_id.isnot(None)).count()
#         users_with_old_groups = User.query.filter(User.old_group_id.isnot(None)).count()
        
#         print(f"\n📊 USER HIERARCHY SUMMARY:")
#         print(f"Users with Group ID: {users_with_groups}/{len(all_users)}")
#         print(f"Users with OldGroup ID: {users_with_old_groups}/{len(all_users)}")
        
#         return {
#             "message": f"Enhanced hierarchy imported successfully under {state_name}/{region_name}!",
#             "summary": {
#                 "state": state_name,
#                 "region": region_name,
#                 "old_groups": old_groups_created,
#                 "groups": groups_created,
#                 "districts": districts_created,
#                 "users": users_created
#             },
#             "hierarchy_ids": {
#                 "state_id": state.id,
#                 "region_id": region.id
#             }
#         }
        
#     except Exception as e:
#         db.session.rollback()
#         print(f"❌ IMPORT FAILED: {str(e)}")
#         import traceback
#         print(f"Traceback: {traceback.format_exc()}")
#         raise e

