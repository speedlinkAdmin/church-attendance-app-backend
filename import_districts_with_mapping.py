# import_districts_by_name.py
import pandas as pd
import sys
import os
from datetime import datetime

# Add your app to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_duplicate_abuja_group():
    """
    Fix the duplicate Abuja group in the database by renaming it to UST GROUP
    """
    print("\n🔧 Checking for duplicate Abuja group fix...")
    
    try:
        from app import create_app, db
        from app.models import Group
        
        app = create_app()
        
        with app.app_context():
            # Find duplicate Abuja groups in CAMPUS OLD GROUP
            duplicate_groups = Group.query.filter(
                Group.name == 'ABUJA GROUP'
            ).all()
            
            if len(duplicate_groups) > 1:
                print(f"Found {len(duplicate_groups)} groups named 'ABUJA GROUP'")
                
                # Keep the first one, rename others
                for i, group in enumerate(duplicate_groups):
                    if i == 0:
                        print(f"  ✅ Keeping group ID {group.id} as 'ABUJA GROUP'")
                    else:
                        old_name = group.name
                        group.name = 'UST GROUP'
                        group.code = 'UST'
                        print(f"  🔄 Renamed group ID {group.id} from '{old_name}' to 'UST GROUP'")
                
                db.session.commit()
                print("✅ Fixed duplicate groups successfully!")
                return True
            else:
                print("✅ No duplicate groups found (already fixed)")
                return False
                
    except Exception as e:
        print(f"⚠️  Error fixing duplicate groups: {e}")
        import traceback
        traceback.print_exc()
        return False


