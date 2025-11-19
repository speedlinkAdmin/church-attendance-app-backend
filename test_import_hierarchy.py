import requests

# Configuration
BASE_URL = "http://127.0.0.1:5000"  # adjust if running in Docker or different host
ENDPOINT = "/admin/import-hierarchy"
FILE_PATH = "hierarchy.xlsx"  # the Excel file you dropped in root
STATE_NAME = "Rivers Central"

# Admin token (if using JWT for authentication)
# Replace with a valid token for your super admin
# JWT_TOKEN = "your_super_admin_jwt_here"

def test_import_hierarchy():
    url = BASE_URL + ENDPOINT
    # headers = {
    #     "Authorization": f"Bearer {JWT_TOKEN}"
    # }
    files = {
        "file": open(FILE_PATH, "rb")
    }
    data = {
        "state_name": STATE_NAME
    }

    response = requests.post(url, 
                            #  headers=headers, 
                             files=files, data=data)
    
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())


if __name__ == "__main__":
    test_import_hierarchy()
