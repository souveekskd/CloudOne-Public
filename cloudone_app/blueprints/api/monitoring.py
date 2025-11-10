from flask import Blueprint, jsonify, current_app
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest
import logging

# Load .env file
load_dotenv()

# Blueprint
monitoring_bp = Blueprint('api_monitoring', __name__, url_prefix='/api/azure/monitoring')

def _get_monitoring_status_data(subscription_id):
    """
    Internal function to fetch and process monitoring data.
    This can be called by the dashboard API to get alerts.
    """
    credential = DefaultAzureCredential()
    resource_graph_client = ResourceGraphClient(credential)

    # This Kusto query is the core of the feature.
    # It fetches VMs and App Services, joins for power state, and projects tags.
    # Note: VM powerState is in properties.extended.instanceView.powerState.code
    # Note: App Service state is in properties.state
    query_str = f"""
    Resources
    | where subscriptionId == '{subscription_id}'
    | where type in~ ('microsoft.compute/virtualmachines', 'microsoft.web/sites')
    | extend powerState = case(
        type =~ 'microsoft.compute/virtualmachines', tostring(properties.extended.instanceView.powerState.code),
        type =~ 'microsoft.web/sites', tostring(properties.state),
        'N/A'
    )
    | project id, name, type, location, resourceGroup, tags, powerState
    """
    
    query = QueryRequest(subscriptions=[subscription_id], query=query_str)
    query_response = resource_graph_client.resources(query)
    
    results = {
        "alerts": [],
        "monitored": [],
        "notConfigured": []
    }

    if not query_response.data:
        return results

    for resource in query_response.data:
        tags = resource.get('tags', {})
        # Tag matching is case-insensitive, but keys are case-sensitive. Let's normalize.
        normalized_tags = {k.lower(): v for k, v in tags.items()}
        
        monitor_tag = normalized_tags.get('monitor', 'notset').lower()
        criticality_tag = normalized_tags.get('criticality', 'notset').lower()
        
        # Standardize power state
        power_state = resource.get('powerState', 'N/A').lower()
        
        if 'deallocated' in power_state: power_state = 'Deallocated'
        elif 'stopped' in power_state: power_state = 'Stopped'
        elif 'running' in power_state: power_state = 'Running'
        else: power_state = 'Other'


        item = {
            "name": resource['name'],
            "type": resource['type'],
            "location": resource['location'],
            "resourceGroup": resource['resourceGroup'],
            "powerState": power_state,
            "monitorTag": monitor_tag,
            "criticalityTag": criticality_tag
        }

        # Task 1: Check for "Monitor Disable" or no "Monitor" tag
        if monitor_tag in ('disable', 'notset', 'no'):
            results["notConfigured"].append(item)
            continue
        
        # From here, we assume monitor_tag is 'enable' or similar
        item['monitorTag'] = 'enabled' # Normalize
        
        # Task 2: High Criticality check
        if criticality_tag == 'high':
            if power_state in ('Stopped', 'Deallocated', 'Other'):
                item['alertLevel'] = 'High'
                item['alertReason'] = f"High criticality resource is {power_state}."
                results["alerts"].append(item)
            else:
                results["monitored"].append(item)
        
        # Task 3: Medium Criticality check
        elif criticality_tag == 'medium':
            if power_state in ('Stopped', 'Deallocated', 'Other'):
                item['alertLevel'] = 'Medium'
                item['alertReason'] = f"Medium criticality resource is {power_state}."
                results["alerts"].append(item)
            else:
                results["monitored"].append(item)
        
        else:
            # Low criticality or monitored resources without issues
            results["monitored"].append(item)
            
    return results

@monitoring_bp.route("/status/<subscription_id>", methods=["GET"])
def get_monitoring_status(subscription_id):
    """
    API endpoint to fetch the full monitoring status for the Smart Monitoring page.
    """
    try:
        data = _get_monitoring_status_data(subscription_id)
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Failed to fetch monitoring status: {str(e)}")
        return jsonify({"error": str(e)}), 500
