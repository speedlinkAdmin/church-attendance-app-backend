# app/routes/admin_routes.py
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import importlib
# from app.utils.excel_importer import import_hierarchy_from_excel
# Force reload the module
# importlib.reload(utils.excel_importer)
from app.utils.excel_importer_new import import_hierarchy_from_excel
from app.utils.access_control import require_role
import os
import tempfile
import datetime
from datetime import datetime

admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.post("/import-hierarchy")
def import_hierarchy():

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    state_name = request.form.get("state_name", "Rivers Central")  # 🎯 Default to Rivers Central
    import_districts = request.form.get('import_districts', 'false').lower() == 'true'
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        return jsonify({"error": "Only Excel files (.xlsx, .xls, .csv) are allowed"}), 400

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        file_path = tmp_file.name
        file.save(file_path)

    try:
        print(f"=== Starting hierarchy import for state: {state_name} ===")
        
        # 🎯 Use enhanced importer with fixed state and region
        result = import_hierarchy_from_excel(file_path, state_name, import_districts=import_districts)
        
        print(f"=== Hierarchy import completed ===")
        
        # Clean up
        try:
            os.unlink(file_path)
        except:
            pass
            
        return jsonify(result), 200
        
    except Exception as e:
        print(f"=== Hierarchy import failed ===")
        print(f"Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        # Clean up
        try:
            os.unlink(file_path)
        except:
            pass
            
        return jsonify({"error": str(e)}), 400

        