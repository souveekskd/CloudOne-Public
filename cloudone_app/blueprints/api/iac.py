from flask import Blueprint, jsonify, request, current_app
from dotenv import load_dotenv
from cloudone_app.services.ai_service import get_iac_code

# Load .env file
load_dotenv()

# Blueprint
iac_bp = Blueprint('api_iac', __name__, url_prefix='/api/iac')

@iac_bp.route("/generate", methods=["POST"])
def generate_iac_code():
    data = request.get_json()
    current_app.logger.debug(f"Received IaC generation request: {data}")

    iac_type = data.get("iac_type") # 'terraform', 'bicep', 'arm'
    module_type = data.get("module_type") # 'custom', 'avm' (only for terraform)
    resources = data.get("resources")    

    if not iac_type or not resources:
        return jsonify({"error": "Missing iac_type or resources"}), 400
    
    if iac_type == 'terraform' and not module_type:
        return jsonify({"error": "Missing module_type for Terraform"}), 400

    try:
        # Call the new refactored service
        iac_files = get_iac_code(iac_type, module_type, resources)
        
        if "error" in iac_files:
            return jsonify(iac_files), 500

        # The service now returns a full payload
        # e.g., {"iac_type": "bicep", "files": {"main.bicep": "..."}}
        # or {"iac_type": "terraform", "files": {"root": {...}, "modules": {...}}}
        return jsonify(iac_files)

    except Exception as e:
        current_app.logger.error(f"Failed to generate IaC module: {str(e)}")
        return jsonify({"error": str(e)}), 500
