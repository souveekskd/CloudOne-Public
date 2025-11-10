from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)

@views_bp.route("/")
def index():
    return render_template("index.html")

@views_bp.route("/orphaned_resources")
def orphaned_resources():
    return render_template("orphaned_resources.html")

@views_bp.route("/cloud_providers")
def cloud_providers():
    return render_template("cloud_providers.html")

@views_bp.route("/azure_landing")
def azure_landing():
    return render_template("azure_landing.html")

@views_bp.route("/my_resources")
def my_resources():
    return render_template("my_resources.html")

@views_bp.route("/environment_security_score")
def environment_security_score():
    return render_template("environment_security_score.html")

@views_bp.route("/migration_bot")
def migration_bot():
    return render_template("migration_bot.html")

@views_bp.route("/terraform_generator")
def terraform_generator():
    # It now serves the new, renamed template file.
    return render_template("iac_generator.html")

@views_bp.route("/advisor_recommendations")
def advisor_recommendations():
    return render_template("advisor_recommendations.html")

@views_bp.route("/policy_manager")
def policy_manager():
    return render_template("policy_manager.html")

# --- ADD THIS NEW ROUTE ---
@views_bp.route("/resource_optimization")
def resource_optimization():
    return render_template("resource_optimization.html")
@views_bp.route("/carbon_footprint")
def carbon_footprint():
    return render_template("carbon_footprint.html")

# --- ADD THIS NEW ROUTE ---
@views_bp.route("/smart_monitoring")
def smart_monitoring():
    return render_template("smart_monitoring.html")
