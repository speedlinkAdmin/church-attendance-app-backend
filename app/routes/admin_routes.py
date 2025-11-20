# app/routes/admin_routes.py
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import importlib
from app.utils.excel_importer import import_hierarchy_from_excel
# Force reload the module
# importlib.reload(utils.excel_importer)
from app.utils.excel_importer_new import import_hierarchy_from_excel
from app.utils.access_control import require_role
import os
import tempfile

admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.post("/import-hierarchy")
def import_hierarchy():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    state_name = request.form.get("state_name")
    if not state_name:
        return jsonify({"error": "State name is required"}), 400

    # DEBUG: Check which function we're actually using
    print(f"=== DEBUG: Starting import ===")
    print(f"Import function: {import_hierarchy_from_excel}")
    print(f"Import function location: {import_hierarchy_from_excel.__module__}")
    print(f"Import function file: {import_hierarchy_from_excel.__code__.co_filename}")

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        file_path = tmp_file.name
        file.save(file_path)

    try:
        print(f"=== DEBUG: Calling import function ===")
        result = import_hierarchy_from_excel(file_path, state_name)
        print(f"=== DEBUG: Import completed ===")
        
        # Clean up
        try:
            os.unlink(file_path)
        except:
            pass
            
        return jsonify(result), 200
        
    except Exception as e:
        print(f"=== DEBUG: Import failed ===")
        print(f"Error: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        # Clean up
        try:
            os.unlink(file_path)
        except:
            pass
            
        return jsonify({"error": str(e)}), 400
    

# @admin_bp.post("/import-hierarchy")
# # @require_role(["super admin"])
# def import_hierarchy():
#     """
#     Import Church Hierarchy from Excel
#     ---
#     tags:
#       - Admin
#     consumes:
#       - multipart/form-data
#     parameters:
#       - name: file
#         in: formData
#         type: file
#         required: true
#         description: Excel file containing hierarchy data
#       - name: state_name
#         in: formData
#         type: string
#         required: true
#         description: State name for this data (e.g. "Rivers Central")
#     responses:
#       200:
#         description: Success message
#         schema:
#           type: object
#           properties:
#             message:
#               type: string
#       400:
#         description: Error in file upload or parsing
#     """
#     if "file" not in request.files:
#         return jsonify({"error": "No file provided"}), 400

#     file = request.files["file"]
#     state_name = request.form.get("state_name")
#     if not state_name:
#         return jsonify({"error": "State name is required"}), 400
    
#     # DEBUG: Check which function we're actually using
#     print(f"Import function location: {import_hierarchy_from_excel.__module__}")
#     print(f"Import function file: {import_hierarchy_from_excel.__code__.co_filename}")

#     # FIX: Use tempfile for cross-platform compatibility
#     filename = secure_filename(file.filename)
    
#     # Create a temporary file that works on both Windows and Linux
#     with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
#         file_path = tmp_file.name
#         file.save(file_path)

#     try:
#         result = import_hierarchy_from_excel(file_path, state_name)
        
#         # Clean up the temporary file
#         try:
#             os.unlink(file_path)
#         except:
#             pass  # Ignore cleanup errors
            
#         return jsonify(result), 200
        
#     except Exception as e:
#         # Clean up the temporary file even on error
#         try:
#             os.unlink(file_path)
#         except:
#             pass
            
#         return jsonify({"error": str(e)}), 400
   