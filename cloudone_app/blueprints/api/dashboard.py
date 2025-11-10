from flask import Blueprint, jsonify, current_app
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.security import SecurityCenter
from azure.mgmt.carbonoptimization import CarbonOptimizationMgmtClient
from azure.mgmt.carbonoptimization.models import (
    DateRange,
    EmissionScopeEnum,
    OverallSummaryReportQueryFilter
)
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest
import requests
import logging
import time
from threading import Lock

# Import the monitoring function
from .monitoring import _get_monitoring_status_data

# Import the concurrency tool
from concurrent.futures import ThreadPoolExecutor

# Load .env file
load_dotenv()

# Blueprint
dashboard_bp = Blueprint('api_dashboard', __name__, url_prefix='/api/azure/dashboard')

# --- NEW CACHING MECHANISM ---
# This is a simple, thread-safe, in-memory cache.
# This is NOT a file. This lives in the server's memory.
_cache = {}
_cache_lock = Lock()
CACHE_TTL_SECONDS = 60 # Cache data for 60 seconds

# --- Internal Helper Functions ---
# (All helper functions: _get_security_score, _get_advisor_scores, _get_carbon_summary,
# _get_orphan_counts, _get_resource_counts, _get_top_recommendations remain UNCHANGED.
# They are synchronous, which is what the ThreadPoolExecutor wants.)

def _get_security_score(credential, subscription_id):
    """Fetches the main security score."""
    try:
        security_client = SecurityCenter(credential=credential, subscription_id=subscription_id)
        scores_list = list(security_client.secure_scores.list())
        score = next((s for s in scores_list if s.name == "ascScore"), scores_list[0] if scores_list else None)
        if score and score.max > 0:
            return {
                "current": score.current,
                "max": score.max,
                "percentage": round((score.current / score.max) * 100, 2)
            }
    except Exception as e:
        current_app.logger.error(f"Dashboard: Failed to get security score: {e}")
    return {"current": 0, "max": 0, "percentage": 0}

