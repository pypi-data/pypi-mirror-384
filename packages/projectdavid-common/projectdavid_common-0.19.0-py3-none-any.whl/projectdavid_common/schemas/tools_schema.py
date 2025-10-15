from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ToolFunction(BaseModel):
    function: Optional[dict] = Field(default=None, description="Tool function definition")

    @field_validator("function", mode="before")
    @classmethod
    def parse_function(cls, v):
        if isinstance(v, dict) and "name" in v and "description" in v:
            return v
        elif isinstance(v, dict) and "function" in v:
            return v["function"]
        raise ValueError("Invalid function format")


class Tool(BaseModel):
    id: str
    type: str
    name: Optional[str] = Field(default=None)
    function: Optional[ToolFunction] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class ToolCreate(BaseModel):
    name: str
    type: str
    function: Optional[ToolFunction] = Field(default=None)

    @field_validator("function", mode="before")
    @classmethod
    def parse_function(cls, v):
        if isinstance(v, ToolFunction):
            return v
        if isinstance(v, dict) and "function" in v:
            return ToolFunction(function=v["function"])
        return ToolFunction(**v)


class ToolRead(Tool):
    @field_validator("function", mode="before")
    @classmethod
    def parse_function(cls, v):
        if isinstance(v, dict):
            return ToolFunction(**v)
        elif v is None:
            return None
        raise ValueError("Invalid function format")

    model_config = ConfigDict(from_attributes=True)


class ToolUpdate(BaseModel):
    type: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    function: Optional[ToolFunction] = Field(default=None)


class ToolList(BaseModel):
    tools: List[ToolRead]

    model_config = ConfigDict(from_attributes=True)
