from celery_app import celery
from database import SessionLocal
from models import AgentRun, ToolCall, AgentEvent, RunStatus
from datetime import datetime
import uuid

@celery.task
def log_tool_call_task(run_id, tool_name, input_data, output_data, tokens_used, cost, status):
    """Async task to log tool calls to DB"""
    db = SessionLocal()
    try:
        tool = ToolCall(
            run_id=uuid.UUID(run_id),
            tool_name=tool_name,
            input_data=input_data,
            output_data=output_data,
            tokens_used=tokens_used,
            cost=cost,
            status=status
        )
        db.add(tool)
        db.commit()
        return {"status": "logged", "tool": tool_name}
    except Exception as e:
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery.task
def log_event_task(run_id, event_type, data, step_number):
    """Async task to log events to DB"""
    db = SessionLocal()
    try:
        event = AgentEvent(
            run_id=uuid.UUID(run_id),
            event_type=event_type,
            data=data,
            step_number=step_number
        )
        db.add(event)
        db.commit()
        return {"status": "logged", "event": event_type}
    except Exception as e:
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery.task
def finish_run_task(run_id, status, total_tokens, total_cost, error=None):
    """Async task to finish a run"""
    db = SessionLocal()
    try:
        run = db.query(AgentRun).filter(
            AgentRun.id == uuid.UUID(run_id)
        ).first()
        if run:
            run.status = status
            run.total_tokens = total_tokens
            run.total_cost = total_cost
            run.error = error
            run.finished_at = datetime.utcnow()
            db.commit()

            # Log a final replay event for the finished run
            event = AgentEvent(
                run_id=uuid.UUID(run_id),
                event_type="run_finished",
                data={
                    "status": status,
                    "total_tokens": total_tokens,
                    "total_cost": total_cost,
                    "error": error,
                },
                step_number=9999
            )
            db.add(event)
            db.commit()
        return {"status": "finished", "run_id": run_id}
    except Exception as e:
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()