def import_districts_by_group_name(csv_file='districts_with_group_ids.csv'):
    """
    Import districts using group NAMES instead of IDs
    """
    print("🚀 Importing Districts by Group Name")
    print("====================================")
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        print("Looking for file in current directory...")
        files = [f for f in os.listdir('.') if f.endswith('.csv')]
        if files:
            print(f"Found CSV files: {files}")
            csv_file = files[0]  # Use first CSV file
            print(f"Using: {csv_file}")
        else:
            print("❌ No CSV files found in current directory")
            return False
    
    print(f"📁 Using file: {csv_file}")
    
    try:
        # Import your Flask app components
        from app import create_app, db
        from app.models import District, Group, OldGroup
        
        # Create app context
        app = create_app()
        
        with app.app_context():
            # Read the CSV file
            df = pd.read_csv(csv_file)
            print(f"Loaded CSV: {len(df)} rows, {len(df.columns)} columns")
            print(f"Columns: {list(df.columns)}")
            
            # Check required columns - we only need district_name and group_name now
            required_columns = ['district_name', 'group_name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"❌ Missing required columns: {missing_columns}")
                print("Available columns:", list(df.columns))
                return False
            
            # Show preview
            print(f"\n📋 First 5 rows of CSV:")
            print(df.head().to_string())
            
            # Filter out empty rows
            initial_count = len(df)
            df = df[df['district_name'].notna() & (df['district_name'] != '')]
            df = df[df['group_name'].notna() & (df['group_name'] != '')]
            filtered_count = len(df)
            
            print(f"\n🔍 Found {filtered_count} valid districts (from {initial_count} total rows)")
            
            # Group districts by group for reporting
            districts_by_group = df.groupby(['group_name']).size().reset_index()
            districts_by_group.columns = ['group_name', 'district_count']
            
            print(f"\n📊 Districts by Group (first 10):")
            print(districts_by_group.head(10).to_string(index=False))
            
            # Get unique group names from CSV
            unique_groups_csv = df['group_name'].unique()
            print(f"\n📋 Found {len(unique_groups_csv)} unique groups in CSV")
            
            # Check which groups exist in database
            groups_in_db = Group.query.filter(Group.name.in_(unique_groups_csv)).all()
            group_names_in_db = {group.name: group for group in groups_in_db}
            
            print(f"✅ Found {len(groups_in_db)}/{len(unique_groups_csv)} groups in database")
            
            # Check for missing groups
            missing_groups = set(unique_groups_csv) - set(group_names_in_db.keys())
            if missing_groups:
                print(f"\n⚠️  WARNING: {len(missing_groups)} groups not found in database:")
                for group_name in list(missing_groups)[:10]:  # Show first 10
                    print(f"   - {group_name}")
                if len(missing_groups) > 10:
                    print(f"   ... and {len(missing_groups) - 10} more")
            
            # Ask for confirmation
            total_districts = filtered_count
            confirm = input(f"\nReady to import {total_districts} districts? (yes/no): ").strip().lower()
            
            if confirm != 'yes':
                print("Import cancelled.")
                return False
            
            imported_count = 0
            skipped_count = 0
            errors = []
            
            print(f"\n⏳ Importing {total_districts} districts...")
            
            # Process each district
            for index, row in df.iterrows():
                try:
                    group_name = str(row['group_name']).strip()
                    district_name = str(row['district_name']).strip()
                    
                    if not district_name or not group_name:
                        errors.append(f"Row {index}: Empty district or group name")
                        skipped_count += 1
                        continue
                    
                    # Get the group by NAME instead of ID
                    group = group_names_in_db.get(group_name)
                    if not group:
                        errors.append(f"Row {index}: Group '{group_name}' not found in database")
                        skipped_count += 1
                        continue
                    
                    # Generate district code (sequential number for this group)
                    # Count how many districts this group already has
                    existing_districts_count = District.query.filter_by(group_id=group.id).count()
                    district_code = str(existing_districts_count + 1)
                    
                    # Check if district already exists for this group
                    existing_district = District.query.filter_by(
                        group_id=group.id,
                        name=district_name
                    ).first()
                    
                    if existing_district:
                        # Update existing district
                        existing_district.code = district_code
                        existing_district.leader = f"{district_name} Leader"
                        # print(f"  ↺ Updated: '{district_name}' (Group: {group.name})")
                    else:
                        # Create new district
                        district = District(
                            name=district_name,
                            code=district_code,
                            state_id=group.state_id,
                            region_id=group.region_id,
                            old_group_id=group.old_group_id,
                            group_id=group.id,
                            leader=f"{district_name} Leader"
                        )
                        db.session.add(district)
                        # print(f"  + Added: '{district_name}' (Group: {group.name})")
                    
                    imported_count += 1
                    
                    # Progress indicator
                    if imported_count % 50 == 0:
                        print(f"  → Processed {imported_count}/{total_districts} districts...")
                        db.session.commit()  # Commit every 50 records
                    
                except Exception as e:
                    errors.append(f"Row {index}: Error '{row.get('district_name', 'N/A')}' - {str(e)}")
                    skipped_count += 1
                    continue
            
            # Final commit
            db.session.commit()
            
            print(f"\n{'='*60}")
            print("✅ IMPORT COMPLETE!")
            print(f"{'='*60}")
            print(f"📊 Summary:")
            print(f"   Total in CSV: {initial_count}")
            print(f"   Valid districts: {filtered_count}")
            print(f"   Successfully imported: {imported_count}")
            print(f"   Skipped/Errors: {skipped_count}")
            
            if errors:
                print(f"\n⚠️  Errors encountered ({len(errors)}):")
                for i, error in enumerate(errors[:5]):  # Show first 5 errors
                    print(f"   {i+1}. {error}")
                if len(errors) > 5:
                    print(f"   ... and {len(errors) - 5} more errors")
            
            # Generate detailed report
            generate_import_report_by_name(imported_count, skipped_count, errors, csv_file)
            
            # Verify import
            verify_import()
            
            return True
            
    except Exception as e:
        print(f"❌ Error importing districts: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_import_report_by_name(imported_count, skipped_count, errors, csv_file):
    """Generate a detailed import report"""
    try:
        from app import create_app, db
        from app.models import District, Group, OldGroup
        
        app = create_app()
        
        with app.app_context():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = f"district_import_report_{timestamp}.txt"
            
            with open(report_file, 'w') as f:
                f.write(f"DISTRICT IMPORT REPORT (BY GROUP NAME)\n")
                f.write(f"Generated: {datetime.now()}\n")
                f.write("="*60 + "\n\n")
                
                f.write(f"Source CSV: {csv_file}\n")
                f.write(f"Districts imported: {imported_count}\n")
                f.write(f"Districts skipped: {skipped_count}\n")
                f.write(f"Success rate: {imported_count/(imported_count+skipped_count)*100:.1f}%\n\n")
                
                # Count districts by old group
                f.write("DISTRICTS BY OLD GROUP:\n")
                f.write("-"*40 + "\n")
                
                old_groups = OldGroup.query.all()
                total_db_districts = 0
                
                for old_group in old_groups:
                    # Count districts in this old group
                    district_count = District.query.join(Group).filter(
                        Group.old_group_id == old_group.id
                    ).count()
                    
                    if district_count > 0:
                        f.write(f"{old_group.name}: {district_count} districts\n")
                        total_db_districts += district_count
                
                f.write(f"\nTOTAL DISTRICTS IN DATABASE: {total_db_districts}\n")
                
                # List all groups with their district counts
                f.write("\n\nGROUPS WITH DISTRICT COUNTS:\n")
                f.write("-"*40 + "\n")
                
                groups = Group.query.order_by(Group.old_group_id, Group.name).all()
                for group in groups:
                    district_count = District.query.filter_by(group_id=group.id).count()
                    old_group = OldGroup.query.get(group.old_group_id) if group.old_group_id else None
                    old_group_name = old_group.name if old_group else "Unknown"
                    
                    if district_count > 0:
                        f.write(f"{old_group_name} > {group.name}: {district_count} districts\n")
            
            print(f"📁 Detailed report saved to: {report_file}")
            
    except Exception as e:
        print(f"⚠️  Could not generate report: {e}")


def verify_import():
    """Verify the import was successful"""
    print(f"\n🔍 Verifying import...")
    
    try:
        from app import create_app, db
        from app.models import District, Group
        
        app = create_app()
        
        with app.app_context():
            # Count total districts
            total_districts = District.query.count()
            print(f"   Total districts in database: {total_districts}")
            
            # Count groups with districts
            groups_with_districts = db.session.query(Group).join(District).distinct().count()
            total_groups = Group.query.count()
            print(f"   Groups with districts: {groups_with_districts}/{total_groups}")
            
            # Find groups without districts
            groups_no_districts = Group.query.filter(~Group.districts.any()).all()
            if groups_no_districts:
                print(f"   ⚠️  Groups without districts: {len(groups_no_districts)}")
                for group in groups_no_districts[:5]:  # Show first 5
                    print(f"      - {group.name} (ID: {group.id})")
                if len(groups_no_districts) > 5:
                    print(f"      ... and {len(groups_no_districts) - 5} more")
            
            return total_districts
            
    except Exception as e:
        print(f"   ⚠️  Verification error: {e}")
        return 0


def check_and_fix_duplicate_groups():
    """
    Check for any duplicate groups and fix them
    """
    print("\n🔍 Checking for duplicate groups...")
    
    try:
        from app import create_app, db
        from app.models import Group, OldGroup
        
        app = create_app()
        
        with app.app_context():
            # Find groups with duplicate names within the same old group
            duplicate_issues = []
            
            # Get all old groups
            old_groups = OldGroup.query.all()
            
            for old_group in old_groups:
                # Get groups for this old group
                groups = Group.query.filter_by(old_group_id=old_group.id).all()
                
                # Check for duplicates
                seen_names = set()
                for group in groups:
                    if group.name in seen_names:
                        duplicate_issues.append({
                            'old_group': old_group.name,
                            'group_name': group.name,
                            'group_id': group.id
                        })
                    else:
                        seen_names.add(group.name)
            
            if duplicate_issues:
                print(f"Found {len(duplicate_issues)} potential duplicate groups:")
                for issue in duplicate_issues:
                    print(f"  - {issue['old_group']} > {issue['group_name']} (ID: {issue['group_id']})")
                
                # Fix the specific Abuja duplicate
                return fix_duplicate_abuja_group()
            else:
                print("✅ No duplicate groups found")
                return True
                
    except Exception as e:
        print(f"⚠️  Error checking duplicates: {e}")
        return False


def create_clean_districts_file():
    """
    Create a clean version of the districts file without IDs
    """
    print("\n🔄 Creating clean districts file...")
    
    input_file = 'districts_with_group_ids.csv'
    output_file = 'districts_by_group_name.csv'
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return None
    
    try:
        # Read the CSV
        df = pd.read_csv(input_file)
        
        # Check if we have the required columns
        if 'district_name' in df.columns and 'group_name' in df.columns:
            # Create clean DataFrame with only necessary columns
            clean_df = df[['district_name', 'group_name']].copy()
            
            # Save to new file
            clean_df.to_csv(output_file, index=False)
            print(f"✅ Created clean file: {output_file}")
            print(f"   Total districts: {len(clean_df)}")
            print(f"   Unique groups: {clean_df['group_name'].nunique()}")
            
            return output_file
        else:
            print("❌ Required columns not found in input file")
            return None
            
    except Exception as e:
        print(f"❌ Error creating clean file: {e}")
        return None


def main():
    """
    Main function to run the CSV district import
    """
    print("🚀 DISTRICT IMPORT BY GROUP NAME")
    print("="*60)
    
    # STEP 1: Fix duplicate groups before import
    print("\n1. Checking and fixing duplicate groups...")
    check_and_fix_duplicate_groups()
    
    # STEP 2: Create clean file without IDs (optional)
    print("\n2. Creating clean districts file...")
    clean_file = create_clean_districts_file()
    
    # Use either the original or clean file
    csv_file = clean_file if clean_file else 'districts_with_group_ids.csv'
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"\n⚠️  File '{csv_file}' not found.")
        print("Looking for CSV files in current directory...")
        
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
        
        if csv_files:
            print(f"\nFound CSV files:")
            for i, file in enumerate(csv_files, 1):
                print(f"  {i}. {file}")
            
            choice = input(f"\nSelect file (1-{len(csv_files)}) or enter custom path: ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(csv_files):
                csv_file = csv_files[int(choice)-1]
            elif choice:
                csv_file = choice
        else:
            print("❌ No CSV files found in current directory.")
            custom_file = input("Enter full path to CSV file: ").strip()
            if custom_file and os.path.exists(custom_file):
                csv_file = custom_file
            else:
                print("❌ File not found. Exiting.")
                return
    
    print(f"\n3. Importing districts from: {csv_file}")
    
    # Show file info
    try:
        df = pd.read_csv(csv_file, nrows=5)
        print(f"📋 File preview (first 5 rows):")
        print(df.to_string())
        
        total_rows = sum(1 for _ in open(csv_file, 'r', encoding='utf-8')) - 1  # Subtract header
        print(f"\n📊 File has approximately {total_rows} districts to import")
        
    except Exception as e:
        print(f"⚠️  Could not preview file: {e}")
    
    # Run import
    print(f"\n{'='*60}")
    success = import_districts_by_group_name(csv_file)
    
    if success:
        print("\n🎉 District import completed successfully!")
    else:
        print("\n❌ District import failed.")


if __name__ == "__main__":
    main()
















# # import_districts_fixed.py
# import pandas as pd
# import sys
# import os
# from datetime import datetime

# # Add your app to the Python path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# def fix_duplicate_abuja_group():
#     """
#     Fix the duplicate Abuja group in the database by renaming it to UST GROUP
#     """
#     print("\n🔧 Checking for duplicate Abuja group fix...")
    
#     try:
#         from app import create_app, db
#         from app.models import Group
        
#         app = create_app()
        
#         with app.app_context():
#             # Find duplicate Abuja groups in CAMPUS OLD GROUP
#             duplicate_groups = Group.query.filter(
#                 Group.name == 'ABUJA GROUP'
#             ).all()
            
#             if len(duplicate_groups) > 1:
#                 print(f"Found {len(duplicate_groups)} groups named 'ABUJA GROUP'")
                
#                 # Keep the first one, rename others
#                 for i, group in enumerate(duplicate_groups):
#                     if i == 0:
#                         print(f"  ✅ Keeping group ID {group.id} as 'ABUJA GROUP'")
#                     else:
#                         old_name = group.name
#                         group.name = 'UST GROUP'
#                         group.code = 'UST'
#                         print(f"  🔄 Renamed group ID {group.id} from '{old_name}' to 'UST GROUP'")
                
#                 db.session.commit()
#                 print("✅ Fixed duplicate groups successfully!")
#                 return True
#             else:
#                 print("✅ No duplicate groups found (already fixed)")
#                 return False
                
#     except Exception as e:
#         print(f"⚠️  Error fixing duplicate groups: {e}")
#         import traceback
#         traceback.print_exc()
#         return False


# def import_districts_from_csv(csv_file='districts_with_group_ids.csv'):
#     """
#     Import districts from the CSV file with group IDs
#     """
#     print("🚀 Importing Districts from CSV")
#     print("================================")
    
#     # Check if file exists
#     if not os.path.exists(csv_file):
#         print(f"❌ File not found: {csv_file}")
#         print("Looking for file in current directory...")
#         files = [f for f in os.listdir('.') if f.endswith('.csv')]
#         if files:
#             print(f"Found CSV files: {files}")
#             csv_file = files[0]  # Use first CSV file
#             print(f"Using: {csv_file}")
#         else:
#             print("❌ No CSV files found in current directory")
#             return False
    
#     print(f"📁 Using file: {csv_file}")
    
#     try:
#         # Import your Flask app components
#         from app import create_app, db
#         from app.models import District, Group, OldGroup
        
#         # Create app context
#         app = create_app()
        
#         with app.app_context():
#             # Read the CSV file
#             df = pd.read_csv(csv_file)
#             print(f"Loaded CSV: {len(df)} rows, {len(df.columns)} columns")
#             print(f"Columns: {list(df.columns)}")
            
#             # Check required columns
#             required_columns = ['district_name', 'group_id', 'group_name']
#             missing_columns = [col for col in required_columns if col not in df.columns]
            
#             if missing_columns:
#                 print(f"❌ Missing required columns: {missing_columns}")
#                 print("Available columns:", list(df.columns))
#                 return False
            
#             # Show preview
#             print(f"\n📋 First 5 rows of CSV:")
#             print(df.head().to_string())
            
#             # Filter out empty rows
#             initial_count = len(df)
#             df = df[df['district_name'].notna() & (df['district_name'] != '')]
#             filtered_count = len(df)
            
#             print(f"\n🔍 Found {filtered_count} valid districts (from {initial_count} total rows)")
            
#             # Group districts by group for reporting
#             districts_by_group = df.groupby(['group_id', 'group_name']).size().reset_index()
#             districts_by_group.columns = ['group_id', 'group_name', 'district_count']
            
#             print(f"\n📊 Districts by Group (first 10):")
#             print(districts_by_group.head(10).to_string(index=False))
            
#             # Ask for confirmation
#             total_districts = filtered_count
#             confirm = input(f"\nReady to import {total_districts} districts? (yes/no): ").strip().lower()
            
#             if confirm != 'yes':
#                 print("Import cancelled.")
#                 return False
            
#             imported_count = 0
#             skipped_count = 0
#             errors = []
            
#             print(f"\n⏳ Importing {total_districts} districts...")
            
#             # Process each district
#             for index, row in df.iterrows():
#                 try:
#                     group_id = int(row['group_id'])
#                     district_name = str(row['district_name']).strip()
                    
#                     if not district_name:
#                         errors.append(f"Row {index}: Empty district name")
#                         skipped_count += 1
#                         continue
                    
#                     # Get the group
#                     group = Group.query.get(group_id)
#                     if not group:
#                         errors.append(f"Row {index}: Group ID {group_id} not found")
#                         skipped_count += 1
#                         continue
                    
#                     # Generate district code (sequential number for this group)
#                     # Count how many districts this group already has
#                     existing_districts_count = District.query.filter_by(group_id=group_id).count()
#                     district_code = str(existing_districts_count + 1)
                    
#                     # Check if district already exists for this group
#                     existing_district = District.query.filter_by(
#                         group_id=group_id,
#                         name=district_name
#                     ).first()
                    
#                     if existing_district:
#                         # Update existing district
#                         existing_district.code = district_code
#                         existing_district.leader = f"{district_name} Leader"
#                     else:
#                         # Create new district
#                         district = District(
#                             name=district_name,
#                             code=district_code,
#                             state_id=group.state_id,
#                             region_id=group.region_id,
#                             old_group_id=group.old_group_id,
#                             group_id=group.id,
#                             leader=f"{district_name} Leader"
#                         )
#                         db.session.add(district)
                    
#                     imported_count += 1
                    
#                     # Progress indicator
#                     if imported_count % 50 == 0:
#                         print(f"  → Processed {imported_count}/{total_districts} districts...")
#                         db.session.commit()  # Commit every 50 records
                    
#                 except Exception as e:
#                     errors.append(f"Row {index}: Error '{row.get('district_name', 'N/A')}' - {str(e)}")
#                     skipped_count += 1
#                     continue
            
#             # Final commit
#             db.session.commit()
            
#             print(f"\n{'='*60}")
#             print("✅ IMPORT COMPLETE!")
#             print(f"{'='*60}")
#             print(f"📊 Summary:")
#             print(f"   Total in CSV: {initial_count}")
#             print(f"   Valid districts: {filtered_count}")
#             print(f"   Successfully imported: {imported_count}")
#             print(f"   Skipped/Errors: {skipped_count}")
            
#             if errors:
#                 print(f"\n⚠️  Errors encountered ({len(errors)}):")
#                 for i, error in enumerate(errors[:5]):  # Show first 5 errors
#                     print(f"   {i+1}. {error}")
#                 if len(errors) > 5:
#                     print(f"   ... and {len(errors) - 5} more errors")
            
#             # Generate detailed report
#             generate_import_report(imported_count, skipped_count, errors, csv_file)
            
#             # Verify import
#             verify_import()
            
#             return True
            
#     except Exception as e:
#         print(f"❌ Error importing districts: {e}")
#         import traceback
#         traceback.print_exc()
#         return False


# def generate_import_report(imported_count, skipped_count, errors, csv_file):
#     """Generate a detailed import report"""
#     try:
#         from app import create_app, db
#         from app.models import District, Group, OldGroup
        
#         app = create_app()
        
#         with app.app_context():
#             timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#             report_file = f"district_import_report_{timestamp}.txt"
            
#             with open(report_file, 'w') as f:
#                 f.write(f"DISTRICT IMPORT REPORT\n")
#                 f.write(f"Generated: {datetime.now()}\n")
#                 f.write("="*60 + "\n\n")
                
#                 f.write(f"Source CSV: {csv_file}\n")
#                 f.write(f"Districts imported: {imported_count}\n")
#                 f.write(f"Districts skipped: {skipped_count}\n")
#                 f.write(f"Success rate: {imported_count/(imported_count+skipped_count)*100:.1f}%\n\n")
                
#                 # Count districts by old group
#                 f.write("DISTRICTS BY OLD GROUP:\n")
#                 f.write("-"*40 + "\n")
                
#                 old_groups = OldGroup.query.all()
#                 total_db_districts = 0
                
#                 for old_group in old_groups:
#                     # Count districts in this old group
#                     district_count = District.query.join(Group).filter(
#                         Group.old_group_id == old_group.id
#                     ).count()
                    
#                     if district_count > 0:
#                         f.write(f"{old_group.name}: {district_count} districts\n")
#                         total_db_districts += district_count
                
#                 f.write(f"\nTOTAL DISTRICTS IN DATABASE: {total_db_districts}\n")
                
#                 # List all groups with their district counts
#                 f.write("\n\nGROUPS WITH DISTRICT COUNTS:\n")
#                 f.write("-"*40 + "\n")
                
#                 groups = Group.query.order_by(Group.old_group_id, Group.name).all()
#                 for group in groups:
#                     district_count = District.query.filter_by(group_id=group.id).count()
#                     old_group = OldGroup.query.get(group.old_group_id) if group.old_group_id else None
#                     old_group_name = old_group.name if old_group else "Unknown"
                    
#                     if district_count > 0:
#                         f.write(f"{old_group_name} > {group.name}: {district_count} districts\n")
            
#             print(f"📁 Detailed report saved to: {report_file}")
            
#     except Exception as e:
#         print(f"⚠️  Could not generate report: {e}")


# def verify_import():
#     """Verify the import was successful"""
#     print(f"\n🔍 Verifying import...")
    
#     try:
#         from app import create_app, db
#         from app.models import District, Group
        
#         app = create_app()
        
#         with app.app_context():
#             # Count total districts
#             total_districts = District.query.count()
#             print(f"   Total districts in database: {total_districts}")
            
#             # Count groups with districts
#             groups_with_districts = db.session.query(Group).join(District).distinct().count()
#             total_groups = Group.query.count()
#             print(f"   Groups with districts: {groups_with_districts}/{total_groups}")
            
#             # Find groups without districts
#             groups_no_districts = Group.query.filter(~Group.districts.any()).all()
#             if groups_no_districts:
#                 print(f"   ⚠️  Groups without districts: {len(groups_no_districts)}")
#                 for group in groups_no_districts[:5]:  # Show first 5
#                     print(f"      - {group.name} (ID: {group.id})")
#                 if len(groups_no_districts) > 5:
#                     print(f"      ... and {len(groups_no_districts) - 5} more")
            
#             return total_districts
            
#     except Exception as e:
#         print(f"   ⚠️  Verification error: {e}")
#         return 0


# def check_and_fix_duplicate_groups():
#     """
#     Check for any duplicate groups and fix them
#     """
#     print("\n🔍 Checking for duplicate groups...")
    
#     try:
#         from app import create_app, db
#         from app.models import Group, OldGroup
        
#         app = create_app()
        
#         with app.app_context():
#             # Find groups with duplicate names within the same old group
#             duplicate_issues = []
            
#             # Get all old groups
#             old_groups = OldGroup.query.all()
            
#             for old_group in old_groups:
#                 # Get groups for this old group
#                 groups = Group.query.filter_by(old_group_id=old_group.id).all()
                
#                 # Check for duplicates
#                 seen_names = set()
#                 for group in groups:
#                     if group.name in seen_names:
#                         duplicate_issues.append({
#                             'old_group': old_group.name,
#                             'group_name': group.name,
#                             'group_id': group.id
#                         })
#                     else:
#                         seen_names.add(group.name)
            
#             if duplicate_issues:
#                 print(f"Found {len(duplicate_issues)} potential duplicate groups:")
#                 for issue in duplicate_issues:
#                     print(f"  - {issue['old_group']} > {issue['group_name']} (ID: {issue['group_id']})")
                
#                 # Fix the specific Abuja duplicate
#                 return fix_duplicate_abuja_group()
#             else:
#                 print("✅ No duplicate groups found")
#                 return True
                
#     except Exception as e:
#         print(f"⚠️  Error checking duplicates: {e}")
#         return False


# def main():
#     """
#     Main function to run the CSV district import
#     """
#     print("🚀 DISTRICT IMPORT FROM CSV (WITH DUPLICATE FIX)")
#     print("="*60)
    
#     # STEP 1: Fix duplicate groups before import
#     print("\n1. Checking and fixing duplicate groups...")
#     check_and_fix_duplicate_groups()
    
#     # Default file name
#     csv_file = 'districts_with_group_ids.csv'
    
#     # Check if file exists
#     if not os.path.exists(csv_file):
#         print(f"\n⚠️  Default file '{csv_file}' not found.")
#         print("Looking for CSV files in current directory...")
        
#         csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
        
#         if csv_files:
#             print(f"\nFound CSV files:")
#             for i, file in enumerate(csv_files, 1):
#                 print(f"  {i}. {file}")
            
#             choice = input(f"\nSelect file (1-{len(csv_files)}) or enter custom path: ").strip()
            
#             if choice.isdigit() and 1 <= int(choice) <= len(csv_files):
#                 csv_file = csv_files[int(choice)-1]
#             elif choice:
#                 csv_file = choice
#         else:
#             print("❌ No CSV files found in current directory.")
#             custom_file = input("Enter full path to CSV file: ").strip()
#             if custom_file and os.path.exists(custom_file):
#                 csv_file = custom_file
#             else:
#                 print("❌ File not found. Exiting.")
#                 return
    
#     print(f"\n2. Importing districts from: {csv_file}")
    
#     # Show file info
#     try:
#         df = pd.read_csv(csv_file, nrows=5)
#         print(f"📋 File preview (first 5 rows):")
#         print(df.to_string())
        
#         total_rows = sum(1 for _ in open(csv_file, 'r', encoding='utf-8')) - 1  # Subtract header
#         print(f"\n📊 File has approximately {total_rows} districts to import")
        
#     except Exception as e:
#         print(f"⚠️  Could not preview file: {e}")
    
#     # Run import
#     print(f"\n{'='*60}")
#     success = import_districts_from_csv(csv_file)
    
#     if success:
#         print("\n🎉 District import completed successfully!")
#     else:
#         print("\n❌ District import failed.")


# if __name__ == "__main__":
#     main()








