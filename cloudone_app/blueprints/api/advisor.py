from flask import Blueprint, jsonify, current_app
from dotenv import load_dotenv
import requests
from azure.identity import DefaultAzureCredential

# Load .env file
load_dotenv()

# Blueprint
advisor_bp = Blueprint('api_advisor', __name__, url_prefix='/api/azure/advisor')

@advisor_bp.route("/scores/<subscription_id>", methods=["GET"])
def get_advisor_scores(subscription_id):
    credential = DefaultAzureCredential()
    try:
        token = credential.get_token("https://management.azure.com/.default")
        url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Advisor/advisorScore?api-version=2023-01-01"
        headers = {
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status() 

        data = response.json()
        scores_list = data.get('value', [])
        results = {}
        if not scores_list:
            current_app.logger.warning(f"No Advisor Scores found for subscription {subscription_id}.")
            return jsonify({"error": "No Advisor Scores found."}), 404

        for score_entity in scores_list:
            pillar_name = score_entity.get('name')
            properties = score_entity.get('properties', {})
            impact_breakdown = properties.get('recommendationsByImpact', {})

            results[pillar_name.lower()] = {
                "score": properties.get('score', 0),
                "total_recommendations": properties.get('recommendationsCount', 0),
                "impacted_resources": properties.get('impactedResourcesCount', 0),
                "impact": {
                    "high": impact_breakdown.get('high', 0),
                    "medium": impact_breakdown.get('medium', 0),
                    "low": impact_breakdown.get('low', 0)
                }
            }

        if "highavailability" in results:
            results["reliability"] = results.pop("highavailability")

        return jsonify(results)

    except Exception as e:
        current_app.logger.error(f"Failed to fetch advisor scores: {str(e)}")
        return jsonify({"error": str(e)}), 500

@advisor_bp.route("/recommendations/<subscription_id>/<category>", methods=["GET"])
def get_advisor_recommendations_by_category(subscription_id, category):
    credential = DefaultAzureCredential()
    try:
        token = credential.get_token("https://management.azure.com/.default")

        if category.lower() == 'reliability':
            api_category = 'HighAvailability'
        else:
            api_category = category.capitalize()

        url = (
            f"https://management.azure.com/subscriptions/{subscription_id}"
            f"/providers/Microsoft.Advisor/recommendations"
            f"?api-version=2023-01-01"
            f"&$filter=Category eq '{api_category}'"
        )
        headers = {
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        recommendations_list = data.get('value', [])
        results = []
        for rec in recommendations_list:
            properties = rec.get('properties', {})
            if not properties.get('suppressionId'):

                # --- NEW LOGIC: Get extended details ---
                extended_props = properties.get('extendedProperties', {})

                results.append({
                    "impact": properties.get('impact'),
                    "description": properties.get('shortDescription', {}).get('problem', 'No description available'),
                    "impacted_resource": properties.get('impactedField'),
                    "learn_more_link": properties.get('learnMoreLink'),
                    # --- NEW FIELDS FOR OPTIMIZATION ---
                    "resource_group": properties.get('resourceGroup', 'N/A'),
                    "potential_savings": extended_props.get('savingsAmount', '0'),
                    "savings_currency": extended_props.get('savingsCurrency', 'USD')
                })

        return jsonify({"recommendations": results})

    except Exception as e:
        current_app.logger.error(f"Failed to fetch advisor recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500