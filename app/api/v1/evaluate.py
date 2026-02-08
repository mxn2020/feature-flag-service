"""Flag evaluation endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require_read
from app.core.database import get_db
from app.core.evaluation import evaluate_flag
from app.schemas.schemas import BulkEvalRequest, BulkEvalResponse, EvalRequest, EvalResponse

router = APIRouter(tags=["evaluate"])


@router.post("/evaluate", response_model=EvalResponse | BulkEvalResponse)
def evaluate(
    body: EvalRequest | BulkEvalRequest,
    db: Session = Depends(get_db),
    _key: str = Depends(require_read),
) -> EvalResponse | BulkEvalResponse:
    if isinstance(body, BulkEvalRequest):
        results = [evaluate_flag(req, db) for req in body.evaluations]
        return BulkEvalResponse(results=results)
    return evaluate_flag(body, db)
