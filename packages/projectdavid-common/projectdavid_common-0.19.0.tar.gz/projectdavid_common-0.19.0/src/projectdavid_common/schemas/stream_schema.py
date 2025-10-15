from typing import Optional

from pydantic import BaseModel, Field, validator

from projectdavid_common.constants.ai_model_map import MODEL_MAP


class StreamRequest(BaseModel):
    provider: str
    model: str
    api_key: Optional[str]
    thread_id: str
    message_id: str
    run_id: str
    assistant_id: str
    content: Optional[str] = None

    @validator("model")
    def validate_model_key(cls, v):
        if v not in MODEL_MAP:
            raise ValueError(f"Invalid model '{v}'. Must be one of: {', '.join(MODEL_MAP.keys())}")
        return v

    @property
    def mapped_model(self) -> str:
        return MODEL_MAP[self.model]
