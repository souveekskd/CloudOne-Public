from flask import Blueprint, jsonify, request, current_app
from dotenv import load_dotenv
from cloudone_app.services.ai_service import get_ai_remediation

# Load .env file
load_dotenv()

# Blueprint
ai_bp = Blueprint('api_ai', __name__, url_prefix='/api/ai')

@ai_bp.route("/remediate", methods=["POST"])
def get_remediation_steps():
    """
    API endpoint to be called by the frontend button.
    """
    data = request.get_json()
    problem = data.get("problem_description")

    if not problem:
        return jsonify({"error": "No problem_description provided"}), 400
    
    try:
        remediation = get_ai_remediation(problem)
        if "error" in remediation:
            return jsonify(remediation), 500
        return jsonify(remediation)
    except Exception as e:
        current_app.logger.error(f"Failed to get remediation: {str(e)}")
        return jsonify({"error": str(e)}), 500
