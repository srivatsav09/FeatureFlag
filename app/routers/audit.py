from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import AuditLogResponse
from app.services.audit import AuditService
from app.auth import require_any_role

router = APIRouter(
    prefix="/audit",
    tags=["Audit Logs"],
)


@router.get("/", response_model=list[AuditLogResponse])
def get_recent_logs(
    limit: int = Query(default=50, ge=1, le=200, description="Number of logs to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """
    Get the most recent audit logs.

    Returns the latest changes across all flags and environments.
    """
    audit = AuditService(db)
    logs = audit.get_recent_logs(limit=limit)
    return logs


@router.get("/flag/{flag_key}", response_model=list[AuditLogResponse])
def get_flag_history(
    flag_key: str,
    limit: int = Query(default=50, ge=1, le=200, description="Number of logs to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """
    Get the audit history for a specific flag.

    Shows all changes made to this flag across all environments.
    """
    audit = AuditService(db)
    logs = audit.get_logs_for_entity(
        entity_type="flag",
        entity_key=flag_key,
        limit=limit,
    )
    return logs
