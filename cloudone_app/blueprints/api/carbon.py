from flask import Blueprint, jsonify, current_app
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.carbonoptimization import CarbonOptimizationMgmtClient
from azure.mgmt.carbonoptimization.models import (
    DateRange,
    EmissionScopeEnum,
    OverallSummaryReportQueryFilter
)
import logging

# Load .env file
load_dotenv()

# Blueprint
carbon_bp = Blueprint('api_carbon', __name__, url_prefix='/api/azure/carbon')

@carbon_bp.route("/summary/<subscription_id>", methods=["GET"])
def get_carbon_summary(subscription_id):
    """
    Fetches the latest overall carbon emission summary for a subscription.
    """
    credential = DefaultAzureCredential()
    try:
        carbon_client = CarbonOptimizationMgmtClient(credential=credential)
        
        # 1. Get the latest available date range from the service
        # Data is typically available for the previous full month.
        available_date_range = carbon_client.carbon_service.query_carbon_emission_data_available_date_range()
        
        if not available_date_range or not available_date_range.end_date:
            current_app.logger.warning(f"No available carbon data date range found for sub {subscription_id}.")
            return jsonify({"error": "No carbon data available from the service yet."}), 404

        # 2. Build the filter for an Overall Summary report
        query_filter = OverallSummaryReportQueryFilter(
            date_range=DateRange(
                start=available_date_range.start_date,
                end=available_date_range.end_date
            ),
            subscription_list=[subscription_id],
            carbon_scope_list=[
                EmissionScopeEnum.SCOPE1,
                EmissionScopeEnum.SCOPE2,
                EmissionScopeEnum.SCOPE3
            ]
        )

        # 3. Query the reports API
        result = carbon_client.carbon_service.query_carbon_emission_reports(query_filter)

        if not result or not result.value:
            current_app.logger.warning(f"Carbon summary report was empty for sub {subscription_id}.")
            return jsonify({"error": "No summary data returned for the available date range."}), 404

        # 4. Return the first summary item as a dictionary
        summary_data = result.value[0].as_dict()
        
        return jsonify(summary_data)

    except Exception as e:
        current_app.logger.error(f"Failed to fetch carbon summary: {str(e)}")
        return jsonify({"error": str(e)}), 500