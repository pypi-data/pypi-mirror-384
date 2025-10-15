from projectdavid_common.schemas.enums import StatusEnum

"""
projectdavid_common.validation
------------------------------

Vector-store & file schemas shared by the API and SDK.

Key 0.4-series change
~~~~~~~~~~~~~~~~~~~~~
* `user_id` is **no longer supplied by the client** when you create a
  store.  The backend infers ownership from the API key.
"""

import time
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# --------------------------------------------------------------------------- #
#  VECTOR-STORE SCHEMAS
# --------------------------------------------------------------------------- #
class VectorStoreCreate(BaseModel):
    """
    Payload sent by the client to create a new vector-store.

    `user_id` REMOVED – ownership now derived from the caller’s API key.
    """

    name: str = Field(..., min_length=3, max_length=128, description="Human-friendly store name")
    vector_size: int = Field(..., gt=0, description="Dimensionality of the vectors")
    distance_metric: str = Field(..., description="Distance metric (COSINE, EUCLID, DOT)")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration options")

    # --- validators -------------------------------------------------------- #
    @field_validator("distance_metric")
    @classmethod
    def validate_distance_metric(cls, v: str) -> str:
        allowed = {"COSINE", "EUCLID", "DOT"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"Invalid distance metric: '{v}'. Must be one of {allowed}")
        return upper


class VectorStoreCreateWithSharedId(VectorStoreCreate):
    """
    Same payload as `VectorStoreCreate`, but the client pre-generates the
    shared/collection ID so Qdrant can be provisioned first.
    """

    shared_id: str = Field(
        ..., description="Pre-generated unique ID (also used as collection name)."
    )


class VectorStoreRead(BaseModel):
    """
    Metadata returned from the API for an existing vector-store.
    """

    id: str = Field(..., description="Unique identifier for the vector store")
    name: str = Field(..., description="Vector store name")
    user_id: str = Field(..., description="Owner user ID (server-side filled)")
    collection_name: str = Field(..., description="Qdrant collection name (== id)")
    vector_size: int = Field(..., description="Vector dimensionality")
    distance_metric: str = Field(..., description="Metric used for comparison")
    created_at: int = Field(..., description="Unix timestamp (sec) when created")
    updated_at: Optional[int] = Field(None, description="Last modified timestamp")
    status: StatusEnum = Field(..., description="Vector store status")
    config: Optional[Dict[str, Any]] = Field(None, description="Optional config dict")
    file_count: int = Field(..., ge=0, description="Number of files associated")
    object: str = Field("vector_store", description="Object type identifier")

    model_config = ConfigDict(from_attributes=True)


class VectorStoreUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=128, description="New store name")
    status: Optional[StatusEnum] = Field(None, description="Status override")
    config: Optional[Dict[str, Any]] = Field(None, description="New config")


# --------------------------------------------------------------------------- #
#  FILE SCHEMAS
# --------------------------------------------------------------------------- #
class VectorStoreFileCreate(BaseModel):
    file_id: str = Field(..., description="Client-assigned unique file record ID")
    file_name: str = Field(..., max_length=256, description="Original filename")
    file_path: str = Field(..., max_length=1024, description="Identifier path in metadata")
    status: Optional[StatusEnum] = Field(None, description="Initial processing state")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Arbitrary metadata")


class VectorStoreFileRead(BaseModel):
    id: str = Field(..., description="File record ID")
    vector_store_id: str = Field(..., description="Owning vector-store ID")
    file_name: str = Field(..., description="Original file name")
    file_path: str = Field(..., description="Metadata path identifier")
    processed_at: Optional[int] = Field(
        None, description="Unix timestamp of last processing change"
    )
    status: StatusEnum = Field(..., description="Current processing state")
    error_message: Optional[str] = Field(None, description="Failure reason, if any")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Metadata dict")
    object: str = Field("vector_store.file", description="Object type identifier")

    model_config = ConfigDict(from_attributes=True)


class VectorStoreFileUpdateStatus(BaseModel):
    status: StatusEnum = Field(..., description="New status for the file record")
    error_message: Optional[str] = Field(None, description="Error message if status is 'failed'")


class VectorStoreFileUpdate(BaseModel):
    status: Optional[StatusEnum] = Field(None, description="Status override")
    error_message: Optional[str] = Field(None, description="New error message")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Metadata replacement")


# --------------------------------------------------------------------------- #
#  LIST & LINK HELPERS
# --------------------------------------------------------------------------- #
class VectorStoreList(BaseModel):
    vector_stores: List[VectorStoreRead]
    object: str = Field("list", description="Object type identifier")


class VectorStoreFileList(BaseModel):
    files: List[VectorStoreFileRead]
    object: str = Field("list", description="Object type identifier")


class VectorStoreLinkAssistant(BaseModel):
    assistant_ids: List[str] = Field(..., min_length=1, description="Assistant IDs to link")


class VectorStoreUnlinkAssistant(BaseModel):
    assistant_id: str = Field(..., description="Assistant ID to unlink")


# --------------------------------------------------------------------------- #
#  SEARCH RESULT MODELS
# --------------------------------------------------------------------------- #
class VectorStoreSearchResult(BaseModel):
    text: str
    meta_data: Optional[Dict[str, Any]] = None
    score: float
    vector_id: Optional[str] = None
    store_id: Optional[str] = None
    retrieved_at: int = Field(
        default_factory=lambda: int(time.time()), description="Unix timestamp when retrieved"
    )


class SearchExplanation(BaseModel):
    base_score: float
    filters_passed: Optional[List[str]] = None
    boosts_applied: Optional[Dict[str, float]] = None
    final_score: float


class EnhancedVectorSearchResult(VectorStoreSearchResult):
    explanation: Optional[SearchExplanation] = None


# --------------------------------------------------------------------------- #
#  BULK-ADD PAYLOAD
# --------------------------------------------------------------------------- #
class VectorStoreAddRequest(BaseModel):
    texts: List[str]
    vectors: List[List[float]]
    meta_data: List[Dict[str, Any]]

    @model_validator(mode="after")
    def check_lengths_match(self) -> "VectorStoreAddRequest":
        if not (len(self.texts) == len(self.vectors) == len(self.meta_data)):
            raise ValueError(
                f"Lengths must match: texts({len(self.texts)}), "
                f"vectors({len(self.vectors)}), meta_data({len(self.meta_data)})"
            )
        return self
