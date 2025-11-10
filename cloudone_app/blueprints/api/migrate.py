from flask import Blueprint, jsonify, request, current_app
from dotenv import load_dotenv
from cloudone_app.services.ai_service import get_migration_recommendation

# Load .env file
load_dotenv()

# Blueprint
migrate_bp = Blueprint('api_migrate', __name__, url_prefix='/api/azure/migrate')

@migrate_bp.route("/manual_plan", methods=["POST"])
def get_manual_migration_plan():
    data = request.get_json()
    current_app.logger.debug(f"Received migration bot request: {data}")

    try:
        app_name = data.get("appName")
        region = data.get("region")
        target_type = data.get("target_type")
        db_required = data.get("db_required", False)
        db_prompt_details = ""
        if db_required:
            db_prompt_details = f"""
        Database Required: Yes
        Database Type: {data.get("db_type", "N/A")}
        Database vCores: {data.get("db_vCore", "N/A")}
        Database RAM: {data.get("db_ram", "N/A")} GB
        Database Size: {data.get("db_size", "N/A")} GB
        """
        else:
            db_prompt_details = "Database Required: No"

        prompt = f"""
        Current On-Premises Application: {app_name}
        Current OS: {data.get("systemOS")} ({data.get("systemVersion")})
        Current vCPUs: {data.get("vCore")}
        Current RAM: {data.get("systemRAM")} GB
        Current Storage: {data.get("storageSize")} GB ({data.get("storageType")})
        Number of Users: {data.get("numUsers")}
        Target Azure Region: {region}
        Target Migration Strategy: {target_type}
        {db_prompt_details}
        Integration Details: {data.get("integration_details", "Not provided")}
        Please generate the JSON migration plan.
        """

        ai_plan = get_migration_recommendation(prompt)
        if "error" in ai_plan:
            return jsonify(ai_plan), 500

        compute_cost = 0.0
        compute_hourly = 0.0
        if "compute_recommendation" in ai_plan and "estimated_hourly_price_payg" in ai_plan["compute_recommendation"]:
            compute_hourly = ai_plan["compute_recommendation"]["estimated_hourly_price_payg"]
            compute_cost = round(compute_hourly * 730, 2) 

        db_cost = 0.0
        db_hourly = 0.0
        if "database_recommendation" in ai_plan and "estimated_hourly_price_payg" in ai_plan["database_recommendation"]:
            db_hourly = ai_plan["database_recommendation"]["estimated_hourly_price_payg"]
            db_cost = round(db_hourly * 730, 2)

        ai_plan["compute_recommendation"]["estimated_monthly_cost"] = compute_cost
        ai_plan["database_recommendation"]["estimated_monthly_cost"] = db_cost
        ai_plan["total_estimated_monthly_cost"] = round(compute_cost + db_cost, 2)

        return jsonify(ai_plan)

    except Exception as e:
        current_app.logger.error(f"Failed to generate manual migration plan: {str(e)}")
        return jsonify({"error": str(e)}), 500