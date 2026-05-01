from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import AgentRun, AgentEvent
from pydantic import BaseModel
from typing import Optional
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[3] / ".env")
from deepeval import evaluate
from deepeval.metrics import (
    AnswerRelevancyMetric,
    HallucinationMetric,
    FaithfulnessMetric
)
from deepeval.test_case import LLMTestCase

router = APIRouter(prefix="/quality", tags=["Quality Checks"])

class QualityCheckRequest(BaseModel):
    run_id: str
    input: str
    actual_output: str
    expected_output: Optional[str] = None
    context: Optional[list] = None

@router.post("/check")
def quality_check(req: QualityCheckRequest, db: Session = Depends(get_db)):
    try:
        # Build test case
        test_case = LLMTestCase(
            input=req.input,
            actual_output=req.actual_output,
            expected_output=req.expected_output,
            context=req.context or []
        )

        # Ensure OpenAI key is configured
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key is not configured. Add OPENAI_API_KEY to the environment or .env."
            )

        # Run metrics
        relevancy = AnswerRelevancyMetric(threshold=0.7)
        relevancy.measure(test_case)

        results = {
            "run_id": req.run_id,
            "input": req.input,
            "actual_output": req.actual_output,
            "scores": {
                "answer_relevancy": {
                    "score": relevancy.score,
                    "passed": relevancy.is_successful(),
                    "reason": relevancy.reason
                }
            },
            "overall_passed": relevancy.is_successful()
        }

        # Save quality score as an event
        run = db.query(AgentRun).filter(
            AgentRun.id == uuid.UUID(req.run_id)
        ).first()

        if run:
            event = AgentEvent(
                run_id=uuid.UUID(req.run_id),
                event_type="quality_check",
                data=results,
                step_number=999  # Always last step
            )
            db.add(event)
            db.commit()

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}")
def get_quality_results(run_id: str, db: Session = Depends(get_db)):
    """Get quality check results for a run"""
    events = db.query(AgentEvent).filter(
        AgentEvent.run_id == uuid.UUID(run_id),
        AgentEvent.event_type == "quality_check"
    ).all()

    if not events:
        raise HTTPException(
            status_code=404,
            detail="No quality checks found for this run"
        )

    return {
        "run_id": run_id,
        "quality_checks": [e.data for e in events]
    }