from flask import Blueprint, jsonify
from dotenv import load_dotenv
import logging
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import SubscriptionClient

# Load .env file
load_dotenv()

# Blueprint
account_bp = Blueprint('api_account', __name__, url_prefix='/api/azure')

@account_bp.route("/subscriptions/", methods=["GET"])
def get_subscriptions():
    logger = logging.getLogger("azure.identity")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    credential = DefaultAzureCredential()
    subscription_client = SubscriptionClient(credential=credential)
    results = []
    for sub in subscription_client.subscriptions.list():
        results.append({
            "display_name": sub.display_name,
            "subscription_id": sub.subscription_id
        })
    return jsonify({"subscriptions": results})

@account_bp.route("/tenants/", methods=["GET"])
def get_tenants():
    credential = DefaultAzureCredential()
    subscription_client = SubscriptionClient(credential=credential)
    tenants = []
    for tenant in subscription_client.tenants.list():
        tenants.append({
            "tenant_id": tenant.tenant_id,
            "display_name": tenant.display_name if hasattr(tenant, 'display_name') else tenant.tenant_id
        })
    return jsonify({"tenants": tenants})