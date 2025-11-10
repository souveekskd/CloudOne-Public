import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# Get a logger for this module
app_logger = logging.getLogger(__name__)

#
# --- THIS IS THE OLD, RENAMED FUNCTION ---
#
def get_terraform_code(module_type, resources):
    """
    Generates Terraform project structure.
    This is the original function, now nested.
    """
    # Helper function to get the resource "short name" (e.g., "vnet")
    def get_short_name(resource_type):
        return resource_type.replace('azurerm_', '').replace('_', '-')

    # --- The "Custom" prompt: Root module + local child modules using "resource" blocks ---
    if module_type == 'custom':
        system_prompt = f"""You are a Terraform Solution Architect.
Your task is to generate a complete, professional Terraform project structure for the user.
The project must have a root module and a separate local child module for *each* resource requested.

Your response MUST be in a single, valid JSON object with this exact nested structure:
{{
  "root": {{
    "provider.tf": "...",
    "main.tf": "...",
    "variables.tf": "...",
    "outputs.tf": "..."
  }},
  "modules": {{
    "resource-short-name-1": {{
      "main.tf": "...",
      "variables.tf": "...",
      "outputs.tf": "..."
    }},
    "resource-short-name-2": {{
      "main.tf": "...",
      "variables.tf": "...",
      "outputs.tf": "..."
    }}
  }}
}}

INSTRUCTIONS:
1.  **root/provider.tf**: Must contain the 'terraform' block and 'azurerm' provider block.
2.  **root/main.tf**: Must contain `module` calls for *each* child module. It should wire them together (e.g., pass the root `resource_group_name` to each module).
3.  **root/variables.tf**: Must define common variables (like `resource_group_name`, `location`).
4.  **root/outputs.tf**: Must pass through the most important outputs from each child module.
5.  **modules/<name>/main.tf**: Must contain the `resource "azurerm_..."` block for that specific resource.
6.  **modules/<name>/variables.tf**: Must define the variables needed for that resource.
7.  **modules/<name>/outputs.tf**: Must output the key attributes of that resource (id, name, etc.).
"""
        user_prompt = f"Generate the 'Custom' module project for these resources: {', '.join(resources)}"

    # --- The "AVM" prompt: Root module + local child modules that *wrap* AVMs ---
    else:
        system_prompt = f"""You are a Terraform Solution Architect who *strictly* uses Azure Verified Modules (AVM).
Your task is to generate a complete, professional Terraform project structure.
The project must have a root module and a separate local child module for *each* resource. This child module will *wrap* the official AVM.
Your knowledge base for AVMs is: https://azure.github.io/Azure-Verified-Modules/indexes/terraform/tf-resource-modules/

Your response MUST be in a single, valid JSON object with this exact nested structure:
{{
  "root": {{
    "provider.tf": "...",
    "main.tf": "...",
    "variables.tf": "...",
    "outputs.tf": "..."
  }},
  "modules": {{
    "resource-short-name-1": {{
      "main.tf": "...",
      "variables.tf": "...",
      "outputs.tf": "..."
    }},
    "resource-short-name-2": {{
      "main.tf": "...",
  
      "variables.tf": "...",
      "outputs.tf": "..."
    }}
  }}
}}

INSTRUCTIONS:
1.  **root/provider.tf**: Must contain the 'terraform' block and 'azurerm' provider block.
2.  **root/main.tf**: Must contain `module` calls for *each* local child module (e.g., `source = "./modules/vnet"`).
3.  **root/variables.tf**: Must define common variables (like `resource_group_name`, `location`).
4.  **root/outputs.tf**: Must pass through the outputs from each child module.
5.  **modules/<name>/main.tf**: Must contain a `module "avm_..."` block that calls the *official* AVM from the registry (e.g., `source = "Azure/avm-res-network-virtualnetwork/azurerm"`).
6.  **modules/<name>/variables.tf**: Must define variables to pass into the AVM module block.
7.  **modules/<name>/outputs.tf**: Must pass through the outputs from the AVM module block.
"""
        user_prompt = f"Generate the 'AVM' wrapper module project for these resources: {', '.join(resources)}"

    try:
        model = genai.GenerativeModel(
            # --- CHANGE 1 ---
            model_name="gemini-2.5-flash", # Was gemini-1.5-flash
            system_instruction=system_prompt
        )
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        response = model.generate_content(
            user_prompt,
            generation_config=generation_config
        )
        response_content = response.text
        # This is the Terraform project structure
        return json.loads(response_content)
    except Exception as e:
        app_logger.error(f"Error calling Gemini API for Terraform: {e}")
        return {"error": f"Failed to get AI recommendation: {str(e)}"}

