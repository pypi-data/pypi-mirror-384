# src/projectdavid_common/schemas/actions_schema.py
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ActionBase(BaseModel):
    id: str
    run_id: str
    triggered_at: datetime
    expires_at: Optional[datetime] = None
    is_processed: bool
    processed_at: Optional[datetime] = None
    status: str = "pending"
    function_args: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class ActionStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    expired = "expired"
    cancelled = "cancelled"
    retrying = "retrying"


class ActionCreate(BaseModel):
    id: Optional[str] = None
    tool_name: Optional[str] = None
    run_id: str
    function_args: Optional[Dict[str, Any]] = {}
    expires_at: Optional[datetime] = None
    status: Optional[str] = "pending"

    @field_validator("tool_name", mode="before")
    @classmethod
    def validate_tool_fields(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            raise ValueError("Tool name must be provided.")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tool_name": "example_tool_name",
                "run_id": "example_run_id",
                "function_args": {"arg1": "value1", "arg2": "value2"},
                "expires_at": "2024-09-10T12:00:00Z",
                "status": "pending",
            }
        }
    )


class ActionRead(BaseModel):
    id: str = Field(...)
    run_id: Optional[str] = None
    tool_id: Optional[str] = None
    tool_name: Optional[str] = None
    triggered_at: Optional[str] = None
    expires_at: Optional[str] = None
    is_processed: Optional[bool] = None
    processed_at: Optional[str] = None
    status: Optional[str] = None
    function_args: Optional[dict] = None
    result: Optional[dict] = None

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "id": "action_123456",
                "run_id": "run_123456",
                "tool_id": "tool_123456",
                "tool_name": "code_interpreter",
                "triggered_at": "2025-03-24T12:00:00Z",
                "expires_at": "2025-03-24T12:05:00Z",
                "is_processed": False,
                "processed_at": "2025-03-24T12:01:00Z",
                "status": "in_progress",
                "function_args": {"param1": "value1"},
                "result": {"output": "result data"},
            }
        },
    )


class ActionList(BaseModel):
    actions: List[ActionRead]


class ActionUpdate(BaseModel):
    status: ActionStatus
    result: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
