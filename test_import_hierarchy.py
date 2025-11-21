import requests

# Configuration
BASE_URL = "http://127.0.0.1:5000"  # adjust if running in Docker or different host
ENDPOINT = "/admin/import-hierarchy"
FILE_PATH = "hierarchy.xlsx"  # the Excel file you dropped in root
STATE_NAME = "Rivers Central"



def test_enhanced_import():
    url = BASE_URL + ENDPOINT
    
    try:
        with open(FILE_PATH, "rb") as file:
            response = requests.post(url, 
                                   files={"file": file}, 
                                   data={"state_name": STATE_NAME})
            
            print("Status Code:", response.status_code)
            if response.status_code == 200:
                result = response.json()
                print("✅ SUCCESS! Response:", result)
                
                # Verify user links
                if "summary" in result and result["summary"]["users"] > 0:
                    print(f"🎉 Created {result['summary']['users']} users with proper hierarchy links!")
            else:
                print(f"❌ Request failed: {response.text}")
                
    except FileNotFoundError:
        print(f"❌ File not found: {FILE_PATH}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_enhanced_import()

# def test_import_hierarchy():
#     url = BASE_URL + ENDPOINT
#     files = {
#         "file": open(FILE_PATH, "rb")
#     }
#     data = {
#         "state_name": STATE_NAME
#     }
    
#     response = requests.post(url, files=files, data=data)
    
#     print("Status Code:", response.status_code)
#     result = response.json()
#     print("Response JSON:", result)
    
#     # Check if users were created
#     if "summary" in result and "users" in result["summary"]:
#         print(f"✅ Users created: {result['summary']['users']}")

# if __name__ == "__main__":
#     test_import_hierarchy()
