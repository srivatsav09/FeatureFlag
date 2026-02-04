from fastapi import FastAPI

from app.database import engine, Base
from app.models import Flag, Environment  # Import models so they're registered
from app.routers import environments_router, flags_router

# Create the FastAPI application instance
# This is the core object that handles all HTTP requests
app = FastAPI(
    title="Feature Flag Service",
    description="A feature flag and experimentation platform",
    version="0.1.0"
)

# Register routers
app.include_router(environments_router)
app.include_router(flags_router)


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
    Creates all database tables if they don't exist.
    """
    Base.metadata.create_all(bind=engine)