#
# --- ADD THIS NEW BICEP PROMPT ---
#
def get_bicep_code(resources):
    """
    Generates a single, comprehensive main.bicep file.
    """
    system_prompt = """You are an expert Azure Bicep developer.
Your task is to generate a single, complete `main.bicep` file based on a list of requested Azure resources.

INSTRUCTIONS:
1.  The entire response MUST be a single, valid JSON object with one key: "main.bicep".
2.  The value of "main.bicep" must be a string containing the complete Bicep code.
3.  Include `@description` decorators for all parameters and resources.
4.  Define common parameters at the top, like `location` and `resourceGroupName`.
5.  Use Bicep resource loops (`for`) for any resources that are commonly deployed in groups (like subnets or VMs).
6.  Intelligently link resources (e.g., pass the VNet name to the subnet, pass the NIC ID to the VM).
7.  Generate a few meaningful `output` variables at the end.
8.  Do not include any text, markdown, or explanations outside of the JSON object.

Example Response:
{
  "main.bicep": "param location string = 'eastus'\\n\\nresource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {\\n  name: 'myResourceGroup'\\n  location: location\\n}\\n\\n// ... other resources ...\\n\\noutput vnetId string = vnet.id"
}
"""
    user_prompt = f"Generate the `main.bicep` file content for these Azure resources: {', '.join(resources)}. Include sensible defaults and wire them together."

    try:
        model = genai.GenerativeModel(
            # --- CHANGE 2 ---
            model_name="gemini-2.5-flash", # Was gemini-1.5-flash
            system_instruction=system_prompt
        )
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        response = model.generate_content(
            user_prompt,
            generation_config=generation_config
        )
        response_content = response.text
        return json.loads(response_content)
    except Exception as e:
        app_logger.error(f"Error calling Gemini API for Bicep: {e}")
        return {"error": f"Failed to get AI recommendation: {str(e)}"}

#
# --- ADD THIS NEW ARM PROMPT ---
#
def get_arm_code(resources):
    """
    Generates a single, comprehensive template.json file.
    """
    system_prompt = """You are an expert Azure ARM Template developer.
Your task is to generate a single, complete `template.json` file based on a list of requested Azure resources.

INSTRUCTIONS:
1.  The entire response MUST be a single, valid JSON object, representing the ARM template itself.
2.  The template must be well-formed JSON, starting with `{$schema: ...}`.
3.  Include `parameters`, `variables`, `resources`, and `outputs` sections.
4.  Define common parameters at the top, like `location`.
5.  Intelligently link resources using `dependsOn` and `resourceId()` functions.
6.  Generate a few meaningful `output` variables at the end.
7.  Do not include any text, markdown, or explanations outside of the main JSON template object.

Example Response:
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "location": {
      "type": "string",
      "defaultValue": "eastus"
    }
  },
  "resources": [
    {
      "type": "Microsoft.Storage/storageAccounts",
      "apiVersion": "2021-04-01",
      "name": "[concat('storage', uniqueString(resourceGroup().id))]",
      "location": "[parameters('location')]",
      "sku": {
        "name": "Standard_LRS"
      },
      "kind": "StorageV2"
    }
  ],
  "outputs": {
    "storageAccountId": {
      "type": "string",
      "value": "[resourceId('Microsoft.Storage/storageAccounts', concat('storage', uniqueString(resourceGroup().id)))]"
    }
  }
}
"""
    user_prompt = f"Generate the `template.json` for these Azure resources: {', '.join(resources)}. Include sensible defaults and wire them together."

    try:
        model = genai.GenerativeModel(
            # --- CHANGE 3 ---
            model_name="gemini-2.5-flash", # Was gemini-1.5-flash
            system_instruction=system_prompt
        )
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        response = model.generate_content(
            user_prompt,
            generation_config=generation_config
        )
        response_content = response.text
        # The response *is* the JSON, so we package it into our file format
        return {"template.json": response_content}
    except Exception as e:
        app_logger.error(f"Error calling Gemini API for ARM: {e}")
        return {"error": f"Failed to get AI recommendation: {str(e)}"}


