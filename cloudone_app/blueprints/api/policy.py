from flask import Blueprint, jsonify, current_app, request
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource.policy import PolicyClient
from azure.mgmt.resource import ResourceManagementClient
import uuid

# Load .env file
load_dotenv()

# Blueprint
policy_bp = Blueprint('api_policy', __name__, url_prefix='/api/azure/policy')

@policy_bp.route("/assignments/<subscription_id>", methods=["GET"])
def get_policy_assignments(subscription_id):
    """
    Fetches all policy assignments for the given subscription.
    (Tab 1)
    """
    credential = DefaultAzureCredential()
    policy_client = PolicyClient(credential, subscription_id)
    
    try:
        assignments_list = list(policy_client.policy_assignments.list())
        results = []
        
        for assignment in assignments_list:
            results.append({
                "name": assignment.name,
                "display_name": assignment.display_name,
                "scope": assignment.scope,
                "mode": assignment.enforcement_mode,
                "policy_definition_id": assignment.policy_definition_id
            })
            
        return jsonify({"assignments": results})

    except Exception as e:
        current_app.logger.error(f"Failed to fetch policy assignments: {str(e)}")
        return jsonify({"error": str(e)}), 500

@policy_bp.route("/caf_initiatives", methods=["GET"])
def get_caf_initiatives():
    """
    Returns an expanded static list of recommended CAF/ALZ Policy Initiatives.
    (Tab 2)
    """
    # Expanded list based on your references
    caf_policies = [
        {
            "display_name": "Enforce specified tags",
            "description": "Enforces a specific tag and value on resources. Good for CostCenter or AppName.",
            "definition_id": "/providers/Microsoft.Authorization/policyDefinitions/1e30110a-5ceb-460c-a204-c1c3969c6d62"
        },
        {
            "display_name": "Allowed locations",
            "description": "Restricts which Azure regions your organization can deploy resources into.",
            "definition_id": "/providers/Microsoft.Authorization/policyDefinitions/e56962a6-4747-49cd-b67b-bf8b01975c4c"
        },
        {
            "display_name": "Deny RDP access from the Internet",
            "description": "Audits or denies network security rules that allow RDP access from 'Any' or 'Internet'.",
            "definition_id": "/providers/Microsoft.Authorization/policyDefinitions/30201c19-1f4b-4c74-9b5a-5309b671c4c1"
        },
        {
            "display_name": "Deny SSH access from the Internet",
            "description": "Audits or denies network security rules that allow SSH access from 'Any' or 'Internet'.",
            "definition_id": "/providers/Microsoft.Authorization/policyDefinitions/e51bae91-21e0-4e97-8532-b02c0b568faf"
        },
        {
            "display_name": "Deny Public IP addresses on network interfaces",
            "description": "A core ALZ policy to ensure no public IPs are attached directly to VMs.",
            "definition_id": "/providers/Microsoft.Authorization/policyDefinitions/83a86a26-fd1f-447c-b59d-e51f44062112"
        },
        {
            "display_name": "Storage accounts should restrict network access",
            "description": "Ensures storage accounts are not open to the public internet.",
            "definition_id": "/providers/Microsoft.Authorization/policyDefinitions/34c877ad-507e-4c82-993e-3452a6e0ad3c"
        },
        {
            "display_name": "Key vaults should have soft delete enabled",
            "description": "Ensures all Key Vaults can be recovered from accidental deletion.",
            "definition_id": "/providers/Microsoft.Authorization/policyDefinitions/1e220e14-998A-4f0f-8025-24b4f6b2164c"
        },
        {
            "display_name": "Azure VMs should enable backup",
            "description": "Audits VMs that do not have Azure Backup enabled.",
            "definition_id": "/providers/Microsoft.Authorization/policyDefinitions/013e242c-8828-4970-87b3-ab247555486d"
        },
        {
            "display_name": "Enable Microsoft Defender for Cloud",
            "description": "Policy initiative to configure Microsoft Defender for Cloud (Standard) pricing.",
            "definition_id": "/providers/Microsoft.Authorization/policySetDefinitions/1f3afdf9-d0c9-4c3d-847f-89da613e70a8"
        },
        {
            "display_name": "Enable DDoS Protection Standard on Virtual Networks",
            "description": "Audits or enforces DDoS Protection Standard on all VNETs.",
            "definition_id": "/providers/Microsoft.Authorization/policyDefinitions/94de20c0-b0c5-4224-a9b7-3a18c1ecb391"
        },
        {
            "display_name": "Private endpoints should be used on PaaS services",
            "description": "Audits PaaS services that are not using private endpoints for enhanced security.",
            "definition_id": "/providers/Microsoft.Authorization/policySetDefinitions/739c9441-50e7-4003-8b27-66181b1f1f2a"
        },
        {
            "display_name": "Log Analytics agent should be installed on virtual machines",
            "description": "Audits for missing Log Analytics agents on both Windows and Linux VMs.",
            "definition_id": "/providers/Microsoft.Authorization/policySetDefinitions/5ab41f05-3a32-4f0e-8628-a28a9b2b2190"
        }
    ]
    return jsonify({"caf_policies": caf_policies})


@policy_bp.route("/create_assignment", methods=["POST"])
def create_policy_assignment():
    """
    Creates a new policy assignment at a specified scope.
    This is the "Apply" logic for Tab 2 and Tab 3.
    """
    data = request.get_json()
    subscription_id = data.get("subscription_id")
    policy_definition_id = data.get("policy_definition_id")
    assignment_scope = data.get("assignment_scope") # e.g., /subscriptions/YOUR_SUB_ID
    enforcement_mode = data.get("enforcement_mode") # "Default" (Enforced) or "DoNotEnforce" (Audit)
    policy_name = data.get("policy_name")

    if not all([subscription_id, policy_definition_id, assignment_scope, enforcement_mode, policy_name]):
        return jsonify({"error": "Missing required fields"}), 400

    credential = DefaultAzureCredential()
    policy_client = PolicyClient(credential, subscription_id)
    
    # Generate a unique name for the assignment
    assignment_name = str(uuid.uuid4())
    
    try:
        assignment = policy_client.policy_assignments.create(
            scope=assignment_scope,
            policy_assignment_name=assignment_name,
            parameters={
                "properties": {
                    "displayName": policy_name,
                    "policyDefinitionId": policy_definition_id,
                    "enforcementMode": enforcement_mode
                }
            }
        )
        
        return jsonify({
            "success": True,
            "name": assignment.name,
            "displayName": assignment.display_name,
            "scope": assignment.scope,
            "mode": assignment.enforcement_mode
        })

    except Exception as e:
        current_app.logger.error(f"Failed to create policy assignment: {str(e)}")
        return jsonify({"error": str(e)}), 500