from typing import List, Literal, Optional, Union

from pydantic import BaseModel


class FileCitation(BaseModel):
    type: Literal["file_citation"] = "file_citation"
    index: int
    file_id: str
    filename: str
    page: Optional[int] = None  # new
    lines: Optional[List[int]] = None


class OutputText(BaseModel):
    type: Literal["output_text"] = "output_text"
    text: str
    annotations: List[FileCitation] = []


class AssistantMessage(BaseModel):
    id: str
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    content: List[OutputText]


class FileSearchCall(BaseModel):
    type: Literal["file_search_call"] = "file_search_call"
    id: str
    status: Literal["completed"] = "completed"
    queries: List[str]
    search_results: Optional[Literal[None]] = None  # keeping null like OpenAI


class FileSearchEnvelope(BaseModel):
    output: List[Union[FileSearchCall, AssistantMessage]]
