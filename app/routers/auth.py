from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth import AuthService
from app.auth import get_current_user, require_admin

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    New users are created with VIEWER role by default.
    Only admins can upgrade roles.
    """
    auth_service = AuthService(db)

    # Check if email already exists
    existing_user = auth_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create the user
    user = auth_service.create_user(
        email=user_data.email,
        password=user_data.password,
        name=user_data.name,
        role=UserRole.VIEWER,  # Default role
    )

    # Generate token
    token = auth_service.create_access_token(user)

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password.

    Returns a JWT token to use for authenticated requests.
    """
    auth_service = AuthService(db)

    user = auth_service.authenticate_user(
        email=credentials.email,
        password=credentials.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = auth_service.create_access_token(user)

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(user: User = Depends(get_current_user)):
    """
    Get the currently authenticated user's info.

    Requires a valid JWT token.
    """
    return user


@router.get("/users", response_model=list[UserResponse])
def list_users(
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    List all users (admin only).
    """
    users = db.query(User).all()
    return users


@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: str,
    new_role: UserRole,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Update a user's role (admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from removing their own admin role
    if user.id == current_user.id and new_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin role",
        )

    user.role = new_role
    db.commit()
    db.refresh(user)

    return user
