from flask import Blueprint, jsonify, current_app
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest

# Load .env file
load_dotenv()

# Blueprint
resources_bp = Blueprint('api_resources', __name__, url_prefix='/api/azure')

@resources_bp.route("/resources/<subscription_id>", methods=["GET"])
def get_resources(subscription_id):
    credential = DefaultAzureCredential()
    resource_client = ResourceManagementClient(credential=credential, subscription_id=subscription_id)
    resources = []
    for resource in resource_client.resources.list():
        resources.append({
            "name": resource.name,
            "type": resource.type,
            "location": resource.location,
            "status": "Active" if resource.properties else "Unknown"
        })
    return jsonify({"resources": resources})

@resources_bp.route("/orphans/<subscription_id>", methods=["GET"])
def get_orphans(subscription_id):
    credential = DefaultAzureCredential()
    try:
        resource_graph_client = ResourceGraphClient(credential)

        disk_query = f"""
        Resources
        | where subscriptionId == '{subscription_id}'
        | where type == 'microsoft.compute/disks'
        | where isnull(managedBy) and properties.diskState == 'Unattached'
        | project name, type, location, resourceGroup, id
        """
        
        nic_query = f"""
        Resources
        | where subscriptionId == '{subscription_id}'
        | where type == 'microsoft.network/networkinterfaces'
        | where isnull(properties.virtualMachine.id)
        | project name, type, location, resourceGroup, id
        """
        
        pip_query = f"""
        Resources
        | where subscriptionId == '{subscription_id}'
        | where type == 'microsoft.network/publicipaddresses'
        | where isnull(properties.ipConfiguration.id)
        | project name, type, location, resourceGroup, id
        """
        
        nsg_query = f"""
        Resources
        | where subscriptionId == '{subscription_id}'
        | where type == 'microsoft.network/networksecuritygroups'
        | where isnull(properties.subnets) and isnull(properties.networkInterfaces)
        | project name, type, location, resourceGroup, id
        """

        rg_query = f"""
        ResourceContainers
        | where type == 'microsoft.resources/subscriptions/resourcegroups' and subscriptionId == '{subscription_id}'
        | project rgName = name, rgId = id, rgLocation = location, resourceGroup = name
        | join kind=leftouter (
            Resources
            | where subscriptionId == '{subscription_id}'
            | project resourceGroup
        ) on $left.rgName == $right.resourceGroup
        | where isnull(resourceGroup1)
        | distinct rgName, rgId, rgLocation, resourceGroup
        | project name = rgName, type='Microsoft.Resources/resourceGroups (Empty)', location = rgLocation, resourceGroup, id = rgId
        """

        queries = {
            "disks": disk_query,
            "nics": nic_query,
            "pips": pip_query,
            "nsgs": nsg_query,
            "rgs": rg_query  # <-- Corrected variable name
        }
        
        results = { "disks": [], "nics": [], "pips": [], "nsgs": [], "rgs": [] }

        for key, query_str in queries.items():
            if key == 'rgs':
                query_options = None 
            else:
                query_options = None 

            query = QueryRequest(subscriptions=[subscription_id], query=query_str, options=query_options)
            query_response = resource_graph_client.resources(query)
            
            for item in query_response.data:
                results[key].append({
                    "name": item.get('name'),
                    "type": item.get('type'),
                    "location": item.get('location'),
                    "resource_group": item.get('resourceGroup'),
                    "id": item.get('id')
                })
                
        return jsonify(results)

    except Exception as e:
        current_app.logger.error(f"Failed to fetch orphans: {str(e)}")
        return jsonify({"error": str(e)}), 500