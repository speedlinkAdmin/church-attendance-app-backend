# export_group_mappings_clean.py
import sys
import os
import pandas as pd
from datetime import datetime

# Add your app to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def export_group_mappings_simple():
    """
    Simple export of groups with their IDs for district mapping
    """
    print("🚀 Exporting Group Mappings for District Import")
    print("===============================================")
    
    try:
        # Import your Flask app components
        from app import create_app, db
        from app.models import Group, OldGroup
        
        # Create app context
        app = create_app()
        
        with app.app_context():
            # Query all groups with their old groups
            groups = db.session.query(
                Group.id,
                Group.name,
                Group.code,
                Group.old_group_id,
                OldGroup.name.label('old_group_name'),
                OldGroup.code.label('old_group_code')
            ).join(OldGroup, Group.old_group_id == OldGroup.id).all()
            
            print(f"Found {len(groups)} groups in database")
            
            # Convert to list of dictionaries
            export_data = []
            for group in groups:
                export_data.append({
                    'group_id': group.id,
                    'group_name': group.name,
                    'group_code': group.code,
                    'old_group_id': group.old_group_id,
                    'old_group_name': group.old_group_name,
                    'old_group_code': group.old_group_code
                })
            
            if export_data:
                # Create DataFrame
                export_df = pd.DataFrame(export_data)
                
                # Save to Excel
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                excel_filename = f"group_mappings_clean_{timestamp}.xlsx"
                
                # Create Excel writer with multiple sheets
                with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                    # Sheet 1: All groups sorted by old group
                    export_df.sort_values(['old_group_name', 'group_name']).to_excel(
                        writer, sheet_name='All_Groups', index=False
                    )
                    
                    # Sheet 2: Groups by Old Group (for easy reference)
                    for old_group_name in export_df['old_group_name'].unique():
                        old_group_groups = export_df[export_df['old_group_name'] == old_group_name]
                        sheet_name = old_group_name[:31].replace('OLD GROUP', 'OG').replace(' ', '_')  # Excel sheet name limit
                        old_group_groups.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Sheet 3: Summary
                    summary_data = []
                    for old_group_name in export_df['old_group_name'].unique():
                        count = len(export_df[export_df['old_group_name'] == old_group_name])
                        summary_data.append({
                            'Old Group': old_group_name,
                            'Number of Groups': count
                        })
                    
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                print(f"✅ Exported {len(export_data)} groups to Excel: {excel_filename}")
                
                # Also save to CSV for easy sharing
                csv_filename = f"group_mappings_clean_{timestamp}.csv"
                export_df.to_csv(csv_filename, index=False)
                print(f"✅ Also saved as CSV: {csv_filename}")
                
                # Print summary
                print(f"\n📊 Summary:")
                print(f"   Total Groups: {len(export_data)}")
                print(f"   Total Old Groups: {export_df['old_group_name'].nunique()}")
                
                # Show first 10 groups
                print(f"\n📋 First 10 groups:")
                print(export_df[['group_id', 'group_name', 'old_group_name']].head(10).to_string())
                
                return excel_filename
            else:
                print("⚠️  No groups found in database")
                return None
                
    except Exception as e:
        print(f"❌ Error exporting group mappings: {e}")
        import traceback
        traceback.print_exc()
        return None


def export_groups_for_district_template():
    """
    Create a template Excel file for the other developer to fill districts
    """
    print("\n🚀 Creating District Mapping Template")
    print("=====================================")
    
    try:
        # Import your Flask app components
        from app import create_app, db
        from app.models import Group, OldGroup
        
        # Create app context
        app = create_app()
        
        with app.app_context():
            # Get all groups
            groups = db.session.query(
                Group.id,
                Group.name,
                OldGroup.name.label('old_group_name')
            ).join(OldGroup, Group.old_group_id == OldGroup.id).order_by(OldGroup.name, Group.name).all()
            
            # Create template data
            template_data = []
            
            for group in groups:
                # Create 10 empty district slots for each group
                for i in range(1, 11):  # Up to 10 districts per group
                    template_data.append({
                        'group_id': group.id,
                        'group_name': group.name,
                        'old_group_name': group.old_group_name,
                        'district_number': f'District {i}',
                        'district_name': '',  # Empty for developer to fill
                        'district_code': ''   # Empty for developer to fill
                    })
            
            if template_data:
                # Create DataFrame
                template_df = pd.DataFrame(template_data)
                
                # Save to Excel
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                template_filename = f"district_mapping_template_{timestamp}.xlsx"
                
                # Create Excel with formatting
                with pd.ExcelWriter(template_filename, engine='openpyxl') as writer:
                    # Main template sheet
                    template_df.to_excel(writer, sheet_name='Template', index=False)
                    
                    # Instructions sheet
                    instructions = pd.DataFrame({
                        'Instruction': [
                            '1. Fill in district_name and district_code for each district',
                            '2. Delete rows for districts that don\'t exist',
                            '3. Add more rows if a group has more than 10 districts',
                            '4. Save file as "districts_filled.xlsx"',
                            '5. The district_code should be a number (1, 2, 3, etc.)',
                            '6. Keep group_id and group_name as reference only',
                            '7. Do not modify group_id values'
                        ]
                    })
                    instructions.to_excel(writer, sheet_name='Instructions', index=False)
                    
                    # Groups reference sheet
                    groups_ref = [{'group_id': g.id, 'group_name': g.name, 'old_group_name': g.old_group_name} 
                                 for g in groups]
                    groups_ref_df = pd.DataFrame(groups_ref)
                    groups_ref_df.to_excel(writer, sheet_name='Groups_Reference', index=False)
                
                print(f"✅ Created template: {template_filename}")
                print(f"   Contains {len(template_data)} rows (10 slots per group)")
                print(f"   Reference for {len(groups)} groups")
                
                return template_filename
            else:
                print("⚠️  No groups found to create template")
                return None
                
    except Exception as e:
        print(f"❌ Error creating template: {e}")
        return None


def main():
    """
    Main function to run exports
    """
    print("🚀 GROUP AND DISTRICT MAPPING EXPORT")
    print("="*60)
    
    print("\n1. Exporting group mappings...")
    groups_file = export_group_mappings_simple()
    
    print("\n2. Creating district mapping template...")
    template_file = export_groups_for_district_template()
    
    print("\n" + "="*60)
    print("✅ EXPORT COMPLETE!")
    
    if groups_file:
        print(f"📁 Groups exported to: {groups_file}")
    
    if template_file:
        print(f"📁 Template created: {template_file}")
    
    if groups_file and template_file:
        print("\n📝 Give these files to the other developer:")
        print(f"   1. {groups_file} - For reference")
        print(f"   2. {template_file} - To fill in districts")
        print("\n📋 When they return the filled file, run:")
        print("   python import_districts_from_template.py")


if __name__ == "__main__":
    main()