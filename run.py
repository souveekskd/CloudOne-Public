from cloudone_app import create_app

# Create the app instance using the factory
app = create_app()

if __name__ == "__main__":
    # Use the app's config to run, which will load from .env
    app.run(
        debug=app.config.get("DEBUG", True),
        host=app.config.get("HOST", "0.0.0.0"),
        port=app.config.get("PORT", 5000)
    )
