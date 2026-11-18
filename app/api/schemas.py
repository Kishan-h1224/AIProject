
from pydantic import BaseModel, Field
from typing import Any, Optional, Literal


class AgentRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    conversation_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )


class AgentResponse(BaseModel):
    success: bool
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    conversation_id: Optional[str] = None
    pending_approval: Optional[dict[str, Any]] = None


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    role: Literal["admin", "developer", "analyst", "guest"]


class ApprovalDecisionRequest(BaseModel):
    approved: bool
