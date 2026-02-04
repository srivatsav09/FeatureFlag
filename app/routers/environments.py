from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Environment
from app.schemas import EnvironmentCreate, EnvironmentResponse

# Create a router - groups related endpoints together
router = APIRouter(
    prefix="/environments",  # All routes start with /environments
    tags=["Environments"],   # Groups in docs UI
)


@router.post("/", response_model=EnvironmentResponse, status_code=status.HTTP_201_CREATED)
def create_environment(env_data: EnvironmentCreate, db: Session = Depends(get_db)):
    """
    Create a new environment.

    Example: POST /environments
    Body: {"key": "production", "name": "Production Environment"}
    """
    # Check if environment with this key already exists
    existing = db.query(Environment).filter(Environment.key == env_data.key).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Environment with key '{env_data.key}' already exists"
        )

    # Create new environment
    environment = Environment(
        key=env_data.key,
        name=env_data.name,
        description=env_data.description,
    )

    db.add(environment)  # Add to session
    db.commit()          # Save to database
    db.refresh(environment)  # Reload from database (gets generated id, timestamps)

    return environment


@router.get("/", response_model=list[EnvironmentResponse])
def list_environments(db: Session = Depends(get_db)):
    """
    List all environments.

    Example: GET /environments
    """
    environments = db.query(Environment).all()
    return environments


@router.get("/{env_key}", response_model=EnvironmentResponse)
def get_environment(env_key: str, db: Session = Depends(get_db)):
    """
    Get a specific environment by key.

    Example: GET /environments/production
    """
    environment = db.query(Environment).filter(Environment.key == env_key).first()

    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment '{env_key}' not found"
        )

    return environment


@router.delete("/{env_key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_environment(env_key: str, db: Session = Depends(get_db)):
    """
    Delete an environment.

    Example: DELETE /environments/development
    """
    environment = db.query(Environment).filter(Environment.key == env_key).first()

    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment '{env_key}' not found"
        )

    db.delete(environment)
    db.commit()

    return None  # 204 No Content
