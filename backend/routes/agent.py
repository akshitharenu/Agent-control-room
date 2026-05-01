from fastapi import APIRouter
from pydantic import BaseModel
from agent import run_agent

router = APIRouter(prefix="/agent", tags=["AI Agent"])

class AgentRequest(BaseModel):
    prompt: str
    intent: str = None

@router.post("/run")
def run_agent_endpoint(req: AgentRequest):
    result = run_agent(req.prompt, req.intent)
    return result