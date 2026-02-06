from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Flag, Environment, User
from app.schemas import FlagCreate, FlagUpdate, FlagResponse
from app.cache import CacheService
from app.auth import require_admin, require_developer_or_admin, require_any_role
from app.services.audit import AuditService

router = APIRouter(
    prefix="/flags",
    tags=["Flags"],
)


@router.post("/", response_model=FlagResponse, status_code=status.HTTP_201_CREATED)
def create_flag(
    flag_data: FlagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_developer_or_admin),  # Auth required
):
    """
    Create a new feature flag.

    Example: POST /flags
    Body: {
        "key": "new-checkout",
        "name": "New Checkout Flow",
        "environment_id": "uuid-here"
    }
    """
    # Verify environment exists
    environment = db.query(Environment).filter(
        Environment.id == flag_data.environment_id
    ).first()

    if not environment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Environment with id '{flag_data.environment_id}' not found"
        )

    # Check if flag with this key already exists in this environment
    existing = db.query(Flag).filter(
        Flag.key == flag_data.key,
        Flag.environment_id == flag_data.environment_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Flag '{flag_data.key}' already exists in this environment"
        )

    # Create the flag
    flag = Flag(
        key=flag_data.key,
        name=flag_data.name,
        description=flag_data.description,
        flag_type=flag_data.flag_type,
        is_enabled=flag_data.is_enabled,
        rollout_percentage=flag_data.rollout_percentage,
        environment_id=flag_data.environment_id,
    )

    db.add(flag)
    db.commit()
    db.refresh(flag)

    # Audit log
    audit = AuditService(db)
    audit.log_create(
        entity_type="flag",
        entity_id=flag.id,
        entity_key=flag.key,
        user=current_user,
        environment_key=environment.key,
    )

    return flag


@router.get("/", response_model=list[FlagResponse])
def list_flags(
    environment_key: str | None = Query(default=None, description="Filter by environment key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),  # Any logged-in user can read
):
    """
    List all flags, optionally filtered by environment.

    Example: GET /flags
    Example: GET /flags?environment_key=production
    """
    query = db.query(Flag)

    # Filter by environment if provided
    if environment_key:
        environment = db.query(Environment).filter(
            Environment.key == environment_key
        ).first()

        if not environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Environment '{environment_key}' not found"
            )

        query = query.filter(Flag.environment_id == environment.id)

    flags = query.all()
    return flags


@router.get("/{flag_key}", response_model=FlagResponse)
def get_flag(
    flag_key: str,
    environment_key: str = Query(..., description="Environment key (required)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),  # Any logged-in user can read
):
    """
    Get a specific flag by key and environment.

    Example: GET /flags/new-checkout?environment_key=production
    """
    # Find environment
    environment = db.query(Environment).filter(
        Environment.key == environment_key
    ).first()

    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment '{environment_key}' not found"
        )

    # Find flag
    flag = db.query(Flag).filter(
        Flag.key == flag_key,
        Flag.environment_id == environment.id
    ).first()

    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flag '{flag_key}' not found in environment '{environment_key}'"
        )

    return flag


@router.put("/{flag_key}", response_model=FlagResponse)
def update_flag(
    flag_key: str,
    flag_data: FlagUpdate,
    environment_key: str = Query(..., description="Environment key (required)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_developer_or_admin),  # Dev or admin can update
):
    """
    Update a flag's configuration.

    Example: PUT /flags/new-checkout?environment_key=production
    Body: {"is_enabled": true, "rollout_percentage": 50}
    """
    # Find environment
    environment = db.query(Environment).filter(
        Environment.key == environment_key
    ).first()

    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment '{environment_key}' not found"
        )

    # Find flag
    flag = db.query(Flag).filter(
        Flag.key == flag_key,
        Flag.environment_id == environment.id
    ).first()

    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flag '{flag_key}' not found in environment '{environment_key}'"
        )

    # Capture old values for audit log
    old_values = {
        "name": flag.name,
        "description": flag.description,
        "flag_type": flag.flag_type.value if flag.flag_type else None,
        "is_enabled": flag.is_enabled,
        "rollout_percentage": flag.rollout_percentage,
    }

    # Update only provided fields
    update_data = flag_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(flag, field, value)

    db.commit()
    db.refresh(flag)

    # Capture new values for audit log
    new_values = {
        "name": flag.name,
        "description": flag.description,
        "flag_type": flag.flag_type.value if flag.flag_type else None,
        "is_enabled": flag.is_enabled,
        "rollout_percentage": flag.rollout_percentage,
    }

    # Audit log
    audit = AuditService(db)
    audit.log_update(
        entity_type="flag",
        entity_id=flag.id,
        entity_key=flag.key,
        user=current_user,
        old_values=old_values,
        new_values=new_values,
        environment_key=environment_key,
    )

    # Invalidate cache so next evaluation gets fresh data
    cache = CacheService()
    cache.invalidate_flag(flag_key, environment_key)

    return flag


@router.delete("/{flag_key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flag(
    flag_key: str,
    environment_key: str = Query(..., description="Environment key (required)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # Only admin can delete
):
    """
    Delete a flag.

    Example: DELETE /flags/new-checkout?environment_key=development
    """
    # Find environment
    environment = db.query(Environment).filter(
        Environment.key == environment_key
    ).first()

    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment '{environment_key}' not found"
        )

    # Find flag
    flag = db.query(Flag).filter(
        Flag.key == flag_key,
        Flag.environment_id == environment.id
    ).first()

    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flag '{flag_key}' not found in environment '{environment_key}'"
        )

    # Store flag info for audit before deleting
    flag_id = flag.id

    db.delete(flag)
    db.commit()

    # Audit log (after delete succeeds)
    audit = AuditService(db)
    audit.log_delete(
        entity_type="flag",
        entity_id=flag_id,
        entity_key=flag_key,
        user=current_user,
        environment_key=environment_key,
    )

    # Invalidate cache
    cache = CacheService()
    cache.invalidate_flag(flag_key, environment_key)

    return None
