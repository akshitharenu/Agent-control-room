from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import AgentRun, ToolCall, AgentEvent
import uuid

router = APIRouter(prefix="/replay", tags=["Replay Engine"])

@router.get("/{run_id}")
def replay_run(run_id: str, db: Session = Depends(get_db)):
    # Get the run
    run = db.query(AgentRun).filter(
        AgentRun.id == uuid.UUID(run_id)
    ).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Get all events ordered by step
    events = db.query(AgentEvent).filter(
        AgentEvent.run_id == uuid.UUID(run_id)
    ).order_by(AgentEvent.step_number).all()

    # Get all tool calls
    tools = db.query(ToolCall).filter(
        ToolCall.run_id == uuid.UUID(run_id)
    ).order_by(ToolCall.called_at).all()

    # Build replay timeline
    timeline = []

    # Add start event
    timeline.append({
        "step": 0,
        "type": "run_started",
        "timestamp": str(run.started_at),
        "data": {
            "agent_name": run.agent_name,
            "prompt": run.prompt
        }
    })

    # Merge events and tool calls into timeline
    for event in events:
        timeline.append({
            "step": event.step_number,
            "type": event.event_type,
            "timestamp": str(event.created_at),
            "data": event.data
        })

    for tool in tools:
        timeline.append({
            "step": None,
            "type": "tool_call",
            "timestamp": str(tool.called_at),
            "data": {
                "tool_name": tool.tool_name,
                "input": tool.input_data,
                "output": tool.output_data,
                "tokens_used": tool.tokens_used,
                "cost": tool.cost,
                "status": tool.status
            }
        })

    # Sort full timeline by timestamp
    timeline.sort(key=lambda x: x["timestamp"])

    # Add finish event if not already emitted as an AgentEvent
    has_finish_event = any(e.event_type == "run_finished" for e in events)
    if run.finished_at and not has_finish_event:
        timeline.append({
            "step": len(timeline),
            "type": "run_finished",
            "timestamp": str(run.finished_at),
            "data": {
                "status": run.status,
                "total_tokens": run.total_tokens,
                "total_cost": run.total_cost,
                "error": run.error
            }
        })

    return {
        "run_id": run_id,
        "agent_name": run.agent_name,
        "prompt": run.prompt,
        "status": run.status,
        "total_steps": len(timeline),
        "total_tokens": run.total_tokens,
        "total_cost": run.total_cost,
        "timeline": timeline
    }


@router.get("/{run_id}/step/{step_number}")
def replay_step(run_id: str, step_number: int, db: Session = Depends(get_db)):
    """Get a specific step in the replay"""
    
    events = db.query(AgentEvent).filter(
        AgentEvent.run_id == uuid.UUID(run_id),
        AgentEvent.step_number == step_number
    ).first()

    if not events:
        raise HTTPException(status_code=404, detail="Step not found")

    return {
        "run_id": run_id,
        "step": step_number,
        "event_type": events.event_type,
        "data": events.data,
        "timestamp": str(events.created_at)
    }