def _get_advisor_scores(credential, subscription_id):
    """Fetches all advisor scores."""
    scores = {}
    try:
        token = credential.get_token("https://management.azure.com/.default")
        url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Advisor/advisorScore?api-version=2023-01-01"
        headers = {"Authorization": f"Bearer {token.token}", "Content-Type": "application/json"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json().get('value', [])
        
        for score_entity in data:
            pillar = score_entity.get('name').lower()
            if pillar == "highavailability":
                pillar = "reliability" # Rename for consistency
            scores[pillar] = {
                "score": score_entity.get('properties', {}).get('score', 0)
            }
    except Exception as e:
        current_app.logger.error(f"Dashboard: Failed to get advisor scores: {e}")
    
    # Ensure all pillars exist, even if API call fails
    for pillar in ["cost", "security", "reliability", "operationalexcellence", "performance"]:
        if pillar not in scores:
            scores[pillar] = {"score": 0}
            
    return scores

def _get_carbon_summary(credential, subscription_id):
    """Fetches the latest carbon summary."""
    try:
        carbon_client = CarbonOptimizationMgmtClient(credential=credential)
        available_date_range = carbon_client.carbon_service.query_carbon_emission_data_available_date_range()
        if available_date_range and available_date_range.end_date:
            query_filter = OverallSummaryReportQueryFilter(
                date_range=DateRange(start=available_date_range.start_date, end=available_date_range.end_date),
                subscription_list=[subscription_id],
                carbon_scope_list=[EmissionScopeEnum.SCOPE1, EmissionScopeEnum.SCOPE2, EmissionScopeEnum.SCOPE3]
            )
            result = carbon_client.carbon_service.query_carbon_emission_reports(query_filter)
            if result and result.value:
                summary = result.value[0].as_dict()
                return {"total_emissions": summary.get("total_carbon_emission", 0)}
    except Exception as e:
        current_app.logger.error(f"Dashboard: Failed to get carbon summary: {e}")
    return {"total_emissions": 0}

def _get_orphan_counts(credential, subscription_id):
    """Fetches counts of orphaned resources."""
    total_orphans = 0
    try:
        resource_graph_client = ResourceGraphClient(credential)
        query_str = f"""
        Resources
        | where subscriptionId == '{subscription_id}'
        | where type == 'microsoft.compute/disks' and isnull(managedBy) and properties.diskState == 'Unattached'
        | summarize count() by type='Orphaned Disks'
        | union (
            Resources
            | where subscriptionId == '{subscription_id}'
            | where type == 'microsoft.network/networkinterfaces' and isnull(properties.virtualMachine.id)
            | summarize count() by type='Orphaned NICs'
        )
        | union (
            Resources
            | where subscriptionId == '{subscription_id}'
            | where type == 'microsoft.network/publicipaddresses' and isnull(properties.ipConfiguration.id)
            | summarize count() by type='Orphaned PIPs'
        )
        | union (
            ResourceContainers
            | where type == 'microsoft.resources/subscriptions/resourcegroups' and subscriptionId == '{subscription_id}'
            | join kind=leftouter (
                Resources | where subscriptionId == '{subscription_id}' | project resourceGroup
            ) on $left.name == $right.resourceGroup
            | where isnull(resourceGroup1)
            | summarize count() by type='Empty RGs'
        )
        | summarize total_orphans = sum(count_)
        """
        query = QueryRequest(subscriptions=[subscription_id], query=query_str)
        query_response = resource_graph_client.resources(query)
        if query_response.data and len(query_response.data) > 0:
            total_orphans = query_response.data[0].get('total_orphans', 0)
    except Exception as e:
        current_app.logger.error(f"Dashboard: Failed to get orphan counts: {e}")
    return {"count": total_orphans}

def _get_resource_counts(credential, subscription_id):
    """Fetches resource counts by category."""
    counts = {"Compute": 0, "Storage": 0, "Network": 0, "Database": 0, "Other": 0}
    try:
        resource_graph_client = ResourceGraphClient(credential)
        query_str = f"""
        Resources
        | where subscriptionId == '{subscription_id}'
        | extend category = case(
            type has 'microsoft.compute/virtualmachines', 'Compute',
            type has 'microsoft.storage', 'Storage',
            type has 'microsoft.network', 'Network',
            type has 'microsoft.sql' or type has 'microsoft.documentdb', 'Database',
            'Other'
        )
        | summarize count() by category
        """
        query = QueryRequest(subscriptions=[subscription_id], query=query_str)
        query_response = resource_graph_client.resources(query)
        for item in query_response.data:
            if item.get('category') in counts:
                counts[item.get('category')] = item.get('count_')
    except Exception as e:
        current_app.logger.error(f"Dashboard: Failed to get resource counts: {e}")
    return counts

def _get_top_recommendations(credential, subscription_id):
    """Fetches top recommendations and counts by category."""
    insights = {
        "Cost": {"count": 0, "top_item": "No cost savings found."},
        "Security": {"count": 0, "top_item": "No security issues found."},
        "Reliability": {"count": 0, "top_item": "No reliability issues found."}
    }
    try:
        token = credential.get_token("https://management.azure.com/.default")
        headers = {"Authorization": f"Bearer {token.token}", "Content-Type": "application/json"}
        
        cost_url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Advisor/recommendations?api-version=2023-01-01&$filter=Category eq 'Cost'"
        cost_res = requests.get(cost_url, headers=headers).json().get('value', [])
        if cost_res:
            insights["Cost"]["count"] = len(cost_res)
            top_cost = next((r for r in cost_res if r.get('properties', {}).get('extendedProperties', {}).get('savingsAmount', '0') != '0'), cost_res[0])
            props = top_cost.get('properties', {})
            savings = props.get('extendedProperties', {}).get('savingsAmount', '0')
            desc = props.get('shortDescription', {}).get('problem', 'N_A')
            insights["Cost"]["top_item"] = f"{desc} (Est. ${savings})"

        sec_url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Advisor/recommendations?api-version=2023-01-01&$filter=Category eq 'Security'"
        sec_res = requests.get(sec_url, headers=headers).json().get('value', [])
        if sec_res:
            insights["Security"]["count"] = len(sec_res)
            desc = sec_res[0].get('properties', {}).get('shortDescription', {}).get('problem', 'N/A')
            insights["Security"]["top_item"] = desc
            
        rel_url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Advisor/recommendations?api-version=2023-01-01&$filter=Category eq 'HighAvailability'"
        rel_res = requests.get(rel_url, headers=headers).json().get('value', [])
        if rel_res:
            insights["Reliability"]["count"] = len(rel_res)
            desc = rel_res[0].get('properties', {}).get('shortDescription', {}).get('problem', 'N/A')
            insights["Reliability"]["top_item"] = desc
            
    except Exception as e:
        current_app.logger.error(f"Dashboard: Failed to get top recommendations: {e}")
    
    return insights

# --- NEW FUNCTION TO RUN THE PARALLEL CALLS ---
def _fetch_all_dashboard_data(credential, subscription_id):
    """
    This is the core logic that runs all 7 API calls in parallel.
    This is what we will cache.
    """
    current_app.logger.info(f"CACHE MISS. Re-fetching all dashboard data for sub {subscription_id}")
    with ThreadPoolExecutor(max_workers=7) as executor:
        f_advisor_scores = executor.submit(_get_advisor_scores, credential, subscription_id)
        f_defender_score = executor.submit(_get_security_score, credential, subscription_id)
        f_carbon = executor.submit(_get_carbon_summary, credential, subscription_id)
        f_orphans = executor.submit(_get_orphan_counts, credential, subscription_id)
        f_res_counts = executor.submit(_get_resource_counts, credential, subscription_id)
        f_insights = executor.submit(_get_top_recommendations, credential, subscription_id)
        f_monitoring = executor.submit(_get_monitoring_status_data, subscription_id)

        # Retrieve the results
        waf_scores = f_advisor_scores.result()
        defender_score = f_defender_score.result()
        carbon_summary = f_carbon.result()
        orphan_counts = f_orphans.result()
        resource_counts = f_res_counts.result()
        top_insights = f_insights.result()
        monitoring_data = f_monitoring.result()

    # Combine the two security scores
    waf_scores["security"]["score"] = defender_score.get("percentage", 0)
    
    dashboard_data = {
        "waf_scores": waf_scores,
        "kpis": {
            "carbon": carbon_summary,
            "orphans": orphan_counts
        },
        "insights": top_insights,
        "resource_counts": resource_counts,
        "monitoring_alerts": monitoring_data.get("alerts", [])
    }
    
    # --- Store the result in the cache with a timestamp ---
    with _cache_lock:
        _cache[subscription_id] = {
            "timestamp": time.time(),
            "data": dashboard_data
        }
        
    return dashboard_data


# --- Main API Endpoint ---
# THIS IS THE ONLY ROUTE, NOW MODIFIED TO USE THE CACHE
@dashboard_bp.route("/<subscription_id>", methods=["GET"])
def get_dashboard_data(subscription_id):
    """
    Aggregator endpoint for the main Azure dashboard.
    This now uses a thread-safe, time-based in-memory cache.
    """
    credential = DefaultAzureCredential()
    
    # --- CHECK CACHE FIRST ---
    with _cache_lock:
        cached_entry = _cache.get(subscription_id)
        if cached_entry:
            age = time.time() - cached_entry["timestamp"]
            if age < CACHE_TTL_SECONDS:
                current_app.logger.info(f"CACHE HIT. Serving dashboard data for sub {subscription_id} (age: {age:.0f}s)")
                return jsonify(cached_entry["data"])
            else:
                current_app.logger.info(f"CACHE STALE. (age: {age:.0f}s)")
        else:
            current_app.logger.info(f"CACHE MISS. No data for sub {subscription_id}")

    # --- If CACHE MISS or STALE, re-fetch ---
    # The _fetch_all_dashboard_data function handles running all
    # 7 calls in parallel AND updates the cache itself.
    try:
        data = _fetch_all_dashboard_data(credential, subscription_id)
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Failed to fetch and cache dashboard data: {str(e)}")
        return jsonify({"error": "Failed to retrieve dashboard data", "details": str(e)}), 500