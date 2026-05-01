from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from database import Base
from datetime import datetime
import uuid
import enum


class RunStatus(str, enum.Enum):
    running = "running"
    success = "success"
    failed = "failed"


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = {"schema": "agentcontrolroom_data"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String, nullable=False)
    intent = Column(String, nullable=True)
    prompt = Column(Text, nullable=False)
    status = Column(Enum(RunStatus), default=RunStatus.running)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


class ToolCall(Base):
    __tablename__ = "tool_calls"
    __table_args__ = {"schema": "agentcontrolroom_data"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    tool_name = Column(String, nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    status = Column(String, default="success")
    called_at = Column(DateTime, default=datetime.utcnow)


class AgentEvent(Base):
    __tablename__ = "agent_events"
    __table_args__ = {"schema": "agentcontrolroom_data"}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(String, nullable=False)
    data = Column(JSON, nullable=True)
    step_number = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)