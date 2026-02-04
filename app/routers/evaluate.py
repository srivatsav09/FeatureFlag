from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import EvaluationService

router = APIRouter(
    prefix="/evaluate",
    tags=["Evaluation"],
)


@router.get("/{flag_key}")
def evaluate_flag(
    flag_key: str,
    environment_key: str = Query(..., description="Environment to evaluate in"),
    user_id: str | None = Query(default=None, description="User ID (required for percentage rollouts)"),
    db: Session = Depends(get_db),
):
    """
    Evaluate whether a feature flag is enabled.

    This is the primary endpoint that applications call to check
    if a feature should be enabled for a user.

    Examples:
        GET /evaluate/new-checkout?environment_key=production
        GET /evaluate/new-checkout?environment_key=production&user_id=alice
    """
    service = EvaluationService(db)
    result = service.evaluate(
        flag_key=flag_key,
        environment_key=environment_key,
        user_id=user_id,
    )
    return result
