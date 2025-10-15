# Assuming this file is src/projectdavid_common/schemas/user_schemas.py or similar

# --- Import the datetime CLASS ---
from datetime import datetime as dt
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# --- User Schemas (Corrected and Aligned) ---


class UserBase(BaseModel):
    """Base schema, potentially used for embedding user info minimally."""

    # Note: Removed 'name'. Depending on use case, might include id, email, or full_name.
    id: str
    email: Optional[str] = None  # Example minimal fields
    full_name: Optional[str] = None  # Example minimal fields

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Schema for creating a new user (e.g., manual or OAuth)."""

    # Aligned with the extended User model
    email: Optional[str] = Field(default=None, description="User's email address.")
    full_name: Optional[str] = Field(default=None, description="User's full display name.")
    given_name: Optional[str] = Field(default=None, description="User's first name.")
    family_name: Optional[str] = Field(default=None, description="User's last name.")
    picture_url: Optional[str] = Field(default=None, description="URL to profile picture.")
    email_verified: Optional[bool] = Field(default=False, description="Email verification status.")
    oauth_provider: Optional[str] = Field(
        default='local', description="Authentication provider (e.g., 'google', 'local')."
    )
    provider_user_id: Optional[str] = Field(
        default=None, description="User ID from the OAuth provider."
    )

    # Removed 'name' field


class UserRead(BaseModel):
    """Schema for reading user details from the API."""

    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    given_name: Optional[str] = None  # Added
    family_name: Optional[str] = None  # Added
    picture_url: Optional[str] = None  # Added
    email_verified: Optional[bool] = None  # Added
    oauth_provider: Optional[str] = None  # Added

    # --- Corrected datetime type hints ---
    created_at: dt
    updated_at: dt

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema for updating user details."""

    # Fields allowed for update - adjust as needed
    # Removed 'name' field
    email: Optional[str] = Field(
        default=None, description="New email (consider verification flow)."
    )
    full_name: Optional[str] = Field(default=None, description="New full name.")
    given_name: Optional[str] = Field(default=None, description="New first name.")
    family_name: Optional[str] = Field(default=None, description="New last name.")
    picture_url: Optional[str] = Field(default=None, description="New picture URL.")
    email_verified: Optional[bool] = Field(
        default=None, description="Update verification status (admin?)."
    )


class UserDeleteResponse(BaseModel):
    """Standard response for delete operations."""

    success: bool = Field(
        ..., description="Indicates if the deletion was successful (or accepted)."
    )
    message: Optional[str] = Field(default=None, description="Optional message providing context.")
