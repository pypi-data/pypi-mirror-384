#! python
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class MessageRole(str, Enum):
    PLATFORM = "platform"
    ASSISTANT = "assistant"
    USER = "user"
    SYSTEM = "system"
    TOOL = "tool"


class MessageCreate(BaseModel):
    content: str
    thread_id: str
    sender_id: Optional[str] = None
    assistant_id: str
    role: str  # Using string instead of Enum to allow flexible validation
    tool_id: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    is_last_chunk: bool = False

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, v):
        valid_roles = {"platform", "assistant", "user", "system", "tool"}
        if isinstance(v, str):
            v = v.lower()
            if v in valid_roles:
                return v
        raise ValueError(f"Invalid role: {v}. Must be one of {list(valid_roles)}")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Hello, this is a test message.",
                "thread_id": "example_thread_id",
                "assistant_id": "example_assistant_id",
                "meta_data": {"key": "value"},
                "role": "user",
            }
        }
    )


class ToolMessageCreate(BaseModel):
    content: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"content": "This is the content of the tool message."}}
    )


class MessageRead(BaseModel):
    id: str
    assistant_id: Optional[str]
    attachments: List[Any]
    completed_at: Optional[int]
    content: str
    created_at: int
    incomplete_at: Optional[int]
    incomplete_details: Optional[Dict[str, Any]]
    meta_data: Dict[str, Any]
    object: str
    role: str
    run_id: Optional[str]
    tool_id: Optional[str] = None
    status: Optional[str]
    thread_id: str
    sender_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MessageUpdate(BaseModel):
    content: Optional[str]
    meta_data: Optional[Dict[str, Any]]
    status: Optional[str]
    role: Optional[str]

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, v):
        if v is None:
            return v
        valid_roles = {"platform", "assistant", "user", "system", "tool"}
        v = v.lower()
        if v in valid_roles:
            return v
        raise ValueError(f"Invalid role: {v}. Must be one of {list(valid_roles)}")

    model_config = ConfigDict(from_attributes=True)


class MessagesList(BaseModel):
    object: str = "list"
    data: List[MessageRead]
    first_id: str | None = None
    last_id: str | None = None
    has_more: bool = False  # earmarked for pagination later

    # QoL helper ------------------------------------------------------
    def to_list(self):
        """Return plain list[dict] for quick consumption."""
        return [m.dict() for m in self.data]

    model_config = ConfigDict(from_attributes=True)


class MessageDeleted(BaseModel):

    id: str
    object: str = "thread.message.deleted"
    deleted: bool = True

    model_config = ConfigDict(from_attributes=True)
