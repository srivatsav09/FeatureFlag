from datetime import datetime, timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User, UserRole


# Password hashing context
# argon2 is the modern standard for password hashing (winner of Password Hashing Competition)
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)


class AuthService:
    """
    Service for authentication operations.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================== Password Hashing ====================

    def hash_password(self, password: str) -> str:
        """
        Hash a plain text password.

        bcrypt automatically handles:
        - Salt generation (random data added to password)
        - Multiple rounds of hashing (slow = secure)
        """
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        """
        return pwd_context.verify(plain_password, hashed_password)

    # ==================== JWT Token ====================

    def create_access_token(self, user: User) -> str:
        """
        Create a JWT token for a user.

        The token contains:
        - sub (subject): user ID
        - email: user's email
        - role: user's role
        - exp (expiration): when the token expires
        """
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)

        payload = {
            "sub": user.id,           # Subject (who this token is for)
            "email": user.email,
            "role": user.role.value,  # Convert enum to string
            "exp": expire,            # Expiration time
        }

        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        return token

    def verify_token(self, token: str) -> dict | None:
        """
        Verify a JWT token and return its payload.

        Returns None if token is invalid or expired.
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            return payload
        except JWTError:
            return None

    # ==================== User Operations ====================

    def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email address."""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: str) -> User | None:
        """Get a user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(
        self,
        email: str,
        password: str,
        name: str,
        role: UserRole = UserRole.VIEWER,
    ) -> User:
        """
        Create a new user.
        """
        hashed_password = self.hash_password(password)

        user = User(
            email=email,
            hashed_password=hashed_password,
            name=name,
            role=role,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def authenticate_user(self, email: str, password: str) -> User | None:
        """
        Authenticate a user with email and password.

        Returns the user if credentials are valid, None otherwise.
        """
        user = self.get_user_by_email(email)

        if not user:
            return None

        if not user.is_active:
            return None

        if not self.verify_password(password, user.hashed_password):
            return None

        return user
