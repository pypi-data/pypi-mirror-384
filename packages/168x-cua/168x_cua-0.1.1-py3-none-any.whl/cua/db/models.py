from sqlalchemy import JSON, Column, Integer, String, Text, ForeignKey, Enum, DateTime
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from pydantic import BaseModel, TypeAdapter, ValidationError

import json
from enum import Enum as PyEnum

from cua.db.database import Base
from cua_protocol.schemas import Event

class PydanticJSON(TypeDecorator):
    impl = Text  # Use Text for SQLite compatibility instead of JSONB
    cache_ok = True

    def __init__(self, model: object, **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self._adapter = TypeAdapter(model)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None

        try:
            coerced = self._adapter.validate_python(value)
        except ValidationError as e:
            model_name = getattr(self.model, "__name__", repr(self.model))
            raise ValueError(f"{model_name} validation error: {e}") from e

        # Dump to a plain python structure and serialize to JSON string for SQLite
        # Use 'json' mode so that enums and other non-JSON-serializable objects get converted to primitive values.
        python_obj = self._adapter.dump_python(coerced, mode="json")
        return json.dumps(python_obj)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # Parse JSON string from SQLite and validate with Pydantic
        python_obj = json.loads(value)
        return self._adapter.validate_python(python_obj)


# ------------------------------------------------------------
# Agent Loop
# ------------------------------------------------------------

class AgentLoopStatus(PyEnum):
    STOP = "stop"
    RUN = "run"
    RUN_ALL = "run_all"
    
class AgentLoopState(PyEnum):
    INITIALIZED = "initialized"

class DB_AgentLoop(Base):
    __tablename__ = "agent_loops"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    memory = Column(Text, nullable=True)
    
    state = Column(Enum(AgentLoopStatus, native_enum=False), nullable=False, default=AgentLoopStatus.STOP)

# ------------------------------------------------------------
# Step
# ------------------------------------------------------------

class StopReason(PyEnum):
    END_TURN = "end_turn"
    TOOL_CALLS = "tool_calls"

class ContentType(PyEnum):
    TEXT = "text"
    IMAGE = "image"

class ContentBlock(BaseModel):
    type: ContentType
    content: str

class RequestContent(BaseModel):
    content_list: list[ContentBlock]

class DB_Step(Base):
    __tablename__ = "steps"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_loop_id = Column(Integer, ForeignKey("agent_loops.id", ondelete="CASCADE"), nullable=False, index=True)
    
    sequence = Column(Integer, nullable=False)
    
    # Response
    raw_response = Column(JSON, nullable=True)  # Store raw JSON as text for SQLite
    
    stop_reason = Column(Enum(StopReason, native_enum=False), nullable=True)
    response_text = Column(Text, nullable=True)
    response_thinking_text = Column(Text, nullable=True)
    
    # Request
    request_content = Column(PydanticJSON(RequestContent), nullable=True)
    
    # Tool calls (request and response)
    tool_calls = relationship("DB_ToolCall", back_populates="step", lazy="selectin")
    
    def __str__(self) -> str:
        return f"DB_Step(id={self.id}, agent_loop_id={self.agent_loop_id}, sequence={self.sequence}, stop_reason={self.stop_reason}, response_text={self.response_text}, response_thinking_text={self.response_thinking_text}, request_content={self.request_content}, tool_calls={self.tool_calls})"
    
# ------------------------------------------------------------
# Tool Call
# ------------------------------------------------------------

class ToolCallStatus(PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
  
class DB_ToolCall(Base):
    __tablename__ = "tool_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    
    step_id = Column(Integer, ForeignKey("steps.id", ondelete="CASCADE"), nullable=False, index=True)
    step = relationship("DB_Step", back_populates="tool_calls")

    call_id = Column(String(100), nullable=False)
    name = Column(Text, nullable=False)
    input = Column(Text, nullable=False)
   
    status = Column(Enum(ToolCallStatus, native_enum=False), nullable=True, default=ToolCallStatus.PENDING)
    output_text = Column(Text, nullable=True)
    output_base64_png_list = Column(JSON, nullable=True) # list[str]
    
# ------------------------------------------------------------
# Events
# ------------------------------------------------------------

class LLMTrace(BaseModel):
    request: dict
    response: dict
    parameters: dict
    input_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    output_tokens: int
    latency: float


class EventType(PyEnum):
    OUTBOUND = "outbound"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


class DB_Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    event = Column(PydanticJSON(Event), nullable=False)