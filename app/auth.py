from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.services.auth import AuthService


# This extracts the Bearer token from the Authorization header
# Authorization: Bearer <token>
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that extracts and validates the JWT token,
    then returns the current user.

    Usage in routes:
        @router.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            return {"message": f"Hello {user.name}"}
    """
    token = credentials.credentials

    auth_service = AuthService(db)
    payload = auth_service.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    user = auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    return user


def require_role(allowed_roles: list[UserRole]):
    """
    Factory function that creates a dependency requiring specific roles.

    Usage:
        @router.post("/admin-only")
        def admin_route(user: User = Depends(require_role([UserRole.ADMIN]))):
            return {"message": "You are an admin"}

        @router.post("/dev-or-admin")
        def dev_route(user: User = Depends(require_role([UserRole.DEVELOPER, UserRole.ADMIN]))):
            return {"message": "You are a developer or admin"}
    """
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {[r.value for r in allowed_roles]}",
            )
        return user

    return role_checker


# Convenience dependencies for common role checks
require_admin = require_role([UserRole.ADMIN])
require_developer_or_admin = require_role([UserRole.DEVELOPER, UserRole.ADMIN])
require_any_role = require_role([UserRole.VIEWER, UserRole.DEVELOPER, UserRole.ADMIN])
