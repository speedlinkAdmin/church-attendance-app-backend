# prepare_districts_csv.py
import pandas as pd
import json

def prepare_districts_file():
    """
    Step 3: Create a clean districts CSV from your original data
    This reads the original file and creates districts with group names
    """
    print("\n🚀 STEP 3: Preparing Districts CSV File")
    print("========================================")
    
    # Read original file
    try:
        df = pd.read_csv('hierarchy.csv', header=None, encoding='latin-1')
    except:
        df = pd.read_excel('hierarchy.xlsx', header=None)
    
    print(f"Loaded file: {df.shape[0]} rows, {df.shape[1]} columns")
    
    districts_data = []
    
    # Simple parser to extract districts
    for i in range(len(df)):
        row = df.iloc[i].astype(str).str.strip().tolist()
        row_str = ' '.join([v for v in row if v])
        
        if 'OLD GROUP' in row_str.upper():
            old_group_name = next((v for v in row if 'OLD GROUP' in v.upper()), '')
            print(f"\nProcessing: {old_group_name}")
            
            # Find groups in next row
            if i + 1 < len(df):
                group_row = df.iloc[i + 1].astype(str).str.strip().tolist()
                groups = []
                group_cols = []
                
                for col, val in enumerate(group_row):
                    if val and val != 'nan' and not val.isdigit():
                        groups.append(val)
                        group_cols.append(col)
                
                if groups:
                    print(f"  Groups: {groups}")
                    
                    # Process district rows
                    row_idx = i + 2
                    while row_idx < len(df):
                        dist_row = df.iloc[row_idx].astype(str).str.strip().tolist()
                        
                        # Stop if next OLD GROUP or empty
                        if 'OLD GROUP' in ' '.join(dist_row).upper():
                            break
                        
                        if all(v == '' or v == 'nan' for v in dist_row):
                            row_idx += 1
                            continue
                        
                        # Extract districts for each group
                        for group_idx, group_name in enumerate(groups):
                            group_col = group_cols[group_idx]
                            
                            # Look for district number in group_col or group_col-1
                            for check_col in [group_col, group_col-1]:
                                if 0 <= check_col < len(dist_row):
                                    dist_num = dist_row[check_col]
                                    dist_name = dist_row[check_col + 1] if check_col + 1 < len(dist_row) else ''
                                    
                                    if dist_num.isdigit() and dist_name and dist_name != 'nan':
                                        districts_data.append({
                                            'group_name': group_name,
                                            'district_number': dist_num,
                                            'district_name': dist_name
                                        })
                        
                        row_idx += 1
    
    # Create districts CSV
    if districts_data:
        districts_df = pd.DataFrame(districts_data)
        districts_df.to_csv('districts_clean.csv', index=False)
        print(f"\n✅ Created districts_clean.csv with {len(districts_data)} districts")
        print("First 5 rows:")
        print(districts_df.head())
    else:
        print("❌ No districts found")

if __name__ == "__main__":
    prepare_districts_file()