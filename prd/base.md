## Abstract

The Intelligent CloudOne Portal is a unified platform designed to address the
complexities of cloud computing management, focusing on cost optimization, resource
utilization, operational efficiency, and sustainability. By integrating key metrics from
cost, performance, and environmental impact, the portal leverages artificial intelligence
(AI) to provide actionable insights and recommendations. This enables organizations to
optimize cloud resources economically while promoting environmental responsibility.
This dissertation project emphasizes sustainable computing (Green IT) to minimize
energy consumption and carbon emissions; CloudOps for managing infrastructure
across platforms like Azure (as the primary focus), AWS, and GCP; AI/ML for analyzing
usage patterns and generating optimization strategies; and data analytics/visualization
for interactive dashboards.
The background highlights the gap in existing tools that overlook sustainability alongside
cost and performance. The CloudOne Portal fills this void using predictive analytics on
Azure as the initial provider, with extensibility planned for others.
Objectives include designing the portal as a proof-of-concept integrating cost data,
performance metrics, and sustainability indicators; implementing an AI-driven
recommendation engine for forecasting, resource identification, and optimizations;
creating intuitive dashboards; and incorporating smart CloudOps features like intelligent
migration and monitoring.
The scope is a functional prototype on Azure, developed with HTML/CSS for frontend,
Python Flask for backend API to fetch Azure data, and Google APIs for AI integration.
This mid-semester report outlines progress on modules, architecture, specifications,
design considerations, future plans, and work status.


## Modules in CloudOne Solution
The CloudOne Portal is structured into modular components to ensure scalability,
maintainability, and focused functionality. Each module aligns with the core objectives
of integrating cost, performance, and sustainability metrics, primarily using Azure as the
cloud provider. The modules are as follows:
• Data Ingestion Module: Responsible for fetching real-time and historical data from
Azure services via the backend Python Flask API. This includes cost data from Azure
Cost Management API, performance metrics from Azure Monitor, and
sustainability indicators from Azure Sustainability Calculator (e.g., carbon emissions
estimates based on resource usage). Data is pulled securely using Azure SDK for
Python, with authentication via Azure Active Directory
• AI Recommendation Engine Module: Utilizes Google APIs (e.g., Google Cloud AI or
Vertex AI) for machine learning models. This module analyzes ingested data to
forecast resource demand, identify underutilized instances (e.g., idle VMs in
Azure), and recommend actions like rightsizing Azure Virtual Machines, workload
migration to energy-efficient regions, or rescheduling for off-peak hours.
Recommendations quantify benefits in cost savings (e.g., percentage reduction),
performance improvements (e.g., latency metrics), and carbon footprint reduction
(e.g., CO2e savings).
• Visualization Dashboard Module: Built with HTML/CSS for the frontend, this
module presents interactive dashboards using libraries like Chart.js or D3.js
integrated via Flask. It displays KPIs such as overall sustainability score, carbon
emissions trends, resource utilization graphs, and cost breakdowns. Users can filter
views by Azure resource groups or subscriptions.
• Smart CloudOps Module: Includes features for intelligent operations on Azure,
such as automated monitoring with Azure Alerts, resource provisioning via
Infrastructure as Code (IaC) using auto generated Terraform modules (integrated
through Flask backend), and migration tools leveraging Azure Migrate API. This
module supports hybrid scenarios but focuses on Azure-native optimizations.


## Highlighted features:

• Terraform Module Generator: Automates Infrastructure as Code (IaC) creation
using Terraform for Azure resources, integrated via the Flask backend to generate
configuration files for provisioning and management.
• Orphan/Unused Resources Finder: Identifies idle or underutilized Azure resources
(e.g., stopped VMs, unused storage) through Azure Resource Graph API, enabling
cost and energy savings.
• Cloud Carbon Emission and Footprint: Calculates and tracks carbon emissions and
sustainability metrics using Azure Sustainability Calculator data, processed via Flask
to provide actionable insights.
• Cloud Smart Monitoring: Implements real-time monitoring of Azure resources
using Azure Monitor API, delivering performance and utilization data to the
frontend dashboards.
• Policy Generator: Creates and manages Azure policies via Flask API calls to Azure
Policy API, ensuring compliance with sustainability and cost optimization rules.
• Migration Bots: Facilitates intelligent migration of workloads to Azure using Azure
Migrate API, optimizing for energy-efficient regions and performance.
• Environment Security Score: Assesses security posture of Azure environments
using Azure Security Center data, visualized on dashboards for informed decisionmaking.
• Quick Heal - TShoot and Fix: Provides automated troubleshooting and remediation
scripts for Azure issues, integrated via Flask to execute fixes like resource resizing.
• Cost Center and Optimizer: Analyzes Azure Cost Management data to identify
savings opportunities, recommending rightsizing or shutdowns with quantified
benefits.
• Code Repos and Pipeline Management: Manages Azure DevOps repositories and
CI/CD pipelines via Flask API, ensuring automated deployment and version control
of CloudOne features.

