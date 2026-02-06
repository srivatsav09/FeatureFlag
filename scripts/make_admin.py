"""
Script to promote a user to admin role.
Run from project root: python -m scripts.make_admin <email>
"""
import sys
sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models import User, UserRole


def make_admin(email: str):
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            print(f"User with email '{email}' not found.")
            return

        if user.role == UserRole.ADMIN:
            print(f"User '{email}' is already an admin.")
            return

        old_role = user.role.value
        user.role = UserRole.ADMIN
        db.commit()

        print(f"Success! User '{email}' promoted from {old_role} to admin.")

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.make_admin <email>")
        print("Example: python -m scripts.make_admin admin@test.com")
        sys.exit(1)

    email = sys.argv[1]
    make_admin(email)
