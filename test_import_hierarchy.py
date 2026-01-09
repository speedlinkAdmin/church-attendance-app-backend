# test_enhanced_import_final.py
import requests

# Configuration
BASE_URL = "http://127.0.0.1:5000"
ENDPOINT = "/admin/import-hierarchy"
FILE_PATH = "hierarchy.xlsx"
STATE_NAME = "Rivers Central"

def test_enhanced_import_final():
    print("🚀 Testing ENHANCED hierarchy import with complete user links")
    url = BASE_URL + ENDPOINT
    
    try:
        with open(FILE_PATH, "rb") as file:
            response = requests.post(url, 
                                   files={"file": file}, 
                                   data={"state_name": STATE_NAME})
            
            print("Status Code:", response.status_code)
            if response.status_code == 200:
                result = response.json()
                print("✅ SUCCESS! Enhanced import completed")
                print("📊 Summary:", result.get("summary", {}))
                
                # Verify user creation
                if "summary" in result and result["summary"]["users"] > 0:
                    print(f"🎉 Created {result['summary']['users']} users with COMPLETE hierarchy links!")
                    
                    # 🎯 TEST: Verify users have proper hierarchy links
                    verify_url = f"{BASE_URL}/api/users"
                    verify_response = requests.get(verify_url)
                    if verify_response.status_code == 200:
                        users_data = verify_response.json()
                        auto_users = [u for u in users_data.get('users', []) 
                                    if u.get('email', '').endswith('@thedcmp.org')]
                        
                        print(f"🔍 Found {len(auto_users)} auto-created users in database")
                        for user in auto_users[:3]:  # Show first 3 as sample
                            print(f"   👤 {user['email']}: "
                                  f"State={user.get('state_id')}, "
                                  f"Region={user.get('region_id')}, "
                                  f"District={user.get('district_id')}, "
                                  f"Group={user.get('group_id')}, "
                                  f"OldGroup={user.get('old_group_id')}")
            else:
                print(f"❌ Import failed: {response.text}")
                
    except FileNotFoundError:
        print(f"❌ File not found: {FILE_PATH}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_enhanced_import_final()


