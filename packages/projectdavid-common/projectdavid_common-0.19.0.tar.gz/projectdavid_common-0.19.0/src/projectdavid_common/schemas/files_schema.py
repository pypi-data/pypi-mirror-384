#! src/projectdavid_common/schemas/files_schema.py
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Request schema (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
class FileUploadRequest(BaseModel):
    purpose: str = Field(..., description="Purpose for uploading the file")

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# Response schemas
# ─────────────────────────────────────────────────────────────────────────────
class FileResponse(BaseModel):
    id: str = Field(..., description="Unique identifier of the file")
    object: Annotated[Literal["file"], Field(description="Always the string 'file'")] = "file"
    bytes: int = Field(..., description="Size of the file in bytes")
    created_at: Union[datetime, str] = Field(
        ...,
        description="ISO‑8601 timestamp when the file was created "
        "(datetime or ISO string accepted)",
    )
    filename: str = Field(..., description="Original filename supplied by the user")
    purpose: str = Field(..., description="Purpose associated with the file")
    status: str = Field("uploaded", description="Current status of the file")
    expires_at: Optional[Union[datetime, str]] = Field(
        None,
        description="Optional ISO‑8601 expiry timestamp",
    )

    model_config = ConfigDict(from_attributes=True)

    # --- validators --------------------------------------------------------
    @field_validator("created_at", "expires_at", mode="before")
    @classmethod
    def ensure_datetime(cls, v):
        """Allow int → datetime conversion so old code paths keep working."""
        if v is None:
            return v
        if isinstance(v, int):
            return datetime.utcfromtimestamp(v)
        return v


class FileDeleteResponse(BaseModel):
    id: str = Field(..., description="Unique identifier of the file")
    object: Annotated[Literal["file"], Field(description="Always the string 'file'")] = "file"
    deleted: bool = Field(..., description="True if the file was deleted successfully")

    model_config = ConfigDict(from_attributes=True)