#
# --- THIS IS THE NEW, REFACTORED MAIN FUNCTION ---
#
def get_iac_code(iac_type, module_type, resources):
    """
    Main service function to route IaC generation.
    """
    load_dotenv()
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in .env file")
        genai.configure(api_key=api_key)

    except Exception as e:
        app_logger.error(f"Failed to initialize Gemini client: {e}. Is GOOGLE_API_KEY set?")
        return {"error": "Failed to initialize AI client. Check server logs."}
    
    # This is the final JSON we will send to the frontend
    # It tells the frontend how to render the output
    response_payload = {
        "iac_type": iac_type,
        "files": {}
    }

    try:
        if iac_type == 'terraform':
            response_payload["files"] = get_terraform_code(module_type, resources)
        
        elif iac_type == 'bicep':
            # Bicep/ARM output is flat: {"main.bicep": "..."}
            response_payload["files"] = get_bicep_code(resources)

        elif iac_type == 'arm':
            # ARM output is flat: {"template.json": "..."}
            files = get_arm_code(resources)
            if "template.json" in files:
                # The LLM returns a JSON string, we must parse and re-dump it to format it nicely
                pretty_json = json.dumps(json.loads(files["template.json"]), indent=4)
                response_payload["files"] = {"template.json": pretty_json}
            else:
                response_payload["files"] = files # Pass on error

        else:
            return {"error": "Invalid IaC type specified."}

        # Check if the sub-function returned an error
        if "error" in response_payload["files"]:
            return response_payload["files"]

        return response_payload

    except Exception as e:
        app_logger.error(f"Failed to generate IaC: {str(e)}")
        return {"error": str(e)}

#
# --- (Keep your other functions like get_migration_recommendation and get_ai_remediation) ---
#
def get_migration_recommendation(prompt):
    load_dotenv()
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in .env file")
        genai.configure(api_key=api_key)

    except Exception as e:
        app_logger.error(f"Failed to initialize Gemini client: {e}. Is GOOGLE_API_KEY set?")
        return {"error": "Failed to initialize AI client. Check server logs."}

    system_prompt = """You are an expert Azure Cloud Solution Architect specializing in migration.
You will be given details of an on-premises environment and a target migration strategy.
Your response MUST be in a single, valid JSON object with the following exact structure:

{
  "strategy_name": "The formal name for this migration (e.g., 'Rehost to Azure VM', 'Replatform to Azure App Service').",
  "target_platform": "The target platform (IaaS, PaaS, or Container).",
  "compute_recommendation": {
    "resource_type": "e.g., 'Virtual Machine', 'App Service Plan', 'AKS Node Pool'",
    "recommended_sku": "The single, specific, billable Azure SKU (e.g., 'Standard_D4s_v5', 'P2v3').",
    "estimated_hourly_price_payg": 0.0
  },
  "database_recommendation": {
    "analysis": "A brief analysis of the user's DB requirement.",
    "resource_type": "e.g., 'Azure SQL Database', 'Azure VM (SQL Server)', 'None'",
    "recommended_sku": "The specific SKU or tier (e.g., 'S3', 'GP_Gen5_4', 'Standard_E4s_v5'). If none, put 'N/A'.",
    "estimated_hourly_price_payg": 0.0
  },
  "resource_list": [
    "A list of all *other* Azure resources required (e.g., 'Virtual Network', 'OS Disk', 'NSG')."
  ],
  "migration_steps": [
    "A concise, step-by-step guide for the migration."
  ],
  "integration_notes": "Provide high-level notes on handling integrations. If none mentioned, say 'No integration notes provided.'"
}

Provide *your best estimate* for the hourly_price_payg in USD based on public pricing.
Do not add any text or markdown outside of this JSON object.
"""
    user_prompt = prompt

    try:
        model = genai.GenerativeModel(
            # --- CHANGE 4 ---
            model_name="gemini-2.5-flash", # Was gemini-1.5-flash
            system_instruction=system_prompt
        )
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        response = model.generate_content(
            user_prompt,
            generation_config=generation_config
        )
        response_content = response.text
        return json.loads(response_content)
    except Exception as e:
        app_logger.error(f"Error calling Gemini API: {e}")
        return {"error": f"Failed to get AI recommendation: {str(e)}"}

def get_ai_remediation(problem_description):
    """
    Calls Gemini to get step-by-step remediation instructions.
    """
    load_dotenv()
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in .env file")
        genai.configure(api_key=api_key)
    except Exception as e:
        app_logger.error(f"Failed to initialize Gemini client: {e}.")
        return {"error": "Failed to initialize AI client. Check server logs."}

    system_prompt = '''You are an expert Azure Cloud Support Engineer. 
    You will be given an Azure Advisor recommendation. 
    Your task is to provide a detailed, step-by-step guide on how to remediate this issue. 
    Format the response clearly using markdown. Use numbered lists for steps and code blocks for any commands or scripts.'''
    
    user_prompt = f"Please provide a step-by-step remediation guide for this Azure Advisor recommendation: '{problem_description}'"

    try:
        model = genai.GenerativeModel(
            # --- CHANGE 5 ---
            model_name="gemini-2.5-flash", # Was gemini-1.5-flash
            system_instruction=system_prompt
        )
        
        response = model.generate_content(user_prompt)
        
        # We are returning plain text (markdown)
        return {"remediation_steps": response.text}
    except Exception as e:
        app_logger.error(f"Error calling Gemini API for remediation: {e}")
        return {"error": f"Failed to get AI remediation: {str(e)}"}
