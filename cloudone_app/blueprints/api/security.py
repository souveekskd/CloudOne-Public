from flask import Blueprint, jsonify, current_app
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.security import SecurityCenter

# Load .env file
load_dotenv()

# Blueprint
security_bp = Blueprint('api_security', __name__, url_prefix='/api/azure/security')

@security_bp.route("/score/<subscription_id>", methods=["GET"])
def get_security_score(subscription_id):
    credential = DefaultAzureCredential()
    try:
        security_client = SecurityCenter(credential=credential, subscription_id=subscription_id)
        scores_list = list(security_client.secure_scores.list())

        if not scores_list:
            current_app.logger.warning(f"No security scores found for {subscription_id}.")
            return jsonify({"display_name": "Security Score", "current": 0, "max": 0, "percentage": 0, "error": "No score data found."}), 500

        score = next((s for s in scores_list if s.name == "ascScore"), None)

        if not score:
            current_app.logger.warning(f"'ascScore' not found, using first available score for {subscription_id}.")
            score = scores_list[0]

        if not score or not score.max or score.max == 0:
            current_app.logger.warning(f"Valid score data not found for {subscription_id}.")
            return jsonify({"display_name": "Security Score", "current": 0, "max": 0, "percentage": 0, "error": "Score data is invalid or empty."}), 500

        score_data = {
            "display_name": score.display_name,
            "current": score.current,
            "max": score.max,
            "percentage": round((score.current / score.max) * 100, 2)
        }
        return jsonify(score_data)

    except Exception as e:
        current_app.logger.error(f"Failed to fetch security score: {str(e)}")
        return jsonify({"display_name": "Security Score", "current": 0, "max": 0, "percentage": 0, "error": str(e)}), 500