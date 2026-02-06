import json
from sqlalchemy.orm import Session

from app.models import AuditLog, AuditAction, User


class AuditService:
    """
    Service for creating and querying audit logs.
    """

    def __init__(self, db: Session):
        self.db = db

    def log_create(
        self,
        entity_type: str,
        entity_id: str,
        entity_key: str,
        user: User,
        environment_key: str | None = None,
    ) -> AuditLog:
        """Log a create action."""
        return self._create_log(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_key=entity_key,
            action=AuditAction.CREATED,
            user=user,
            changes=None,
            environment_key=environment_key,
        )

    def log_update(
        self,
        entity_type: str,
        entity_id: str,
        entity_key: str,
        user: User,
        old_values: dict,
        new_values: dict,
        environment_key: str | None = None,
    ) -> AuditLog:
        """
        Log an update action with what changed.

        Args:
            old_values: Dict of field names to old values
            new_values: Dict of field names to new values
        """
        # Calculate what actually changed
        changes = {}
        for field, new_value in new_values.items():
            old_value = old_values.get(field)
            if old_value != new_value:
                changes[field] = {
                    "old": old_value,
                    "new": new_value,
                }

        return self._create_log(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_key=entity_key,
            action=AuditAction.UPDATED,
            user=user,
            changes=json.dumps(changes) if changes else None,
            environment_key=environment_key,
        )

    def log_delete(
        self,
        entity_type: str,
        entity_id: str,
        entity_key: str,
        user: User,
        environment_key: str | None = None,
    ) -> AuditLog:
        """Log a delete action."""
        return self._create_log(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_key=entity_key,
            action=AuditAction.DELETED,
            user=user,
            changes=None,
            environment_key=environment_key,
        )

    def _create_log(
        self,
        entity_type: str,
        entity_id: str,
        entity_key: str,
        action: AuditAction,
        user: User,
        changes: str | None,
        environment_key: str | None,
    ) -> AuditLog:
        """Internal method to create an audit log entry."""
        log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_key=entity_key,
            action=action,
            user_id=user.id,
            changes=changes,
            environment_key=environment_key,
        )

        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        return log

    def get_logs_for_entity(
        self,
        entity_type: str,
        entity_key: str,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Get audit logs for a specific entity."""
        return (
            self.db.query(AuditLog)
            .filter(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_key == entity_key,
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_recent_logs(self, limit: int = 100) -> list[AuditLog]:
        """Get the most recent audit logs."""
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
