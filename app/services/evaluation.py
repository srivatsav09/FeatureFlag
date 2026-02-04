import hashlib

from sqlalchemy.orm import Session

from app.models import Flag, Environment
from app.models.flag import FlagType


class EvaluationService:
    """
    Service for evaluating feature flags.

    This is the core of the feature flag system - it determines
    whether a flag is enabled for a specific user.
    """

    def __init__(self, db: Session):
        self.db = db

    def evaluate(
        self,
        flag_key: str,
        environment_key: str,
        user_id: str | None = None,
    ) -> dict:
        """
        Evaluate whether a flag is enabled.

        Args:
            flag_key: The flag to evaluate (e.g., "new-checkout")
            environment_key: The environment (e.g., "production")
            user_id: The user to evaluate for (required for percentage rollouts)

        Returns:
            {
                "enabled": bool,
                "flag_key": str,
                "reason": str  # Why this decision was made
            }
        """
        # Step 1: Find the environment
        environment = self.db.query(Environment).filter(
            Environment.key == environment_key
        ).first()

        if not environment:
            return {
                "enabled": False,
                "flag_key": flag_key,
                "reason": f"Environment '{environment_key}' not found"
            }

        # Step 2: Find the flag in this environment
        flag = self.db.query(Flag).filter(
            Flag.key == flag_key,
            Flag.environment_id == environment.id
        ).first()

        if not flag:
            return {
                "enabled": False,
                "flag_key": flag_key,
                "reason": f"Flag '{flag_key}' not found in environment '{environment_key}'"
            }

        # Step 3: Is the flag enabled at all?
        if not flag.is_enabled:
            return {
                "enabled": False,
                "flag_key": flag_key,
                "reason": "Flag is disabled"
            }

        # Step 4: Check flag type
        if flag.flag_type == FlagType.BOOLEAN:
            # Boolean flag: if enabled, it's ON for everyone
            return {
                "enabled": True,
                "flag_key": flag_key,
                "reason": "Boolean flag is enabled"
            }

        elif flag.flag_type == FlagType.PERCENTAGE:
            # Percentage flag: need user_id to determine bucket
            if not user_id:
                return {
                    "enabled": False,
                    "flag_key": flag_key,
                    "reason": "Percentage flag requires user_id"
                }

            # Calculate user's bucket using hash
            bucket = self._get_bucket(flag_key, user_id)

            if bucket < flag.rollout_percentage:
                return {
                    "enabled": True,
                    "flag_key": flag_key,
                    "reason": f"User bucket {bucket} is within {flag.rollout_percentage}% rollout"
                }
            else:
                return {
                    "enabled": False,
                    "flag_key": flag_key,
                    "reason": f"User bucket {bucket} is outside {flag.rollout_percentage}% rollout"
                }

        # Unknown flag type (shouldn't happen)
        return {
            "enabled": False,
            "flag_key": flag_key,
            "reason": f"Unknown flag type: {flag.flag_type}"
        }

    def _get_bucket(self, flag_key: str, user_id: str) -> int:
        """
        Calculate a consistent bucket (0-99) for a user and flag.

        The same user + flag combination always returns the same bucket.
        This ensures users get a consistent experience.

        Args:
            flag_key: The flag key
            user_id: The user identifier

        Returns:
            Integer from 0 to 99
        """
        # Combine flag key and user ID
        combined = f"{flag_key}:{user_id}"

        # Hash it using MD5 (fast, doesn't need to be cryptographically secure)
        hash_bytes = hashlib.md5(combined.encode()).hexdigest()

        # Take first 8 hex characters and convert to integer
        hash_int = int(hash_bytes[:8], 16)

        # Modulo 100 to get a number from 0-99
        bucket = hash_int % 100

        return bucket
