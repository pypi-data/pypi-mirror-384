from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProcessOutput(BaseModel):
    store_name: str
    status: str
    chunks_processed: int

    model_config = ConfigDict(from_attributes=True)