## Major Technical Specification
• Frontend: HTML/CSS-based UI with dashboards and user interfaces.
• Backend: Python Flask API handling data fetching, processing, and AI integration.
• AI Integration:
a. Azure APIs (Cost Management, Monitor, Sustainability, Resource Graph, etc.).
b. Cloud AI APIs (e.g., Vertex AI) for forecasting models, trained on Azure data.
Data Sources:
• Azure Cost Management API: Billing data.
• Azure Monitor: Performance metrics.
• Azure Sustainability Calculator: Emissions data.
• Azure Resource Graph API: Resource inventory.
• Azure Security Center: Security scores etc.
Database: MySQL or Azure SQL Database.
Deployment: Currently Locally in Device. Can be deployed in Server, WebApp or container
environments.
Security: SPN based authentication with Cloud Platform; API rate limiting.

## Functional Architecture Diagram and Description

### Data Flow
1. User logs in via frontend → Flask authenticates with Azure using SPN.
2. Flask API queries Azure APIs for data → Ingests metrics like Cost, Emissions,
Monitor, Sustainability, Resource Graph and Security scores.
3. Data is processed and sent to Google API for AI analysis → Generates
recommendations.
4. Results are visualized on frontend dashboards.
5. Smart CloudOps modules (e.g., Terraform Generator, Migration Bots) generate IaC
resources, migration solutions and trigger actions if approved.
Description
The functional architecture uses a modular design, with Flask as the orchestrator. The
Backend uses Python flask API. Data flows from Cloud Platforms using Cloud/Azure
APIs through secure calls, processed in-memory or cached to reduce latency.
Few of the recommendations are generated as per defined algorithm. Further, AI
integration with AI/LLM like Google APIs occurs via RESTful calls for predictive
analytics. AI Models can be further fine-tuned using RAG/Knowledge base. The
frontend renders responsive views using HTML/CSS.
This design supports future multi-cloud expansion by abstracting provider-specific
APIs.
5. Design Consideration
• Sustainability Focus: Optimizes API calls and selects Azure resources with
sustainable usages.
• User-Centric Design: Accessible user-friendly UI portal.
• Scalability: Modular Flask code for multi-cloud support.
• Error Handling: Try-except for API failures; cached fallbacks.
• Integration Challenges: Handles Google quotas and Azure limits with backoff
strategies.
• Prototyping Constraints: Azure focus enables deep integration; HTML/CSS keeps
frontend simple.
6. Current Status and Future Plans
Progress has been made on the foundational components of the portal, focusing on
environment setup and core data integration. The current status is as follows:
8
• Environment Setup: The primary development environment on Azure is fully
configured. This includes the necessary services and infrastructure to host the
portal's backend API and frontend.
• Authentication and Authorization: The Azure Service Principal (SPN) for the
application has been successfully created and granted the required permissions.
The authentication mechanism for the backend to securely access the Azure
environment is now fully functional.
• User Interface (UI) Development: The core structure of the web portal has been
built. The basic landing page, a multi-cloud overview page, and a dedicated Azure
landing page are all complete, providing the initial framework for user navigation.
• Azure Data Ingestion: The backend API's ability to communicate with the Azure
platform is confirmed. Azure API calls are successfully fetching key data, including
tenant information, subscription details, and a comprehensive list of all resources.
• AI Integration: The intelligent core of the portal is now connected. The backend has
been successfully integrated with Google AI and Grok APIs, laying the groundwork
for future predictive and generative AI features.
• Core Feature Development: Several key features are already operational in a
prototype state:
o My Resources: A basic module that lists and displays the user's resources
from their Azure subscription.
o Unused Resource Finder: A functional module that identifies and flags
resources that are currently not in use, a key step towards cost
optimization.
o Migration Services: Preliminary services for cloud migration are working,
demonstrating the portal's operational capabilities.