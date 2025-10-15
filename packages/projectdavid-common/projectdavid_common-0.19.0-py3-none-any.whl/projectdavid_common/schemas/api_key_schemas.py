# src/projectdavid_common/schemas/api_key_schemas.py

# Import the datetime CLASS from the datetime module, aliased as 'dt'
from datetime import datetime as dt
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreateRequest(BaseModel):
    """
    Schema for the request body when creating a new API key.
    """

    key_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="An optional user-friendly name for the key (e.g., 'My Production Key').",
    )
    expires_in_days: Optional[int] = Field(
        default=None,
        ge=1,  # Greater than or equal to 1 day
        description="Optional number of days from now until the key automatically expires. Minimum value is 1.",
    )

    model_config = ConfigDict(
        extra='forbid',  # Don't allow extra fields in the request
        json_schema_extra={
            "examples": [
                {"key_name": "Development Key", "expires_in_days": 30},
                {"key_name": "Permanent Admin Key"},
            ]
        },
    )


class ApiKeyDetails(BaseModel):
    """
    Schema representing the public details of an API key.
    This schema does *not* include the secret key itself.
    It's designed to be created from the ApiKey ORM model.
    """

    prefix: str = Field(
        ...,  # Ellipsis means required
        description="The non-secret unique prefix of the key (e.g., 'ea_abc123'). Used for identification.",
    )
    key_name: Optional[str] = Field(
        default=None, description="The user-friendly name assigned to the key, if any."
    )
    user_id: str = Field(..., description="The ID of the user who owns this key.")

    # --- Use the datetime CLASS (aliased as dt) for type hints ---
    created_at: dt = Field(..., description="The timestamp (UTC) when the key was created.")
    expires_at: Optional[dt] = Field(
        default=None,
        description="The timestamp (UTC) when the key will expire, if an expiration was set.",
    )
    last_used_at: Optional[dt] = Field(
        default=None,
        description="The timestamp (UTC) when the key was last successfully used for authentication (if tracked).",
    )
    is_active: bool = Field(
        ..., description="Indicates if the key is currently active and usable for authentication."
    )

    # Configure Pydantic to work with ORM objects (SQLAlchemy models)
    model_config = ConfigDict(from_attributes=True)  # Pydantic v2 standard


class ApiKeyCreateResponse(BaseModel):
    """
    Schema for the response after successfully creating an API key.
    Crucially includes the plain text key which should be stored securely by the client.
    """

    plain_key: str = Field(
        ...,
        description="The generated API key. This is the ONLY time this key will be shown. Store it securely immediately.",
    )
    details: ApiKeyDetails = Field(
        ..., description="The details of the API key record that was created in the database."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "plain_key": "ea_abc123_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "details": {
                        "prefix": "ea_abc123",
                        "key_name": "My New Key",
                        "user_id": "user_jkl456",
                        # Example string representation, Pydantic handles conversion
                        "created_at": "2023-10-27T10:00:00Z",
                        "expires_at": None,
                        "last_used_at": None,
                        "is_active": True,
                    },
                }
            ]
        }
    )


class ApiKeyListResponse(BaseModel):
    """
    Schema for the response when listing API keys for a user.
    Contains a list of key details.
    """

    keys: List[ApiKeyDetails] = Field(
        ..., description="A list containing the details of the API keys associated with the user."
    )
