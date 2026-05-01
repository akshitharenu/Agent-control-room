from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import AgentRun, ToolCall, AgentEvent, RunStatus
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any
import uuid
from celery_app import celery as celery_app
from tasks import log_tool_call_task, log_event_task, finish_run_task
router = APIRouter(prefix="/runs", tags=["Agent Runs"])

# --- Schemas ---
class StartRunRequest(BaseModel):
    agent_name: str
    intent: Optional[str] = None
    prompt: str

class LogToolCallRequest(BaseModel):
    run_id: str
    tool_name: str
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    tokens_used: int = 0
    cost: float = 0.0
    status: str = "success"

class LogEventRequest(BaseModel):
    run_id: str
    event_type: str
    data: Optional[Any] = None
    step_number: int = 0

class FinishRunRequest(BaseModel):
    run_id: str
    status: RunStatus
    total_tokens: int = 0
    total_cost: float = 0.0
    error: Optional[str] = None

# --- Endpoints ---

@router.post("/start")
def start_run(req: StartRunRequest, db: Session = Depends(get_db)):
    try:
        run = AgentRun(agent_name=req.agent_name, intent=req.intent, prompt=req.prompt)
        db.add(run)
        db.commit()
        db.refresh(run)
        return {"run_id": str(run.id), "message": "Run started ✅"}
    except Exception as e:
        db.rollback()
        print(f"Error in start_run: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start run: {str(e)}")

@router.post("/log-tool")
def log_tool_call(req: LogToolCallRequest, db: Session = Depends(get_db)):
    """Log tool calls to DB synchronously"""
    try:
        from models import ToolCall
        import uuid
        tool = ToolCall(
            run_id=uuid.UUID(req.run_id),
            tool_name=req.tool_name,
            input_data=req.input_data,
            output_data=req.output_data,
            tokens_used=req.tokens_used,
            cost=req.cost,
            status=req.status
        )
        db.add(tool)
        db.commit()
        return {"status": "logged", "tool": req.tool_name}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/log-event")
def log_event(req: LogEventRequest, db: Session = Depends(get_db)):
    """Log events to DB synchronously"""
    try:
        from models import AgentEvent
        import uuid
        event = AgentEvent(
            run_id=uuid.UUID(req.run_id),
            event_type=req.event_type,
            data=req.data,
            step_number=req.step_number
        )
        db.add(event)
        db.commit()
        return {"status": "logged", "event": req.event_type}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/finish")
def finish_run(req: FinishRunRequest, db: Session = Depends(get_db)):
    """Finish a run synchronously"""
    try:
        from models import AgentRun, AgentEvent
        import uuid
        from datetime import datetime
        run = db.query(AgentRun).filter(AgentRun.id == uuid.UUID(req.run_id)).first()
        if run:
            run.status = req.status
            run.total_tokens = req.total_tokens
            run.total_cost = req.total_cost
            run.error = req.error
            run.finished_at = datetime.utcnow()
            
            # Also log a final event
            event = AgentEvent(
                run_id=uuid.UUID(req.run_id),
                event_type="run_finished",
                data={
                    "status": req.status,
                    "total_tokens": req.total_tokens,
                    "total_cost": req.total_cost,
                    "error": req.error,
                },
                step_number=9999
            )
            db.add(event)
            db.commit()
        return {"status": "finished", "run_id": req.run_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def get_all_runs(db: Session = Depends(get_db)):
    runs = db.query(AgentRun).order_by(AgentRun.started_at.desc()).all()
    return runs

@router.get("/{run_id}")
def get_run_detail(run_id: str, db: Session = Depends(get_db)):
    run = db.query(AgentRun).filter(AgentRun.id == uuid.UUID(run_id)).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    tools = db.query(ToolCall).filter(ToolCall.run_id == uuid.UUID(run_id)).all()
    events = db.query(AgentEvent).filter(AgentEvent.run_id == uuid.UUID(run_id)).order_by(AgentEvent.step_number).all()
    return {"run": run, "tool_calls": tools, "events": events}

@router.delete("/{run_id}")
def delete_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(AgentRun).filter(AgentRun.id == uuid.UUID(run_id)).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Delete related records first
    db.query(ToolCall).filter(ToolCall.run_id == uuid.UUID(run_id)).delete()
    db.query(AgentEvent).filter(AgentEvent.run_id == uuid.UUID(run_id)).delete()
    db.delete(run)
    db.commit()
    return {"message": "Run deleted successfully"}

@router.get("/task/{task_id}")
def get_task_status(task_id: str):
    """Check if a background task completed"""
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result
    }