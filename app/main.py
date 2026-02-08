from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine, Base, SessionLocal
from app.models import Flag, Environment, User, AuditLog  # Import models so they're registered
from app.routers import environments_router, flags_router, evaluate_router, auth_router, audit_router

# Create the FastAPI application instance
# This is the core object that handles all HTTP requests
app = FastAPI(
    title="Feature Flag Service",
    description="A feature flag and experimentation platform",
    version="0.1.0"
)

# Register routers
app.include_router(auth_router)
app.include_router(environments_router)
app.include_router(flags_router)
app.include_router(evaluate_router)
app.include_router(audit_router)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Dashboard - serve the HTML page
@app.get("/")
def serve_dashboard():
    """Serve the dashboard UI."""
    return FileResponse("static/dashboard.html")


# A simple health check endpoint
# When you visit GET /health, this function runs
@app.get("/health")
def health_check():
    """
    Health check endpoint.
    Used to verify the service is running.
    """
    return {"status": "healthy"}


@app.on_event("startup")
def on_startup():
    """
    Runs when the application starts.
    Creates all database tables and seeds default environments.
    """
    Base.metadata.create_all(bind=engine)
    seed_environments()


def seed_environments():
    """
    Create default environments if they don't exist.
    Runs on every startup but only creates missing ones.
    """
    default_envs = [
        {"key": "development", "name": "Development", "description": "Local development and testing"},
        {"key": "staging", "name": "Staging", "description": "Pre-production testing environment"},
        {"key": "production", "name": "Production", "description": "Live environment for real users"},
    ]

    db = SessionLocal()
    try:
        for env_data in default_envs:
            existing = db.query(Environment).filter(
                Environment.key == env_data["key"]
            ).first()

            if not existing:
                env = Environment(**env_data)
                db.add(env)

        db.commit()
    finally:
        db.close()
